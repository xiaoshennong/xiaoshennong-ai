#!/usr/bin/env python3
"""
小神农中医AI - RAG核心引擎 v2.0
双源验证批判性思维架构
"""

import os
import json
import re
import hashlib
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

import chromadb
from chromadb.config import Settings
import numpy as np

# 导入症状编号体系和药物方剂数据库
from symptom_codes import find_symptoms_by_text, SYMPTOM_MAP, BODY_PARTS, CATEGORY_CODES
from drug_formula_db import (
    find_formulas_by_symptoms, find_drugs_by_symptoms, 
    get_formula_by_id, get_drug_by_id, get_drug_contraindications,
    DRUG_DATABASE, FORMULA_DATABASE
)

# 导入证型数据库和禁忌规则库
from syndrome_db import find_syndromes_by_symptoms, get_syndrome_by_id
from contraindication_db import check_all_contraindications
from code_system import validate_symptom_id, validate_drug_id, validate_syndrome_id, get_id_description

# 导入批判性思维验证引擎
from critical_thinking_engine import (
    CriticalThinkingEngine,
    SymptomCooccurrenceAnalyzer,
    TimeWindowAdverseDetector,
    SimilarPatientMatcher,
    AdverseEventDetector,
)

# 导入联网搜索 Agent
try:
    from web_search_agent import WebSearchAgent
    HAS_WEB_SEARCH = True
except ImportError:
    HAS_WEB_SEARCH = False
    WebSearchAgent = None

# 尝试使用sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    USE_ST = True
except ImportError:
    USE_ST = False


@dataclass
class RetrievedChunk:
    """检索到的知识片段"""
    text: str
    source_book: str
    source_section: str
    original_text: str
    score: float
    chunk_id: str


@dataclass
class ThinkingStep:
    """思考步骤"""
    step_name: str
    step_description: str
    start_time: float
    end_time: float = 0
    details: Dict = field(default_factory=dict)
    status: str = "running"


@dataclass
class DiagnosisResult:
    """AI辨证结果（含思考过程）"""
    constitution: str
    syndrome: str
    advice: str
    sources: List[Dict]
    warning: str
    thinking_process: List[Dict]
    total_time_ms: float
    # v2.0兼容字段
    symptom_analysis: Dict = field(default_factory=dict)
    matched_formulas: List[Dict] = field(default_factory=list)
    matched_drugs: List[Dict] = field(default_factory=list)
    contraindications: List[Dict] = field(default_factory=list)
    classic_sources: List[Dict] = field(default_factory=list)
    # v2.1新增字段
    syndrome_analysis: List[Dict] = field(default_factory=list)
    drug_relations: List[Dict] = field(default_factory=list)
    syndrome_matched: bool = False
    syndrome_match_score: float = 0.0
    # v2.2新增字段（批判性思维+副作用检测）
    credibility_assessment: List[Dict] = field(default_factory=list)
    cooccurrence_analysis: Dict = field(default_factory=dict)
    adverse_detection: Dict = field(default_factory=dict)
    similar_patients: List[Dict] = field(default_factory=list)
    knowledge_gap_report: List[Dict] = field(default_factory=list)
    import_suggestions: List[Dict] = field(default_factory=list)


class SimpleEmbedder:
    """简化版嵌入器"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self._init_model()
    
    def _init_model(self):
        if USE_ST:
            try:
                print(f"[Embedder] 加载模型: {self.model_name}")
                self.model = SentenceTransformer(self.model_name)
                print(f"[Embedder] 模型加载完成")
            except Exception as e:
                print(f"[Embedder] 模型加载失败: {e}，使用备用方案")
                self.model = None
        else:
            print("[Embedder] sentence-transformers未安装，使用备用方案")
            self.model = None
    
    def encode(self, texts: List[str]) -> List[List[float]]:
        if isinstance(texts, str):
            texts = [texts]
        
        if self.model is not None:
            embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            return embeddings.tolist()
        else:
            return self._simple_encode(texts)
    
    def _simple_encode(self, texts: List[str]) -> List[List[float]]:
        keywords = {
            "头痛": 0, "发热": 1, "恶寒": 2, "汗出": 3, "咳嗽": 4,
            "胸闷": 5, "心悸": 6, "失眠": 7, "多梦": 8, "食欲不振": 9,
            "腹胀": 10, "腹泻": 11, "便秘": 12, "口干": 13, "口苦": 14,
            "咽痛": 15, "腰痛": 16, "关节痛": 17, "乏力": 18,
            "风寒": 19, "风热": 20, "湿热": 21, "气虚": 22, "血虚": 23,
            "阴虚": 24, "阳虚": 25, "痰湿": 26, "血瘀": 27, "气郁": 28,
            "麻黄": 29, "桂枝": 30, "柴胡": 31, "黄芩": 32, "人参": 33,
            "黄芪": 34, "当归": 35, "甘草": 36, "杏仁": 37, "芍药": 38,
            "无汗": 39, "恶风": 40, "体痛": 41, "喘": 42, "脉浮": 43,
            "脉紧": 44, "脉数": 45, "脉沉": 46, "脉细": 47, "脉弦": 48,
            "呕吐": 49, "心烦": 50, "口渴": 51, "小便不利": 52, "下利": 53,
        }
        
        dim = 128
        embeddings = []
        
        for text in texts:
            vec = np.zeros(dim)
            for kw, idx in keywords.items():
                if kw in text:
                    vec[idx % dim] += 1.0
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            embeddings.append(vec.tolist())
        
        return embeddings


class XiaoShennongRAGv2:
    """
    小神农RAG引擎 v2.2
    双源验证 + 批判性思维 + 副作用检测架构
    """
    
    def __init__(self, 
                 db_path: str = "./data/chroma_db",
                 model_name: str = "all-MiniLM-L6-v2",
                 device: str = None):
        
        self.device = device or "cpu"
        print(f"[RAG v2.2] 使用设备: {self.device}")
        
        self.embedder = SimpleEmbedder(model_name)
        
        print(f"[RAG v2.2] 初始化向量数据库: {db_path}")
        os.makedirs(db_path, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 初始化批判性思维引擎
        print("[RAG v2.2] 初始化批判性思维验证引擎...")
        self.credibility_engine = CriticalThinkingEngine()
        self.cooccurrence_analyzer = SymptomCooccurrenceAnalyzer()
        self.adverse_detector = AdverseEventDetector()
        self.similar_patient_matcher = SimilarPatientMatcher()

        # 初始化联网搜索 Agent（使用 Yunwu AI）
        if HAS_WEB_SEARCH:
            print("[RAG v2.2] 初始化联网搜索 Agent...")
            self.web_search_agent = WebSearchAgent()
            print(f"[RAG v2.2] 联网搜索 Agent 可用: {self.web_search_agent.is_available()}")
        else:
            self.web_search_agent = None

        # 加载症状共现数据（从古籍和方剂数据中学习）
        self._load_cooccurrence_data()
        
        self.collection_name = "tcm_knowledge_v2"  # 使用新集合名称，避免旧编码数据干扰
        
        # 获取当前嵌入模型输出的维度
        self._embedding_dim = len(self.embedder.encode(["测试"])[0])
        print(f"[RAG v2.2] 当前嵌入模型维度: {self._embedding_dim}")
        
        try:
            _collection = self.chroma_client.get_collection(self.collection_name)
            doc_count = _collection.count()
            
            # 检查已有文档的嵌入维度是否与当前模型一致
            if doc_count > 0:
                try:
                    sample = _collection.get(include=["embeddings"], limit=1)
                    existing_dim = sample["embeddings"].shape[1]
                    print(f"[RAG v2.2] 知识库现有文档维度: {existing_dim}")
                    
                    if existing_dim != self._embedding_dim:
                        print(f"[RAG v2.2] 维度不匹配（库{existing_dim} vs 模型{self._embedding_dim}），删除旧知识库并重建...")
                        self.chroma_client.delete_collection(self.collection_name)
                        _collection = self.chroma_client.create_collection(
                            name=self.collection_name,
                            metadata={"description": "中医古籍知识库v2（中文症状名）"}
                        )
                        print("[RAG v2.2] 初始化完成，已重建知识库v2")
                    else:
                        print(f"[RAG v2.2] 初始化完成，当前知识库文档数: {doc_count}")
                except Exception as e:
                    print(f"[RAG v2.2] 维度检查失败: {e}，将尝试重建知识库")
                    try:
                        self.chroma_client.delete_collection(self.collection_name)
                    except Exception:
                        pass
                    _collection = self.chroma_client.create_collection(
                        name=self.collection_name,
                        metadata={"description": "中医古籍知识库v2（中文症状名）"}
                    )
                    print("[RAG v2.2] 初始化完成，已重建知识库v2")
            else:
                print(f"[RAG v2.2] 初始化完成，当前知识库文档数: 0")
        except Exception:
            _collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": "中医古籍知识库v2（中文症状名）"}
            )
            print("[RAG v2.2] 初始化完成，新建知识库v2")
    
    def _load_cooccurrence_data(self):
        """从方剂数据库加载症状共现数据"""
        print("[RAG v2.2] 加载症状共现数据...")
        
        # 从方剂数据库中提取症状共现模式
        for formula_id, formula in FORMULA_DATABASE.items():
            symptoms = formula.get('symptoms', [])
            if len(symptoms) >= 2:
                # 为方剂中的每对症状添加共现记录
                for i, sa in enumerate(symptoms):
                    for sb in symptoms[i+1:]:
                        # 将症状名称转换为ID（简化处理）
                        sa_id = self._symptom_name_to_id(sa)
                        sb_id = self._symptom_name_to_id(sb)
                        if sa_id and sb_id:
                            self.cooccurrence_analyzer.add_cooccurrence(
                                sa_id, sb_id, 0.8, f"方剂:{formula['name']}", 1
                            )
        
        print(f"[RAG v2.2] 症状共现数据加载完成")
    
    def _symptom_name_to_id(self, name: str) -> Optional[str]:
        """将症状名称转换为ID"""
        # 简化映射：直接查找SYMPTOM_MAP
        for sid, info in SYMPTOM_MAP.items():
            if info['name'] == name or name in info['aliases']:
                return sid
        return None
    
    def _estimate_era(self, book_name: str) -> str:
        """根据书名估算朝代/年代"""
        era_map = {
            "黄帝内经": "先秦-西汉",
            "素问": "先秦-西汉",
            "灵枢": "先秦-西汉",
            "伤寒论": "东汉",
            "金匮要略": "东汉",
            "神农本草经": "东汉",
            "难经": "西汉",
            "备急千金要方": "唐",
            "千金翼方": "唐",
            "外台秘要": "唐",
            "医宗金鉴": "清",
            "本草纲目": "明",
            "温病条辨": "清",
            "温热论": "清",
            "医林改错": "清",
            "景岳全书": "明",
            "脾胃论": "金元",
            "丹溪心法": "元",
            "格致余论": "元",
            "儒门事亲": "金",
            "小儿药证直诀": "宋",
            "太平惠民和剂局方": "宋",
            "圣济总录": "宋",
            "诸病源候论": "隋",
            "脉经": "晋",
            "针灸甲乙经": "晋",
        }
        for key, era in era_map.items():
            if key in book_name:
                return era
        return "未知"
    
    def _get_collection(self):
        """重新获取集合引用"""
        try:
            return self.chroma_client.get_collection(self.collection_name)
        except Exception:
            return self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": "中医古籍知识库v2（中文症状名）"}
            )
    
    def add_documents(self, documents: List[Dict]) -> None:
        """向知识库添加文档"""
        texts = []
        metadatas = []
        ids = []
        seen_ids = set()
        
        for doc in documents:
            text = doc["text"]
            metadata = doc.get("metadata", {})
            doc_id = metadata.get("chunk_id", f"chunk_{hashlib.md5(text.encode()).hexdigest()[:12]}")
            
            if doc_id in seen_ids:
                doc_id = f"{doc_id}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:6]}"
            seen_ids.add(doc_id)
            
            texts.append(text)
            metadatas.append(metadata)
            ids.append(doc_id)
        
        embeddings = self.embedder.encode(texts)
        collection = self._get_collection()
        collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"[RAG v2.0] 成功添加 {len(documents)} 条文档")
    
    # ========== v2.0 核心工作流 ==========

    def _classify_web_source_type(self, source_url: str, title: str) -> str:
        """根据URL/标题对联网来源进行粗略分级"""
        text = (source_url + " " + title).lower()
        if any(k in text for k in ['gov.cn', 'edu.cn', 'hospital', 'cma', 'tcm', '中医药']):
            return 'P1'
        if any(k in text for k in ['pubmed', 'ncbi', 'cnki', 'wanfang', 'journal', '核心期刊']):
            return 'P0'
        if any(k in text for k in ['baike', '百科', 'zhihu', '知乎', '健康']):
            return 'P4'
        return 'P5'

    def _assess_web_search_results(self, web_search_results: List[Dict]) -> List[Dict]:
        """
        对联网搜索结果逐条进行批判性思维可信度评估。
        返回字段：source_id, title, source_url, grade, is_adopted, total_score, limitations, adoption_reason
        """
        assessments = []
        for idx, result in enumerate(web_search_results):
            content = result.get('full_content', '') or result.get('content', '')
            title = result.get('title', '') or f"联网结果{idx+1}"
            source_url = result.get('url', '') or result.get('source', '')
            source_type = self._classify_web_source_type(source_url, title)

            content_text = (title + ' ' + content)
            evidence_type = 'case_series'
            if any(k in content_text for k in ['随机对照', 'RCT', '系统综述', 'Meta分析', 'meta分析', '双盲']):
                evidence_type = 'RCT'
            elif any(k in content_text for k in ['队列研究', '病例对照', '临床研究', '临床观察']):
                evidence_type = 'cohort'
            elif any(k in content_text for k in ['个案', '病例报告', '医案']):
                evidence_type = 'case_report'
            elif any(k in content_text for k in ['理论', '经验', '探讨']):
                evidence_type = 'theory'

            year = 0
            year_match = re.search(r'(19|20)\d{2}', content_text)
            if year_match:
                year = int(year_match.group(0))

            assessment = self.credibility_engine.assess_source_credibility(
                source_text=content,
                source_url=source_url,
                source_type=source_type,
                author_title=title,
                publish_year=year,
                evidence_type=evidence_type,
                symptom_match=0.7,
                population_match=0.7,
                conflict_check=0.9,
            )
            assessments.append({
                "source_id": result.get('id', f'WS-{idx+1}'),
                "title": title,
                "source_url": source_url,
                "grade": assessment.grade,
                "is_adopted": assessment.is_adopted,
                "total_score": round(assessment.total_score, 2),
                "limitations": assessment.limitations,
                "adoption_reason": assessment.adoption_reason,
            })
        return assessments

    def _text_overlap(self, text_a: str, text_b: str) -> float:
        """计算两段中文文本的字符集重叠度（0-1）"""
        chars_a = set(re.findall(r'[\u4e00-\u9fff]', text_a or ''))
        chars_b = set(re.findall(r'[\u4e00-\u9fff]', text_b or ''))
        if not chars_a or not chars_b:
            return 0.0
        return len(chars_a & chars_b) / min(len(chars_a), len(chars_b))

    def _compute_kb_corroboration(self, web_search_results: List[Dict],
                                  adopted_source_ids: set,
                                  chunks: List[RetrievedChunk]) -> List[Dict]:
        """检查被采纳的联网结果是否被知识库古籍检索结果佐证"""
        corroborations = []
        for result in web_search_results:
            sid = result.get('id', '')
            if sid not in adopted_source_ids:
                continue
            content = result.get('full_content', '') or result.get('content', '')
            title = result.get('title', '')
            max_overlap = 0.0
            best_chunk = None
            for chunk in chunks:
                overlap = self._text_overlap(content, chunk.text)
                if overlap > max_overlap:
                    max_overlap = overlap
                    best_chunk = chunk
            status = "已佐证" if max_overlap >= 0.15 else "待导入"
            corroborations.append({
                "source_id": sid,
                "title": title,
                "corroboration_status": status,
                "overlap_score": round(max_overlap, 3),
                "best_match_source": f"《{best_chunk.source_book}》·{best_chunk.source_section}" if best_chunk else None,
            })
        return corroborations

    def diagnose_with_thinking(self, query: str, llm_client=None) -> DiagnosisResult:
        """
        v2.1 完整辨证流程（双源验证 + 证型识别 + 禁忌检查）
        7步工作流：症状标准化→古籍检索→方剂药物匹配→证型识别→禁忌规则检查→构建双源验证提示词→AI生成→输出校验
        """
        thinking_process = []
        total_start = time.time()
        
        # Step 1: 症状标准化 + 编号识别
        step1 = ThinkingStep(
            step_name="症状标准化",
            step_description="提取用户症状并映射到标准编号体系",
            start_time=time.time()
        )
        
        symptoms = find_symptoms_by_text(query)
        symptom_ids = [s['id'] for s in symptoms]
        symptom_names = [s['name'] for s in symptoms]
        
        step1.details = {
            "original_query": query,
            "extracted_symptoms": symptom_names,
            "symptom_count": len(symptoms),
            "symptom_ids": symptom_ids,
        }
        step1.end_time = time.time()
        step1.status = "completed"
        thinking_process.append({
            "step": 1,
            "name": step1.step_name,
            "description": step1.step_description,
            "time_ms": round((step1.end_time - step1.start_time) * 1000, 2),
            "status": step1.status,
            "details": step1.details
        })
        
        # Step 2: 联网搜索（实时获取中医临床与文献信息）
        step2 = ThinkingStep(
            step_name="联网搜索",
            step_description="调用 Yunwu AI 联网搜索能力，优先获取最新中医临床与文献信息",
            start_time=time.time()
        )

        web_search_results = []
        try:
            if self.web_search_agent and self.web_search_agent.is_available():
                search_query = query.replace("症状：", "").replace("，", " ")[:80]
                web_search_results = self.web_search_agent.search(
                    search_query,
                    context="中医临床、症状调理、中药方剂",
                    max_results=3
                )
                print(f"[RAG v2.2] 联网搜索返回 {len(web_search_results)} 条结果")
            else:
                print("[RAG v2.2] 联网搜索 Agent 未启用")
        except Exception as e:
            print(f"[RAG v2.2] 联网搜索失败: {e}")

        step2.details = {
            "search_query": query.replace("症状：", ""),
            "result_count": len(web_search_results),
            "results_preview": [
                {
                    "title": r.get("title", ""),
                    "source": r.get("source", ""),
                    "content_preview": r.get("content", "")[:80] + "..." if len(r.get("content", "")) > 80 else r.get("content", "")
                }
                for r in web_search_results[:3]
            ]
        }
        step2.end_time = time.time()
        step2.status = "completed" if web_search_results else "warning"
        thinking_process.append({
            "step": 2,
            "name": step2.step_name,
            "description": step2.step_description,
            "time_ms": round((step2.end_time - step2.start_time) * 1000, 2),
            "status": step2.status,
            "details": step2.details
        })

        # Step 3: 搜索结果批判性评估
        step3 = ThinkingStep(
            step_name="搜索结果批判性评估",
            step_description="对联网搜索结果进行三阶九维可信度评估，决定是否采纳",
            start_time=time.time()
        )

        web_search_credibility = []
        if web_search_results:
            try:
                web_search_credibility = self._assess_web_search_results(web_search_results)
            except Exception as e:
                print(f"[RAG v2.2] 联网结果评估失败: {e}")

        adopted = [a for a in web_search_credibility if a["is_adopted"]]
        rejected = [a for a in web_search_credibility if not a["is_adopted"]]

        step3.details = {
            "assessed_count": len(web_search_credibility),
            "adopted_count": len(adopted),
            "rejected_count": len(rejected),
            "adopted_sources": [
                {
                    "source_id": a["source_id"],
                    "title": a["title"],
                    "grade": a["grade"],
                    "total_score": a["total_score"],
                    "adoption_reason": a["adoption_reason"],
                    "limitations": a["limitations"]
                }
                for a in adopted
            ],
            "rejected_sources": [
                {
                    "source_id": a["source_id"],
                    "title": a["title"],
                    "grade": a["grade"],
                    "total_score": a["total_score"],
                    "adoption_reason": a["adoption_reason"]
                }
                for a in rejected
            ]
        }
        step3.end_time = time.time()
        step3.status = "completed"
        thinking_process.append({
            "step": 3,
            "name": step3.step_name,
            "description": step3.step_description,
            "time_ms": round((step3.end_time - step3.start_time) * 1000, 2),
            "status": step3.status,
            "details": step3.details
        })

        # Step 4: 知识库检索佐证
        step4 = ThinkingStep(
            step_name="知识库检索佐证",
            step_description="从中医古籍知识库检索相关条文，对采纳的联网结果进行佐证/缺项判定",
            start_time=time.time()
        )

        chunks = self.retrieve(query, top_k=5)

        adopted_source_ids = {a["source_id"] for a in adopted}
        kb_corroboration = []
        if adopted_source_ids:
            kb_corroboration = self._compute_kb_corroboration(
                web_search_results, adopted_source_ids, chunks
            )

        step4.details = {
            "total_documents": self._get_collection().count(),
            "retrieved_count": len(chunks),
            "retrieved_sources": [
                {
                    "book": c.source_book,
                    "section": c.source_section,
                    "score": round(c.score, 4),
                    "text_preview": c.text[:80] + "..." if len(c.text) > 80 else c.text
                }
                for c in chunks
            ],
            "web_kb_corroboration": kb_corroboration
        }
        step4.end_time = time.time()
        step4.status = "completed" if chunks else "warning"
        thinking_process.append({
            "step": 4,
            "name": step4.step_name,
            "description": step4.step_description,
            "time_ms": round((step4.end_time - step4.start_time) * 1000, 2),
            "status": step4.status,
            "details": step4.details
        })

        # Step 5: 联网数据入库决策
        step5 = ThinkingStep(
            step_name="联网数据入库决策",
            step_description="对知识库未佐证的采纳结果生成入库建议，暂不实际写入",
            start_time=time.time()
        )

        import_suggestions = []
        for corr in kb_corroboration:
            if corr["corroboration_status"] != "待导入":
                continue
            assessment = next(
                (a for a in web_search_credibility if a["source_id"] == corr["source_id"]),
                None
            )
            score = assessment["total_score"] if assessment else 0.0
            priority = "高" if score >= 4.0 else "中" if score >= 3.0 else "低"
            import_suggestions.append({
                "type": "联网数据待入库",
                "title": corr["title"],
                "reason": (
                    f"该联网来源已被采纳但知识库未找到佐证（最高字符重叠度 {corr['overlap_score']}），"
                    f"建议审核后作为临床/古籍补充数据入库。"
                ),
                "priority": priority
            })

        step5.details = {
            "import_suggestion_count": len(import_suggestions),
            "import_suggestions": import_suggestions[:5]
        }
        step5.end_time = time.time()
        step5.status = "completed"
        thinking_process.append({
            "step": 5,
            "name": step5.step_name,
            "description": step5.step_description,
            "time_ms": round((step5.end_time - step5.start_time) * 1000, 2),
            "status": step5.status,
            "details": step5.details
        })

        # Step 6: 方剂药物匹配（基于症状编号）
        step6 = ThinkingStep(
            step_name="方剂药物匹配",
            step_description="根据症状编号匹配方剂库和药物库",
            start_time=time.time()
        )

        matched_formulas = find_formulas_by_symptoms(symptom_ids) if symptom_ids else []
        matched_drugs = find_drugs_by_symptoms(symptom_ids) if symptom_ids else []

        # 获取禁忌信息（旧版兼容）
        contraindications = []
        if matched_formulas:
            for formula in matched_formulas[:3]:
                formula_detail = get_formula_by_id(formula['id'])
                if formula_detail and formula_detail['contraindications']:
                    contraindications.append({
                        'type': '方剂禁忌',
                        'name': formula_detail['name'],
                        'contraindications': formula_detail['contraindications']
                    })

        if matched_drugs:
            drug_ids = [d['id'] for d in matched_drugs[:5]]
            drug_contras = get_drug_contraindications(drug_ids)
            for dc in drug_contras:
                contraindications.append({
                    'type': '药物禁忌',
                    'name': dc['drug_name'],
                    'contraindications': dc['contraindications']
                })

        step6.details = {
            "matched_formulas_count": len(matched_formulas),
            "matched_drugs_count": len(matched_drugs),
            "top_formulas": [f['name'] for f in matched_formulas[:3]],
            "top_drugs": [d['name'] for d in matched_drugs[:5]],
            "contraindications_count": len(contraindications),
        }
        step6.end_time = time.time()
        step6.status = "completed"
        thinking_process.append({
            "step": 6,
            "name": step6.step_name,
            "description": step6.step_description,
            "time_ms": round((step6.end_time - step6.start_time) * 1000, 2),
            "status": step6.status,
            "details": step6.details
        })

        # Step 7: 证型识别
        step7 = ThinkingStep(
            step_name="证型识别",
            step_description="基于症状匹配证型数据库，识别可能的证型",
            start_time=time.time()
        )

        matched_syndromes = find_syndromes_by_symptoms(symptom_ids) if symptom_ids else []
        syndrome_analysis = []
        syndrome_matched = False
        syndrome_match_score = 0.0

        if matched_syndromes:
            top_syndrome = matched_syndromes[0]
            syndrome_detail = get_syndrome_by_id(top_syndrome['id'])
            if syndrome_detail:
                syndrome_analysis.append({
                    'id': top_syndrome['id'],
                    'name': syndrome_detail['name'],
                    'system': syndrome_detail['system'],
                    'match_score': top_syndrome['match_score'],
                    'severity': syndrome_detail['severity'],
                    'pathogenesis': syndrome_detail['pathogenesis'],
                    'treatment_principle': syndrome_detail['treatment_principle'],
                    'main_formula': syndrome_detail['main_formula'],
                    'key_signs': syndrome_detail['key_signs'],
                    'differentiation': syndrome_detail.get('differentiation', []),
                })
                syndrome_matched = True
                syndrome_match_score = top_syndrome['match_score']

            for ms in matched_syndromes[1:3]:
                sd = get_syndrome_by_id(ms['id'])
                if sd:
                    syndrome_analysis.append({
                        'id': ms['id'],
                        'name': sd['name'],
                        'system': sd['system'],
                        'match_score': ms['match_score'],
                        'severity': sd['severity'],
                        'pathogenesis': sd['pathogenesis'],
                        'treatment_principle': sd['treatment_principle'],
                        'main_formula': sd['main_formula'],
                        'key_signs': sd['key_signs'],
                        'differentiation': sd.get('differentiation', []),
                    })

        step7.details = {
            "matched_syndromes_count": len(matched_syndromes),
            "top_syndrome": syndrome_analysis[0]['name'] if syndrome_analysis else '未识别',
            "match_score": round(syndrome_match_score, 2),
            "severity": syndrome_analysis[0]['severity'] if syndrome_analysis else '未知',
            "system": syndrome_analysis[0]['system'] if syndrome_analysis else '未知',
        }
        step7.end_time = time.time()
        step7.status = "completed" if syndrome_matched else "warning"

        # 相似患者匹配（在证型识别后执行）
        similar_patients = []
        if len(symptom_ids) >= 3:
            target_patient = {
                "patient_id": "current_user",
                "symptoms": {sid: 1.0 for sid in symptom_ids},
                "medications": [],
                "diagnosis": syndrome_analysis[0]['name'] if syndrome_analysis else "未知"
            }
            similar_patients = self.similar_patient_matcher.find_similar_patients(
                target_patient, top_k=3
            )

        thinking_process.append({
            "step": 7,
            "name": step7.step_name,
            "description": step7.step_description,
            "time_ms": round((step7.end_time - step7.start_time) * 1000, 2),
            "status": step7.status,
            "details": step7.details
        })

        # Step 8: 禁忌规则检查（基于十八反/十九畏/七情配伍）
        step8 = ThinkingStep(
            step_name="禁忌规则检查",
            step_description="基于十八反、十九畏、七情配伍规则检查药物安全性",
            start_time=time.time()
        )

        drug_relations = []
        # 收集所有匹配方剂中的药物ID
        all_drug_ids = []
        for formula in matched_formulas[:3]:
            fd = get_formula_by_id(formula['id'])
            if fd and fd.get('composition'):
                for comp in fd['composition']:
                    if 'id' in comp and comp['id']:
                        all_drug_ids.append(comp['id'])

        # 添加单独匹配的药物
        for drug in matched_drugs[:5]:
            if drug['id'] not in all_drug_ids:
                all_drug_ids.append(drug['id'])

        # 去重
        all_drug_ids = list(set(all_drug_ids))

        # 执行禁忌检查（需要转换药物ID到禁忌规则库的ID体系）
        if len(all_drug_ids) >= 2:
            # 构建从公式DB药物ID到规则库药物ID的映射
            from drug_formula_db import DRUG_DATABASE
            name_to_formula_id = {d['name']: did for did, d in DRUG_DATABASE.items()}
            formula_to_rule = {}
            for rule_id, formula_id in {
                'DR-JB-001': name_to_formula_id.get('麻黄'),
                'DR-JB-002': name_to_formula_id.get('桂枝'),
                'DR-HQ-001': name_to_formula_id.get('半夏'),
                'DR-BY-002': name_to_formula_id.get('甘草'),
                'DR-QT-004': name_to_formula_id.get('附子'),
                'DR-BY-001': name_to_formula_id.get('人参'),
            }.items():
                if formula_id:
                    formula_to_rule[formula_id] = rule_id

            # 转换药物ID
            rule_drug_ids = [formula_to_rule.get(did, did) for did in all_drug_ids]
            drug_relations = check_all_contraindications(rule_drug_ids)

        # 分类统计
        critical_count = sum(1 for r in drug_relations if '🔴' in r.get('alert', ''))
        warning_count = sum(1 for r in drug_relations if '🟠' in r.get('alert', ''))
        good_count = sum(1 for r in drug_relations if '🟢' in r.get('alert', ''))

        step8.details = {
            "checked_drug_count": len(all_drug_ids),
            "checked_pairs": len(all_drug_ids) * (len(all_drug_ids) - 1) // 2 if len(all_drug_ids) >= 2 else 0,
            "critical_alerts": critical_count,
            "warning_alerts": warning_count,
            "good_relations": good_count,
            "drug_ids_checked": all_drug_ids,
        }
        step8.end_time = time.time()
        step8.status = "completed"
        thinking_process.append({
            "step": 8,
            "name": step8.step_name,
            "description": step8.step_description,
            "time_ms": round((step8.end_time - step8.start_time) * 1000, 2),
            "status": step8.status,
            "details": step8.details
        })

        # Step 9: 批判性思维验证（古籍来源可信度 + 症状共现 + 副作用检测）
        step9 = ThinkingStep(
            step_name="批判性思维验证",
            step_description="对检索到的古籍进行可信度评估，进行症状共现分析和副作用检测",
            start_time=time.time()
        )

        credibility_assessment = []
        cooccurrence_analysis = {}
        adverse_detection = {}
        knowledge_gap_report = []

        # 9a: 对检索到的古籍进行可信度评估
        if chunks:
            for chunk in chunks[:3]:
                # 估算古籍年代
                era_year = 0
                era_map = {
                    "先秦-西汉": -200, "东汉": 150, "晋": 300, "隋": 600,
                    "唐": 750, "宋": 1000, "金元": 1200, "明": 1500, "清": 1700
                }
                era = self._estimate_era(chunk.source_book)
                era_year = era_map.get(era, 0)

                assessment = self.credibility_engine.assess_source_credibility(
                    source_text=chunk.text,
                    source_type="古籍文献",
                    author_title=chunk.source_book,
                    publish_year=era_year,
                    evidence_type="经典文献",
                    symptom_match=0.8,  # 已匹配到症状
                    population_match=0.7,  # 通用人群
                    conflict_check=0.9  # 内部一致性高
                )
                # 转换为API需要的字典格式
                credibility_assessment.append({
                    "source_type": "古籍文献",
                    "overall_score": getattr(assessment, 'overall_score', 0),
                    "overall_grade": getattr(assessment, 'overall_grade', 'N/A'),
                    "literature_quality": {
                        "grade": getattr(assessment, 'literature_quality_grade', 'N/A'),
                        "era": era,
                        "author": chunk.source_book
                    },
                    "clinical_validation": {
                        "grade": getattr(assessment, 'clinical_validation_grade', 'N/A'),
                        "sample_size": "N/A"
                    },
                    "cross_validation": {
                        "grade": getattr(assessment, 'cross_validation_grade', 'N/A'),
                        "consistency_score": getattr(assessment, 'consistency_score', 'N/A')
                    },
                    "red_flags": getattr(assessment, 'red_flags', [])
                })

        # 9b: 症状共现分析（检测异常症状组合，触发副作用警报）
        if len(symptom_ids) >= 2:
            cooccurrence_analysis = self.cooccurrence_analyzer.analyze_symptom_combination(
                symptom_ids
            )

            # 如果有异常共现，生成知识缺口报告
            if cooccurrence_analysis.get("anomaly_detected"):
                for anomaly in cooccurrence_analysis.get("anomalies", []):
                    knowledge_gap_report.append({
                        "type": "异常症状共现",
                        "description": f"{anomaly['symptom_a_name']} + {anomaly['symptom_b_name']} 共现强度异常低({anomaly['actual_cooccurrence']:.2f})，可能提示药物副作用或并发症",
                        "severity": "高",
                        "suggested_action": "建议医师重点排查药物不良反应或鉴别诊断"
                    })

        # 9c: 时间窗口副作用检测（简化实现）
        # 从query中提取时间线索
        time_keywords = {
            "最近": 7, "昨天": 1, "今天": 0, "上周": 7, "上个月": 30,
            "持续": 30, "一直": 30, "突然": 0, "刚刚": 0
        }
        symptom_onset_days = 7  # 默认7天
        for kw, days in time_keywords.items():
            if kw in query:
                symptom_onset_days = days
                break

        # 简化副作用检测：基于症状共现异常和时间窗口
        adverse_detection = {
            "risk_level": "低风险",
            "adverse_events": [],
            "time_window_days": symptom_onset_days,
            "detection_method": "基于症状共现分析和时间窗口的简化检测"
        }

        # 如果有异常共现，生成副作用警报
        if cooccurrence_analysis.get("anomaly_detected"):
            for anomaly in cooccurrence_analysis.get("anomalies", []):
                event = {
                    "adverse_type": "异常症状组合",
                    "severity": "中等" if anomaly.get("deviation", 0) < 0.5 else "严重",
                    "related_drugs": [],
                    "time_window": f"{symptom_onset_days}天内",
                    "recommendation": "建议医师排查药物不良反应或鉴别诊断",
                    "symptom_pair": f"{anomaly.get('symptom_a_name', '未知')} + {anomaly.get('symptom_b_name', '未知')}"
                }
                adverse_detection["adverse_events"].append(event)
                adverse_detection["risk_level"] = "中风险"

        # 如果有方剂匹配，进一步检测药物相关副作用
        if matched_formulas and matched_formulas[0]:
            top_formula = get_formula_by_id(matched_formulas[0]['id'])
            if top_formula:
                formula_drugs = [comp['name'] for comp in top_formula.get('composition', [])]
                adverse_detection["checked_drugs"] = formula_drugs

        # 9d: 古籍未覆盖症状入库建议（补充已有联网数据入库建议）
        uncovered_symptoms = []
        for sid in symptom_ids:
            has_coverage = any(sid == self._symptom_name_to_id(s) for s in
                [c.text for c in chunks] if self._symptom_name_to_id(s))
            if not has_coverage:
                uncovered_symptoms.append(sid)

        if uncovered_symptoms:
            for sid in uncovered_symptoms[:3]:
                desc = get_id_description(sid) or sid
                import_suggestions.append({
                    "type": "古籍知识缺口",
                    "symptom_id": sid,
                    "description": f"症状 {desc} 在检索到的古籍中缺乏直接记载",
                    "priority": "中",
                    "suggested_source": "建议检索《备急千金要方》《医宗金鉴》等补充"
                })

        step9.details = {
            "credibility_assessed_count": len(credibility_assessment),
            "avg_credibility_score": round(
                sum(c.get("overall_score", 0) for c in credibility_assessment) / max(len(credibility_assessment), 1), 2
            ) if credibility_assessment else 0,
            "cooccurrence_anomaly_detected": cooccurrence_analysis.get("anomaly_detected", False),
            "adverse_events_detected": len(adverse_detection.get("adverse_events", [])),
            "similar_patients_found": len(similar_patients),
            "knowledge_gaps": len(knowledge_gap_report),
            "import_suggestions": len(import_suggestions),
        }
        step9.end_time = time.time()
        step9.status = "completed"
        thinking_process.append({
            "step": 9,
            "name": step9.step_name,
            "description": step9.step_description,
            "time_ms": round((step9.end_time - step9.start_time) * 1000, 2),
            "status": step9.status,
            "details": step9.details
        })

        # Step 10: 构建双源验证提示词
        step10 = ThinkingStep(
            step_name="构建双源验证提示词",
            step_description="整合联网搜索可信度、知识库佐证、证型分析、方剂药物数据和禁忌检查结果，构建结构化提示词",
            start_time=time.time()
        )

        prompt = self.build_v2_prompt(
            query, symptoms, chunks, matched_formulas, matched_drugs,
            syndrome_analysis=syndrome_analysis,
            drug_relations=drug_relations,
            web_search_results=web_search_results,
            web_search_credibility=web_search_credibility,
            kb_corroboration=kb_corroboration
        )

        step10.details = {
            "prompt_length": len(prompt),
            "web_results_count": len(web_search_results),
            "adopted_web_results": len(adopted),
            "kb_corroborated_count": sum(1 for c in kb_corroboration if c["corroboration_status"] == "已佐证"),
            "references_count": len(chunks),
            "formulas_count": len(matched_formulas),
            "drugs_count": len(matched_drugs),
            "syndromes_count": len(syndrome_analysis),
            "relations_count": len(drug_relations),
        }
        step10.end_time = time.time()
        step10.status = "completed"
        thinking_process.append({
            "step": 10,
            "name": step10.step_name,
            "description": step10.step_description,
            "time_ms": round((step10.end_time - step10.start_time) * 1000, 2),
            "status": step10.status,
            "details": step10.details
        })

        # Step 11: AI生成回答
        step11 = ThinkingStep(
            step_name="AI生成双源验证报告",
            step_description="调用大语言模型基于双源数据生成结构化报告",
            start_time=time.time()
        )

        if llm_client is None:
            raw_output = self._format_fallback_result(
                query, symptoms, chunks, matched_formulas, matched_drugs,
                syndrome_analysis=syndrome_analysis,
                drug_relations=drug_relations
            )
            step11.details = {"llm_provider": "fallback", "note": "使用本地结构化输出（无API Key）"}
        else:
            llm_start = time.time()
            raw_output = llm_client.generate(prompt, max_tokens=8000)
            llm_time = (time.time() - llm_start) * 1000
            step11.details = {
                "llm_provider": getattr(llm_client, 'model', 'unknown'),
                "llm_time_ms": round(llm_time, 2),
                "output_length": len(raw_output)
            }

        step11.end_time = time.time()
        step11.status = "completed"
        thinking_process.append({
            "step": 11,
            "name": step11.step_name,
            "description": step11.step_description,
            "time_ms": round((step11.end_time - step11.start_time) * 1000, 2),
            "status": step11.status,
            "details": step11.details
        })

        # Step 12: 输出校验 + 结构化提取
        step12 = ThinkingStep(
            step_name="输出校验与结构化",
            step_description="校验输出质量，提取结构化信息",
            start_time=time.time()
        )

        passed, verified_output = self.verify_output(raw_output, chunks)

        # 提取结构化信息
        constitution = self._extract_constitution(verified_output)
        syndrome = self._extract_syndrome(verified_output)

        sources = []
        for chunk in chunks:
            sources.append({
                "book": chunk.source_book,
                "section": chunk.source_section,
                "original_text": chunk.original_text,
                "text": chunk.text
            })

        step12.details = {
            "verification_passed": passed,
            "sources_found": len(re.findall(r'\[出处：《(.+?)》·(.+?)\]', verified_output)),
            "constitution": constitution,
            "syndrome": syndrome,
        }
        step12.end_time = time.time()
        step12.status = "completed" if passed else "warning"
        thinking_process.append({
            "step": 12,
            "name": step12.step_name,
            "description": step12.step_description,
            "time_ms": round((step12.end_time - step12.start_time) * 1000, 2),
            "status": step12.status,
            "details": step12.details
        })

        # Step 13: 返回结果
        total_end = time.time()
        thinking_process.append({
            "step": 13,
            "name": "返回结果",
            "description": "整理并返回双源验证报告",
            "time_ms": 0,
            "status": "completed",
            "details": {
                "total_time_ms": round((total_end - total_start) * 1000, 2),
                "result_summary": f"体质：{constitution}，证候：{syndrome}"
            }
        })
        
        return DiagnosisResult(
            constitution=constitution,
            syndrome=syndrome,
            advice=verified_output,
            sources=sources,
            warning="【重要提示】本结果仅供参考，不能替代专业医生诊断。如有不适，请及时就医。",
            thinking_process=thinking_process,
            total_time_ms=round((total_end - total_start) * 1000, 2),
            # v2.0兼容字段
            symptom_analysis={
                "extracted_symptoms": symptoms,
                "symptom_ids": symptom_ids,
            },
            matched_formulas=matched_formulas[:5],
            matched_drugs=matched_drugs[:5],
            contraindications=contraindications,
            classic_sources=[{"book": c.source_book, "section": c.source_section} for c in chunks],
            # v2.1新增字段
            syndrome_analysis=syndrome_analysis,
            drug_relations=drug_relations,
            syndrome_matched=syndrome_matched,
            syndrome_match_score=syndrome_match_score,
            # v2.2新增字段（批判性思维+副作用检测）
            credibility_assessment=credibility_assessment,
            cooccurrence_analysis=cooccurrence_analysis,
            adverse_detection=adverse_detection,
            similar_patients=similar_patients,
            knowledge_gap_report=knowledge_gap_report,
            import_suggestions=import_suggestions,
        )
    
    def build_v2_prompt(self, query: str, symptoms: List[Dict], chunks: List[RetrievedChunk], 
                        formulas: List[Dict], drugs: List[Dict],
                        syndrome_analysis: List[Dict] = None,
                        drug_relations: List[Dict] = None,
                        web_search_results: List[Dict] = None,
                        web_search_credibility: List[Dict] = None,
                        kb_corroboration: List[Dict] = None) -> str:
        """
        v2.3 联网搜索优先 + 双源验证提示词构建
        整合：症状分析 + 联网搜索可信度评估 + 知识库佐证 + 证型分析 +
              方剂药物数据（含疗效统计） + 禁忌规则检查
        """
        syndrome_analysis = syndrome_analysis or []
        drug_relations = drug_relations or []
        web_search_results = web_search_results or []
        web_search_credibility = web_search_credibility or []
        kb_corroboration = kb_corroboration or []

        # 症状分析部分
        symptom_text = "\n".join([
            f"  • {s['name']} [{s['id']}] ({s['part']}/{s['category']}) - 古籍参考：{', '.join(s['classic_refs'])}"
            for s in symptoms
        ]) if symptoms else "  未识别到标准症状"

        # 古籍检索部分
        references = []
        for i, chunk in enumerate(chunks, 1):
            ref = f"[古籍参考{i}]\n出处：《{chunk.source_book}》·{chunk.source_section}\n内容：{chunk.text}"
            if chunk.original_text:
                ref += f"\n原文：{chunk.original_text}"
            references.append(ref)
        references_text = "\n\n".join(references) if references else "暂无古籍检索结果"

        # 联网搜索原始结果
        web_search_text = ""
        if web_search_results:
            ws_lines = []
            for i, r in enumerate(web_search_results[:3], 1):
                ws_lines.append(
                    f"[联网参考{i}]\n"
                    f"标题：{r.get('title', '')}\n"
                    f"来源：{r.get('source', 'AI搜索')}\n"
                    f"内容：{r.get('content', '')[:400]}"
                )
            web_search_text = "\n\n".join(ws_lines)
        else:
            web_search_text = "  未获取到联网搜索结果"

        # 联网搜索结果可信度评估
        web_cred_text = ""
        if web_search_credibility:
            adopted = [a for a in web_search_credibility if a["is_adopted"]]
            rejected = [a for a in web_search_credibility if not a["is_adopted"]]
            web_cred_text += f"已采纳 {len(adopted)}/{len(web_search_credibility)} 条：\n"
            for a in adopted:
                web_cred_text += (
                    f"  ✅ [{a['grade']}级/得分{a['total_score']}] {a['title']} - {a['adoption_reason']}\n"
                    f"     局限性：{'; '.join(a['limitations']) if a['limitations'] else '无'}\n"
                )
            if rejected:
                web_cred_text += f"未采纳 {len(rejected)} 条：\n"
                for a in rejected:
                    web_cred_text += f"  ❌ [{a['grade']}级/得分{a['total_score']}] {a['title']} - {a['adoption_reason']}\n"
        else:
            web_cred_text = "  未对联网搜索结果进行评估"

        # 知识库佐证状态
        kb_corr_text = ""
        if kb_corroboration:
            for c in kb_corroboration:
                kb_corr_text += (
                    f"  • {c['title']} [{c['source_id']}]: {c['corroboration_status']} "
                    f"(重叠度 {c['overlap_score']})\n"
                )
        else:
            kb_corr_text = "  无采纳的联网搜索结果需佐证"

        # 方剂匹配部分（含疗效统计）
        formula_text = ""
        if formulas:
            for i, f in enumerate(formulas[:3], 1):
                formula_detail = get_formula_by_id(f['id'])
                if formula_detail:
                    composition = ", ".join([d['name'] for d in formula_detail['composition']])
                    stats = formula_detail.get('effectiveness_stats', {})
                    formula_text += f"""
[方剂{i}] {formula_detail['name']} [{f['id']}]
  来源：《{formula_detail['source']}》
  证型：{formula_detail['syndrome']}
  症状：{', '.join(formula_detail['symptoms'])}
  组成：{composition}
  禁忌：{', '.join(formula_detail['contraindications'])}
  疗效统计：总病例 {stats.get('total_cases', 'N/A')}，有效 {stats.get('effective_cases', 'N/A')}，有效率 {stats.get('effectiveness_rate', 'N/A')}，研究数 {stats.get('studies_count', 'N/A')}，证据等级 {stats.get('evidence_level', 'N/A')}
"""
        else:
            formula_text = "  未匹配到相关方剂"

        # 药物匹配部分（含疗效统计）
        drug_text = ""
        if drugs:
            for i, d in enumerate(drugs[:5], 1):
                drug_detail = get_drug_by_id(d['id'])
                if drug_detail:
                    stats = drug_detail.get('effectiveness_stats', {})
                    drug_text += f"""
[药物{i}] {drug_detail['name']} [{d['id']}]
  性味归经：{drug_detail['properties']['nature']}，{drug_detail['properties']['taste']}，归{drug_detail['properties']['meridian']}
  禁忌：{', '.join(drug_detail['contraindications'])}
  疗效统计：总病例 {stats.get('total_cases', 'N/A')}，有效 {stats.get('effective_cases', 'N/A')}，有效率 {stats.get('effectiveness_rate', 'N/A')}，研究数 {stats.get('studies_count', 'N/A')}，证据等级 {stats.get('evidence_level', 'N/A')}，常见副作用 {stats.get('side_effects', 'N/A')}
"""
        else:
            drug_text = "  未匹配到相关药物"

        # 证型分析部分（v2.1新增）
        syndrome_text = ""
        if syndrome_analysis:
            for i, sa in enumerate(syndrome_analysis[:3], 1):
                syndrome_text += f"""
[证型{i}] {sa['name']} [{sa['id']}]
  辨证体系：{sa['system']}
  匹配度：{sa['match_score']*100:.0f}%
  严重程度：{sa['severity']}
  病机：{sa['pathogenesis']}
  治则：{sa['treatment_principle']}
  主方：{sa['main_formula']['formula_name']} [{sa['main_formula']['formula_id']}]
  关键体征：脉{sa['key_signs']['pulse']}，舌{sa['key_signs']['tongue']}
  鉴别要点：{'; '.join(sa['differentiation']) if sa.get('differentiation') else '无'}
"""
        else:
            syndrome_text = "  未识别到匹配证型"

        # 药物配伍关系部分（v2.1新增）
        relations_text = ""
        if drug_relations:
            critical = [r for r in drug_relations if '🔴' in r.get('alert', '')]
            warning = [r for r in drug_relations if '🟠' in r.get('alert', '')]
            good = [r for r in drug_relations if '🟢' in r.get('alert', '')]

            if critical:
                relations_text += "\n【严重禁忌 - 绝对不可同用】\n"
                for r in critical:
                    relations_text += f"  🔴 {r['drug_a']} + {r['drug_b']}：{r['mechanism']} [{r['type']}]\n"

            if warning:
                relations_text += "\n【配伍警告 - 慎用】\n"
                for r in warning:
                    relations_text += f"  🟠 {r['drug_a']} + {r['drug_b']}：{r['mechanism']} [{r['type']}]\n"

            if good:
                relations_text += "\n【优良配伍 - 协同增效】\n"
                for r in good:
                    relations_text += f"  🟢 {r['drug_a']} + {r['drug_b']}：{r['mechanism']} [{r['type']}]\n"
        else:
            relations_text = "  未检测到药物配伍关系"

        prompt = f"""你是小神农中医AI助手（v2.3 联网搜索优先 + 双源验证 + 批判性思维版）。请严格遵循以下推理与输出要求：

【推理原则】
1. 本次诊断遵循固定流程：症状标准化（SN-xxx 编号） → 联网搜索 → 搜索结果批判性评估 → 知识库检索佐证 → 联网数据入库决策 → 方剂/药物匹配 → 证型识别 → 禁忌检查 → AI生成。
2. 症状已映射到标准编号体系（SN-xxx），回答中引用症状时请保留编号。
3. 方剂、药物分析必须优先使用下方数据库提供的疗效统计（effectiveness_stats），不得编造病例数、有效率或证据等级；若数据库中标记为 N/A，可说明“暂无统计”。
4. 联网搜索结果已经过可信度评估，仅“已采纳”结果可作为主要参考；被知识库佐证（已佐证）的内容可信度更高，未佐证内容仅作参考。
5. 引用古籍/数据库时标注出处 [出处：《书名》·篇章] 或 [来源：方剂数据库/药物数据库]；来自联网搜索且已采纳的内容标注 [联网参考]。
6. 允许基于权威中医理论进行合理推理，但不得编造具体临床数据、病例或古籍原文。
7. 必须包含禁忌提醒、就医建议和免责声明。

【用户症状分析】
用户描述：{query}
标准化症状（编号 SN-xxx）：
{symptom_text}

【证型识别结果】
{syndrome_text}

【古籍知识库检索结果】
{references_text}

【联网搜索结果】
{web_search_text}

【联网搜索结果可信度评估】
{web_cred_text}

【知识库佐证状态】
{kb_corr_text}

【方剂数据库匹配结果（含疗效统计）】
{formula_text}

【药物数据库匹配结果（含疗效统计）】
{drug_text}

【药物配伍关系检查结果】
{relations_text}

用户问题：{query}

请基于以上资料，按以下完整结构输出（不要遗漏任何小节）。输出要求：
1. 整体采用中医传统、古朴、典雅的中文风格，避免使用网络流行语与emoji。
2. 每一小节必须展开具体、可操作的内容，不可只列标题或一两句话带过；单小节建议 3–6 条具体建议，全文总字数建议 1500 字以上。
3. 若某数据库未匹配到条目，请基于已采纳的联网搜索结果与权威中医理论进行合理推理，并明确标注为“基于联网参考推导”。
4. 引用务必标注来源：[出处：《书名》·篇章]、[来源：方剂数据库/药物数据库] 或 [联网参考]。
5. 症状请使用 SN-xxx 编号引用；药物/方剂请优先使用数据库中的疗效统计，若无统计则注明“暂无统计”。

【输出结构】

一、症状分析
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[列出识别到的症状及 SN-xxx 编号；如未识别到标准症状，说明用户主诉并分析其可能含义]

二、病因病机
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[从中医角度分析病因、病位、病性、病机转化，结合古籍与联网参考]

三、证型分析
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[列出匹配证型、辨证体系、匹配度、病机、治则、主方、鉴别要点；未匹配时基于资料推导]

四、方剂推荐
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[推荐 1–3 个最相关方剂，说明证型、症状匹配、组成、来源；无匹配时基于联网参考给出调理方向]

五、药物分析（含效果统计）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[分析相关药物的性味归经、功效、禁忌，并引用疗效统计；无统计时说明]

六、食疗建议
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[给出具体食材、食谱、烹调方法、饮食宜忌]

七、作息建议
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[给出睡眠、起居、日常作息、四季调摄建议]

八、情志调摄
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[给出情绪调节、心理调适、减压方法]

九、运动导引
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[给出运动、导引、气功、八段锦等建议]

十、穴位按摩/推拿
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[给出穴位定位、按摩/推拿手法、频次、注意事项]

十一、禁忌提醒
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[列出饮食、生活、药物配伍等禁忌]

十二、就医建议
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[说明何时需要尽快就医、建议就诊科室、需要记录的症状信息]

【免责声明】
以上内容由AI基于古籍知识库、证型数据库、方剂药物数据库和联网搜索结果，经批判性评估与双源验证后生成，仅供参考学习，不构成医疗建议。请以专业中医师面诊为准，切勿自行用药。"""

        return prompt
    
    def _format_fallback_result(self, query: str, symptoms: List[Dict], 
                                 chunks: List[RetrievedChunk], formulas: List[Dict], 
                                 drugs: List[Dict],
                                 syndrome_analysis: List[Dict] = None,
                                 drug_relations: List[Dict] = None) -> str:
        """无LLM时的结构化输出（v2.1增强版）"""
        syndrome_analysis = syndrome_analysis or []
        drug_relations = drug_relations or []
        lines = []
        
        # 症状分析
        lines.append("📋 症状分析")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for s in symptoms:
            lines.append(f"  • {s['name']} [{s['id']}]")
        lines.append("")
        
        # 证型分析（v2.1新增）
        if syndrome_analysis:
            lines.append("🔬 证型分析")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            for sa in syndrome_analysis[:3]:
                lines.append(f"  {sa['name']} [{sa['id']}] - 匹配度{sa['match_score']*100:.0f}%")
                lines.append(f"  辨证体系：{sa['system']} | 严重程度：{sa['severity']}")
                lines.append(f"  病机：{sa['pathogenesis']}")
                lines.append(f"  治则：{sa['treatment_principle']}")
                lines.append(f"  主方：{sa['main_formula']['formula_name']}")
                if sa.get('differentiation'):
                    lines.append(f"  鉴别：{'; '.join(sa['differentiation'])}")
                lines.append("")
        
        # 古籍佐证
        lines.append("📜 古籍佐证")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for chunk in chunks:
            lines.append(f"  《{chunk.source_book}》·{chunk.source_section}")
            lines.append(f"  {chunk.text[:100]}...")
            lines.append("")
        
        # 方剂推荐
        lines.append("💊 方剂推荐")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for f in formulas[:3]:
            formula_detail = get_formula_by_id(f['id'])
            if formula_detail:
                lines.append(f"  {formula_detail['name']} [{f['id']}]")
                lines.append(f"  证型：{formula_detail['syndrome']}")
                lines.append(f"  症状匹配：{', '.join(formula_detail['symptoms'])}")
                lines.append("")
        
        # 配伍关系分析（v2.1新增）
        if drug_relations:
            lines.append("🔗 配伍关系分析")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            for r in drug_relations:
                alert = r.get('alert', '')
                if '🔴' in alert:
                    lines.append(f"  🔴 禁忌：{r['drug_a']} + {r['drug_b']} [{r['type']}]")
                elif '🟠' in alert:
                    lines.append(f"  🟠 警告：{r['drug_a']} + {r['drug_b']} [{r['type']}]")
                elif '🟢' in alert:
                    lines.append(f"  🟢 协同：{r['drug_a']} + {r['drug_b']} [{r['type']}]")
                lines.append(f"    {r['mechanism']}")
            lines.append("")
        
        # 禁忌提醒
        lines.append("⚠️ 禁忌提醒")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("  以上方剂药物仅供参考，具体用药需经专业中医师辨证后确定。")
        lines.append("")
        
        # 免责声明
        lines.append("【免责声明】")
        lines.append("以上内容由AI基于古籍知识库、证型数据库和方剂药物数据库生成，仅供参考学习，不构成医疗建议。请以专业中医师面诊为准，切勿自行用药。")
        
        return "\n".join(lines)
    
    def verify_output(self, output: str, chunks: List[RetrievedChunk]) -> Tuple[bool, str]:
        """输出校验 - 宽松模式：允许基于通用知识的合理回答"""
        if not output or len(output.strip()) < 10:
            return False, "抱歉，暂无足够依据判断该问题。"

        # 如果已经包含明确来源引用，直接通过
        if re.search(r'\[出处：|【来源|【免责声明】|\[中医常识\]|\[联网参考\]', output):
            return True, output

        # 对于无明确来源但有实质内容的回答，追加通用说明后通过
        if len(output.strip()) > 30:
            return True, output + "\n\n[说明：以上内容由小神农AI基于中医知识库与通用中医理论综合分析生成，具体诊疗请以执业医师面诊为准。]"

        return False, "抱歉，暂无足够依据判断该问题。"
    
    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievedChunk]:
        """检索相关文档（语义检索 + 关键词检索混合）"""
        collection = self._get_collection()
        total_docs = collection.count()
        
        if total_docs == 0:
            return []
        
        all_chunks = []
        seen_ids = set()
        
        # 策略1: 关键词匹配
        symptom_keywords = [
            '头痛', '发热', '恶寒', '无汗', '汗出', '咳嗽', '胸闷', '腰痛', 
            '恶风', '体痛', '喘', '脉浮', '脉紧', '脉数', '脉沉', '脉细',
            '呕吐', '心烦', '口渴', '小便不利', '下利', '失眠', '多梦',
            '腹胀', '腹泻', '食欲不振', '口苦', '口干', '咽痛',
        ]
        matched_keywords = [kw for kw in symptom_keywords if kw in query]
        
        if matched_keywords:
            try:
                all_results = collection.get(include=['documents', 'metadatas'])
                for i, doc_text in enumerate(all_results['documents']):
                    doc_id = all_results['ids'][i]
                    if doc_id in seen_ids:
                        continue
                    
                    keyword_score = 0
                    for kw in matched_keywords:
                        if kw in doc_text:
                            keyword_score += 0.25
                    
                    if keyword_score > 0:
                        metadata = all_results['metadatas'][i]
                        all_chunks.append(RetrievedChunk(
                            text=doc_text,
                            source_book=metadata.get("source_book", "未知"),
                            source_section=metadata.get("source_section", "未知"),
                            original_text=metadata.get("original_text", ""),
                            score=keyword_score,
                            chunk_id=doc_id
                        ))
                        seen_ids.add(doc_id)
            except Exception as e:
                print(f"[RAG v2.0] 关键词检索出错: {e}")
        
        # 策略2: 语义检索
        query_embedding = self.embedder.encode([query])
        n_results = min(top_k * 3, max(total_docs - len(seen_ids), 1))
        
        if n_results > 0 and (total_docs - len(seen_ids)) > 0:
            vector_results = collection.query(
                query_embeddings=query_embedding,
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            if vector_results["ids"] and vector_results["ids"][0]:
                for i in range(len(vector_results["ids"][0])):
                    doc_id = vector_results["ids"][0][i]
                    if doc_id in seen_ids:
                        continue
                    
                    metadata = vector_results["metadatas"][0][i]
                    distance = vector_results["distances"][0][i]
                    score = max(0, np.exp(-distance / 2.0))
                    
                    all_chunks.append(RetrievedChunk(
                        text=vector_results["documents"][0][i],
                        source_book=metadata.get("source_book", "未知"),
                        source_section=metadata.get("source_section", "未知"),
                        original_text=metadata.get("original_text", ""),
                        score=score,
                        chunk_id=doc_id
                    ))
                    seen_ids.add(doc_id)
        
        all_chunks.sort(key=lambda x: x.score, reverse=True)
        return all_chunks[:top_k]
    
    def diagnose(self, query: str, llm_client=None) -> DiagnosisResult:
        """兼容旧接口"""
        return self.diagnose_with_thinking(query, llm_client)
    
    def _extract_constitution(self, text: str) -> str:
        """提取体质类型"""
        constitutions = [
            "平和质", "气虚质", "阳虚质", "阴虚质", "痰湿质", "湿热质", 
            "血瘀质", "气郁质", "特禀质",
            "风寒表实证", "风寒表虚证", "风热证", "湿热证", "少阳证",
            "阳明经证", "太阴病", "少阴病", "厥阴病",
        ]
        for c in constitutions:
            if c in text:
                return c
        return "待辨识"
    
    def _extract_syndrome(self, text: str) -> str:
        """提取证候"""
        patterns = ["证", "症", "病"]
        for p in patterns:
            if p in text:
                sentences = text.split("。")
                for s in sentences:
                    if p in s and len(s) < 50:
                        return s.strip()
        return "详见调理建议"
    
    def get_stats(self) -> Dict:
        """获取知识库统计"""
        try:
            collection = self._get_collection()
            count = collection.count()
        except Exception:
            count = 0
        return {
            "total_documents": count,
            "embedding_model": self.embedder.model_name if hasattr(self.embedder, 'model_name') else "simple",
            "device": self.device,
            "symptom_count": len(SYMPTOM_MAP),
            "drug_count": len(DRUG_DATABASE),
            "formula_count": len(FORMULA_DATABASE),
        }


if __name__ == "__main__":
    # 测试
    rag = XiaoShennongRAGv2()
    
    test_docs = [
        {
            "text": "太阳之为病，脉浮，头项强痛而恶寒。",
            "metadata": {
                "source_book": "伤寒论",
                "source_section": "太阳病篇第一条",
                "original_text": "太阳之为病，脉浮，头项强痛而恶寒。",
                "chunk_id": "shl_001"
            }
        },
        {
            "text": "太阳病，头痛发热，身疼腰痛，骨节疼痛，恶风无汗而喘者，麻黄汤主之。",
            "metadata": {
                "source_book": "伤寒论",
                "source_section": "第35条",
                "original_text": "太阳病，头痛发热，身疼腰痛，骨节疼痛，恶风无汗而喘者，麻黄汤主之。",
                "chunk_id": "shl_035"
            }
        }
    ]
    
    rag.add_documents(test_docs)
    
    result = rag.diagnose_with_thinking("我最近头痛发热，怕冷，没有汗，应该怎么办？")
    print("\n=== 辨证结果 ===")
    print(f"体质：{result.constitution}")
    print(f"证候：{result.syndrome}")
    print(f"建议：{result.advice[:200]}...")
    print(f"溯源：{len(result.sources)}条")
    print(f"匹配方剂：{len(result.matched_formulas)}个")
    print(f"匹配药物：{len(result.matched_drugs)}个")
    print(f"禁忌提醒：{len(result.contraindications)}条")
    print(f"\n=== 思考过程 ===")
    for step in result.thinking_process:
        print(f"步骤{step['step']}: {step['name']} ({step['time_ms']}ms) - {step['status']}")
    print(f"\n总耗时：{result.total_time_ms}ms")
    print(f"\n{result.warning}")
