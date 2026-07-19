#!/usr/bin/env python3
"""
小神农中医AI - 古籍条文批量导入脚本
将 data/raw/classical_texts*.json 导入 Chroma (chroma_db_v2)

数据格式: [{"text_id": "CT-00001", "book": "...", "section": "...",
           "text": "...", "symptom": "...", "keywords": [...]}, ...]

特性:
- 按 text_id 幂等去重, 中断后可安全重跑
- 进度记录到 logs/classical_import_progress.json
- --max-files N 限制导入文件数, 便于小批次验证

用法:
    python scripts/import_classical_texts.py --max-files 5
    python scripts/import_classical_texts.py            # 全部导入

注意: 导入前请停止后端服务, 避免 Chroma SQLite 并发写冲突。
"""

import os
import sys
import json
import time
import hashlib
import argparse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
DB_PATH = os.path.join(BASE_DIR, "data", "chroma_db_v2")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
PROGRESS_FILE = os.path.join(LOGS_DIR, "classical_import_progress.json")

sys.path.insert(0, BACKEND_DIR)
sys.dont_write_bytecode = True

# 离线环境变量, 避免 sentence-transformers 联网检查
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"completed_files": [], "total_imported": 0}


def save_progress(progress):
    os.makedirs(LOGS_DIR, exist_ok=True)
    tmp = PROGRESS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)
    os.replace(tmp, PROGRESS_FILE)


def convert_file(filepath):
    """把一个 classical_texts 批次文件转成 rag add_documents 格式"""
    with open(filepath, "r", encoding="utf-8") as f:
        entries = json.load(f)

    docs = []
    for entry in entries:
        text = (entry.get("text") or "").strip()
        if not text:
            continue
        text_id = entry.get("text_id") or f"ct_{hashlib.md5(text.encode()).hexdigest()[:12]}"
        keywords = entry.get("keywords") or []
        docs.append({
            "text": text,
            "metadata": {
                "chunk_id": text_id,
                "source_book": entry.get("book", "未知"),
                "source_section": entry.get("section", "未知"),
                "symptom": entry.get("symptom", ""),
                "keywords": "、".join(keywords) if isinstance(keywords, list) else str(keywords),
                "data_source": "classical_texts_import",
            },
        })
    return docs


def filter_existing(rag, docs):
    """跳过已存在于知识库的 id, 返回新文档"""
    ids = [d["metadata"]["chunk_id"] for d in docs]
    collection = rag._get_collection()
    existing = set()
    # 分批查询, 避免一次性传入过多 id
    for i in range(0, len(ids), 500):
        batch = ids[i:i + 500]
        try:
            res = collection.get(ids=batch, include=[])
            existing.update(res.get("ids", []))
        except Exception:
            pass
    return [d for d in docs if d["metadata"]["chunk_id"] not in existing]


def main():
    parser = argparse.ArgumentParser(description="导入古籍条文到 Chroma 知识库")
    parser.add_argument("--max-files", type=int, default=0, help="最多导入多少个文件 (0=全部)")
    parser.add_argument("--pattern", default="classical_texts*.json", help="文件名 glob")
    args = parser.parse_args()

    import glob as globmod
    files = sorted(globmod.glob(os.path.join(RAW_DIR, args.pattern)))
    if not files:
        print(f"[导入] 未找到匹配文件: {args.pattern}")
        return

    progress = load_progress()
    done = set(progress["completed_files"])
    todo = [f for f in files if os.path.basename(f) not in done]
    if args.max_files > 0:
        todo = todo[:args.max_files]

    print(f"[导入] 匹配文件 {len(files)} 个, 已完成 {len(done)}, 本次待导入 {len(todo)}")
    if not todo:
        print("[导入] 没有需要导入的文件")
        return

    from rag_engine_v2 import XiaoShennongRAGv2
    rag = XiaoShennongRAGv2(db_path=DB_PATH)
    collection = rag._get_collection()
    print(f"[导入] 导入前知识库文档数: {collection.count()}")

    imported_total = 0
    t0 = time.time()
    for idx, filepath in enumerate(todo, 1):
        name = os.path.basename(filepath)
        ft = time.time()
        try:
            docs = convert_file(filepath)
            new_docs = filter_existing(rag, docs)
            if new_docs:
                rag.add_documents(new_docs)
            imported_total += len(new_docs)
            progress["completed_files"].append(name)
            progress["total_imported"] = progress.get("total_imported", 0) + len(new_docs)
            save_progress(progress)
            print(f"[导入] ({idx}/{len(todo)}) {name}: 新增 {len(new_docs)}/{len(docs)} 条, "
                  f"耗时 {time.time() - ft:.1f}s, 累计 {imported_total}")
        except Exception as e:
            print(f"[导入] ({idx}/{len(todo)}) {name} 失败: {e}")

    print(f"[导入] 完成: 本次新增 {imported_total} 条, 总耗时 {time.time() - t0:.1f}s")
    print(f"[导入] 导入后知识库文档数: {collection.count()}")


if __name__ == "__main__":
    main()
