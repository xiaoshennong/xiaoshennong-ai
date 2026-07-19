#!/usr/bin/env python3
"""
小神农中医AI - 无嵌入词法检索器（语义搜索主路）

设计背景：英文嵌入模型对中文古文产生退化向量，导致向量检索静默失效。
本模块用确定性词法检索替代：
  查询 → 症状别名/药物/方剂/证型词典命中 + jieba 分词
      → SQLite 元数据/全文候选
      → Python 加权打分（元数据命中 > 关键词命中 > 正文命中）
      → top_k
零命中时用 yunwu LLM 把口语改写为标准术语重试一次（结果缓存）。

优势：零 token 主路、结果可解释、毫秒级、不会静默失效。
"""

import os
import re
import sys
import json
import time
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import get_conn, init_db, now_iso

BASE_DIR_ENV = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ============ 词典构建（懒加载） ============

_term_dict: Optional[Dict[str, str]] = None  # term -> type ('symptom'/'drug'/'formula'/'syndrome')
_symptom_standard: Dict[str, str] = {}       # alias/name -> 标准症状名

STOPWORDS = {
    "的", "了", "呢", "吗", "啊", "呀", "吧", "是", "有", "没有", "什么", "怎么",
    "怎么办", "为什么", "如何", "请问", "一下", "可以", "应该", "感觉", "有点",
    "最近", "总是", "一直", "经常", "我", "你", "他", "她", "我们", "这个", "那个",
    "还是", "就是", "好像", "似的", "以及", "而且", "或者", "因为", "所以", "如果",
}


def _build_dict() -> Dict[str, str]:
    global _term_dict, _symptom_standard
    if _term_dict is not None:
        return _term_dict

    d: Dict[str, str] = {}

    from symptom_codes import SYMPTOM_MAP
    for sid, info in SYMPTOM_MAP.items():
        name = info.get("name", "")
        if name:
            d[name] = "symptom"
            _symptom_standard[name] = name
        for alias in info.get("aliases", []):
            if alias and len(alias) >= 2:
                d.setdefault(alias, "symptom")
                _symptom_standard[alias] = name

    from drug_formula_db import DRUG_DATABASE, FORMULA_DATABASE
    for info in DRUG_DATABASE.values():
        name = info.get("name", "")
        if name:
            d[name] = "drug"
    for info in FORMULA_DATABASE.values():
        name = info.get("name", "")
        if name:
            d[name] = "formula"

    try:
        from syndrome_db import SYNDROME_DATABASE
        for info in SYNDROME_DATABASE.values():
            name = info.get("name", "") if isinstance(info, dict) else ""
            if name:
                d[name] = "syndrome"
    except Exception:
        pass

    _term_dict = d
    return d


# ============ 结果结构（与 RetrievedChunk 属性对齐） ============

@dataclass
class LexicalChunk:
    text: str
    source_book: str
    source_section: str
    original_text: str
    score: float
    metadata: Dict = None


# ============ 查询解析 ============

def extract_terms(query: str) -> List[Tuple[str, str]]:
    """
    从查询中抽取检索词，返回 [(term, type)]，按优先级排序去重。
    type: symptom/drug/formula/syndrome/token
    """
    d = _build_dict()
    found: Dict[str, str] = {}

    # 1) 词典扫描：任何 ≥2 字的词典词出现在查询中即命中（先长后短，避免“气喘”被“气”吃掉）
    for term in sorted(d.keys(), key=len, reverse=True):
        if len(term) >= 2 and term in query:
            found.setdefault(term, d[term])
        if len(found) >= 12:
            break

    # 2) jieba 分词兜底（去掉已被词典覆盖的子串）
    try:
        import jieba
        tokens = jieba.lcut(query)
    except Exception:
        tokens = re.split(r"[^\u4e00-\u9fffA-Za-z0-9]+", query)

    covered = query
    for t in found:
        covered = covered.replace(t, " ")
    for tok in tokens:
        tok = tok.strip()
        if (len(tok) >= 2 and tok not in STOPWORDS and not tok.isdigit()
                and tok in covered and tok not in found):
            found[tok] = "token"

    # 排序：词典词优先于裸 token，同类型长的优先
    order = {"symptom": 0, "formula": 1, "drug": 2, "syndrome": 3, "token": 4}
    terms = sorted(found.items(), key=lambda kv: (order.get(kv[1], 5), -len(kv[0])))

    # 口语别名扩展出标准症状名（如“胃不舒服”→“胃脘痛”），否则古文候选取不到
    expanded = list(terms)
    for term, ttype in terms:
        if ttype == "symptom":
            std = _symptom_standard.get(term)
            if std and std != term and std not in found:
                expanded.append((std, "symptom"))
    return expanded[:12]


# ============ 候选检索与打分 ============

def _fetch_candidates(terms: List[Tuple[str, str]], per_term_limit: int = 300) -> Dict[str, Dict]:
    """按词取候选行，返回 text_id -> row dict"""
    if not terms:
        return {}
    conn = get_conn()
    candidates: Dict[str, Dict] = {}
    try:
        for term, _type in terms:
            like = f"%{term}%"
            rows = conn.execute(
                """
                SELECT text_id, book, section, text, symptom, keywords FROM classical_texts
                WHERE symptom = ? OR keywords LIKE ? OR text LIKE ? OR book LIKE ? OR section LIKE ?
                LIMIT ?
                """,
                (term, like, like, like, like, per_term_limit),
            ).fetchall()
            for r in rows:
                candidates.setdefault(r["text_id"], dict(r))
    finally:
        conn.close()
    return candidates


def _score_row(row: Dict, terms: List[Tuple[str, str]]) -> float:
    text = row.get("text") or ""
    keywords = row.get("keywords") or ""
    symptom = row.get("symptom") or ""
    book_sec = (row.get("book") or "") + (row.get("section") or "")

    score = 0.0
    hits = 0
    for term, ttype in terms:
        hit = False
        if symptom and term == symptom:
            score += 2.0
            hit = True
        elif ttype == "symptom":
            std = _symptom_standard.get(term)
            if std and symptom and std == symptom:
                score += 2.0
                hit = True
        if keywords and term in keywords:
            score += 1.5
            hit = True
        if term in text:
            score += 1.0
            hit = True
        if term in book_sec:
            score += 0.5
            hit = True
        if hit:
            hits += 1
    if hits >= 3:
        score += 2.0  # 多词覆盖奖励
    return score


# ============ LLM 改写兜底 ============

def _llm_rewrite(query: str) -> str:
    """零命中时，把口语查询改写为标准中医术语（缓存到 query_cache）"""
    # 独立运行时 .env 可能未加载（api_server 启动时会加载），这里兜底加载一次
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(BASE_DIR_ENV, ".env"), override=False)
    except Exception:
        pass
    conn = get_conn()
    try:
        row = conn.execute("SELECT rewritten FROM query_cache WHERE query = ?", (query,)).fetchone()
        if row:
            return row["rewritten"]

        rewritten = ""
        try:
            from llm_client_yunwu import get_llm_client
            client = get_llm_client()
            messages = [
                {"role": "system", "content": "你是中医术语标准化助手。把用户的口语描述改写为 3-6 个标准中医症状名或证型名（如：眩晕、头痛、肝阳上亢、痰湿内阻）。只输出术语，用中文逗号分隔，不要解释，不要输出药名和方剂名。"},
                {"role": "user", "content": query},
            ]
            if hasattr(client, "chat"):
                resp = client.chat(messages)
                rewritten = resp if isinstance(resp, str) else str(resp)
            else:
                rewritten = client.generate(messages[-1]["content"])
        except Exception as e:
            print(f"[LexicalRetriever] LLM 改写失败: {e}")
            return ""

        return rewritten.strip().replace("，", ",")
    finally:
        conn.close()


def _cache_rewrite(query: str, rewritten: str) -> None:
    """仅当改写真正带来检索结果时才缓存（无效改写不沉淀）"""
    conn = get_conn()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO query_cache (query, rewritten, created_at) VALUES (?,?,?)",
            (query, rewritten, now_iso()),
        )
        conn.commit()
    finally:
        conn.close()


# ============ 主入口 ============

def retrieve(query: str, top_k: int = 5) -> List[LexicalChunk]:
    """词法检索主入口，返回与 RAG retrieve 兼容的结果列表"""
    init_db()
    query = (query or "").strip()
    if not query:
        return []

    terms = extract_terms(query)
    candidates = _fetch_candidates(terms)

    if not candidates:
        rewritten = _llm_rewrite(query)
        if rewritten:
            terms = extract_terms(query + " " + rewritten.replace(",", " "))
            candidates = _fetch_candidates(terms)
            if candidates:
                _cache_rewrite(query, rewritten)

    if not candidates:
        return []

    scored = [(row, _score_row(row, terms)) for row in candidates.values()]
    scored = [(row, s) for row, s in scored if s > 0]
    scored.sort(key=lambda x: (-x[1], x[0]["text_id"]))  # 分数优先，id 次序兜底保证稳定分页

    top = scored[:top_k]
    if not top:
        return []
    max_score = top[0][1]

    results = []
    for row, s in top:
        results.append(LexicalChunk(
            text=row["text"],
            source_book=row.get("book") or "",
            source_section=row.get("section") or "",
            original_text=row["text"],
            score=round(s / max_score, 4) if max_score else 0.0,
            metadata={"symptom": row.get("symptom") or "", "keywords": row.get("keywords") or ""},
        ))
    return results


if __name__ == "__main__":
    # 简单自测
    for q in ["咳嗽", "麻黄汤", "胃不舒服", "腰痛", "失眠多梦怎么办"]:
        rs = retrieve(q, top_k=3)
        print(f"\n查询: {q}")
        for r in rs:
            print(f"  [{r.score}] 《{r.source_book}》{r.source_section} | {r.text[:40]}")
