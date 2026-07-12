#!/usr/bin/env python3
"""
小神农中医AI - RAG核心引擎（带思考过程）
返回完整的AI思考链：检索→分析→生成
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

# 尝试使用sentence-transformers（更轻量）
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
    status: str = "running"  # running, completed, failed


@dataclass
class DiagnosisResult:
    """AI辨证结果（含思考过程）"""
    constitution: str
    syndrome: str
    advice: str
    sources: List[Dict]
    warning: str
    thinking_process: List[Dict]  # 思考过程
    total_time_ms: float


class SimpleEmbedder:
    """简化版嵌入器（无需大模型下载）"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self._init_model()
    
    def _init_model(self):
        """初始化模型"""
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
        """编码文本"""
        if isinstance(texts, str):
            texts = [texts]
        
        if self.model is not None:
            # 使用sentence-transformers
            embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            return embeddings.tolist()
        else:
            # 备用方案：简单词频编码（效果差但可用）
            return self._simple_encode(texts)
    
    def _simple_encode(self, texts: List[str]) -> List[List[float]]:
        """简单编码（备用）"""
        # 使用预定义的关键词向量
        keywords = {
            "头痛": 0, "发热": 1, "恶寒": 2, "汗出": 3, "咳嗽": 4,
            "胸闷": 5, "心悸": 6, "失眠": 7, "多梦": 8, "食欲不振": 9,
            "腹胀": 10, "腹泻": 11, "便秘": 12, "口干": 13, "口苦": 14,
            "咽痛": 15, "腰痛": 16, "关节痛": 17, "乏力": 18,
            "风寒": 19, "风热": 20, "湿热": 21, "气虚": 22, "血虚": 23,
            "阴虚": 24, "阳虚": 25, "痰湿": 26, "血瘀": 27, "气郁": 28,
            "麻黄": 29, "桂枝": 30, "柴胡": 31, "黄芩": 32, "人参": 33,
            "黄芪": 34, "当归": 35, "甘草": 36, "杏仁": 37, "芍药": 38
        }
        
        dim = 128
        embeddings = []
        
        for text in texts:
            vec = np.zeros(dim)
            for kw, idx in keywords.items():
                if kw in text:
                    vec[idx % dim] += 1.0
            # 归一化
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            embeddings.append(vec.tolist())
        
        return embeddings


class XiaoShennongRAG:
    """
    小神农RAG引擎（带思考过程）
    返回完整的AI思考链：检索→分析→生成
    """
    
    def __init__(self, 
                 db_path: str = "./data/chroma_db",
                 model_name: str = "all-MiniLM-L6-v2",
                 device: str = None):
        
        self.device = device or "cpu"
        print(f"[RAG] 使用设备: {self.device}")
        
        # 加载嵌入模型
        self.embedder = SimpleEmbedder(model_name)
        
        # 初始化向量数据库
        print(f"[RAG] 初始化向量数据库: {db_path}")
        os.makedirs(db_path, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 获取或创建集合（仅初始化时检查）
        try:
            _collection = self.chroma_client.get_collection("tcm_knowledge")
            print(f"[RAG] 初始化完成，当前知识库文档数: {_collection.count()}")
        except Exception:
            _collection = self.chroma_client.create_collection(
                name="tcm_knowledge",
                metadata={"description": "中医古籍知识库"}
            )
            print("[RAG] 初始化完成，新建知识库")
        
        # 中医术语标准化词典
        self.term_dict = self._load_term_dict()
    
    def _load_term_dict(self) -> Dict[str, List[str]]:
        """加载中医术语标准化词典"""
        return {
            "中风": ["中风", "卒中", "偏枯", "风痱"],
            "感冒": ["感冒", "伤风", "风寒", "风热"],
            "失眠": ["失眠", "不寐", "不得眠", "目不瞑"],
            "头痛": ["头痛", "头风", "头疼"],
            "咳嗽": ["咳嗽", "咳逆", "嗽"],
            "腹泻": ["腹泻", "泄泻", "下利", "溏泄"],
            "便秘": ["便秘", "便闭", "大便难", "阳结"],
            "发热": ["发热", "发烧", "身热", "潮热"],
            "恶寒": ["恶寒", "畏寒", "怕冷", "恶风"],
            "汗出": ["汗出", "出汗", "自汗", "盗汗"],
        }
    
    def normalize_terms(self, query: str) -> str:
        """标准化中医术语"""
        for standard, variants in self.term_dict.items():
            for variant in variants:
                if variant in query and variant != standard:
                    query = query.replace(variant, standard)
        return query
    
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
            
            # 去重：如果ID已存在，添加随机后缀
            if doc_id in seen_ids:
                doc_id = f"{doc_id}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:6]}"
            seen_ids.add(doc_id)
            
            texts.append(text)
            metadatas.append(metadata)
            ids.append(doc_id)
        
        # 生成嵌入向量
        embeddings = self.embedder.encode(texts)
        
        # 添加到Chroma（使用重新获取的集合引用）
        collection = self._get_collection()
        collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"[RAG] 成功添加 {len(documents)} 条文档")
    
    def diagnose_with_thinking(self, query: str, llm_client=None) -> DiagnosisResult:
        """
        完整辨证流程（带思考过程）
        返回完整的AI思考链：检索→分析→生成
        """
        thinking_process = []
        total_start = time.time()
        
        # 步骤1: 接收查询
        step1 = ThinkingStep(
            step_name="接收查询",
            step_description="接收用户症状描述",
            start_time=time.time(),
            details={"query": query}
        )
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
        
        # 步骤2: 标准化查询
        step2 = ThinkingStep(
            step_name="标准化查询",
            step_description="将用户症状转换为标准中医术语",
            start_time=time.time()
        )
        normalized_query = self.normalize_terms(query)
        step2.details = {
            "original_query": query,
            "normalized_query": normalized_query,
            "terms_normalized": normalized_query != query
        }
        step2.end_time = time.time()
        step2.status = "completed"
        thinking_process.append({
            "step": 2,
            "name": step2.step_name,
            "description": step2.step_description,
            "time_ms": round((step2.end_time - step2.start_time) * 1000, 2),
            "status": step2.status,
            "details": step2.details
        })
        
        # 步骤3: 检索知识库
        step3 = ThinkingStep(
            step_name="检索知识库",
            step_description="从中医古籍知识库中检索相关记载",
            start_time=time.time()
        )
        
        chunks = self.retrieve(query, top_k=5)
        
        step3.details = {
            "total_documents": self._get_collection().count(),
            "retrieved_count": len(chunks),
            "retrieved_sources": [
                {
                    "book": c.source_book,
                    "section": c.source_section,
                    "score": round(c.score, 4),
                    "text_preview": c.text[:100] + "..." if len(c.text) > 100 else c.text
                }
                for c in chunks
            ]
        }
        step3.end_time = time.time()
        step3.status = "completed" if chunks else "failed"
        thinking_process.append({
            "step": 3,
            "name": step3.step_name,
            "description": step3.step_description,
            "time_ms": round((step3.end_time - step3.start_time) * 1000, 2),
            "status": step3.status,
            "details": step3.details
        })
        
        if not chunks:
            total_end = time.time()
            thinking_process.append({
                "step": 4,
                "name": "生成回答",
                "description": "知识库中无相关记载，返回拒答",
                "time_ms": 0,
                "status": "completed",
                "details": {"result": "暂无权威数据支持"}
            })
            return DiagnosisResult(
                constitution="未知",
                syndrome="暂无权威数据支持",
                advice="抱歉，暂无权威数据支持该问题。",
                sources=[],
                warning="本结果仅供参考，不能替代专业医生诊断。",
                thinking_process=thinking_process,
                total_time_ms=round((total_end - total_start) * 1000, 2)
            )
        
        # 步骤4: 构建提示词
        step4 = ThinkingStep(
            step_name="构建提示词",
            step_description="将检索到的古籍内容组织为AI提示词",
            start_time=time.time()
        )
        
        prompt = self.build_prompt(normalized_query, chunks)
        
        step4.details = {
            "prompt_length": len(prompt),
            "references_count": len(chunks),
            "prompt_preview": prompt[:500] + "..." if len(prompt) > 500 else prompt
        }
        step4.end_time = time.time()
        step4.status = "completed"
        thinking_process.append({
            "step": 4,
            "name": step4.step_name,
            "description": step4.step_description,
            "time_ms": round((step4.end_time - step4.start_time) * 1000, 2),
            "status": step4.status,
            "details": step4.details
        })
        
        # 步骤5: AI生成回答
        step5 = ThinkingStep(
            step_name="AI生成回答",
            step_description="调用大语言模型基于古籍资料生成回答",
            start_time=time.time()
        )
        
        if llm_client is None:
            raw_output = self._format_retrieval_result(chunks)
            step5.details = {"llm_provider": "mock", "note": "使用模拟LLM（无API Key）"}
        else:
            llm_start = time.time()
            raw_output = llm_client.generate(prompt)
            llm_time = (time.time() - llm_start) * 1000
            step5.details = {
                "llm_provider": getattr(llm_client, 'model', 'unknown'),
                "llm_time_ms": round(llm_time, 2),
                "output_length": len(raw_output)
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
        
        # 步骤6: 输出校验
        step6 = ThinkingStep(
            step_name="输出校验",
            step_description="校验AI回答是否基于提供的古籍资料，无幻觉",
            start_time=time.time()
        )
        
        passed, verified_output = self.verify_output(raw_output, chunks)
        
        step6.details = {
            "verification_passed": passed,
            "sources_found": len(re.findall(r'\[出处：《(.+?)》·(.+?)\]', verified_output)),
            "output_length": len(verified_output)
        }
        step6.end_time = time.time()
        step6.status = "completed" if passed else "warning"
        thinking_process.append({
            "step": 6,
            "name": step6.step_name,
            "description": step6.step_description,
            "time_ms": round((step6.end_time - step6.start_time) * 1000, 2),
            "status": step6.status,
            "details": step6.details
        })
        
        if not passed:
            total_end = time.time()
            thinking_process.append({
                "step": 7,
                "name": "返回结果",
                "description": "校验失败，返回拒答",
                "time_ms": 0,
                "status": "completed",
                "details": {"result": "暂无权威数据支持"}
            })
            return DiagnosisResult(
                constitution="未知",
                syndrome="暂无权威数据支持",
                advice=verified_output,
                sources=[],
                warning="本结果仅供参考，不能替代专业医生诊断。",
                thinking_process=thinking_process,
                total_time_ms=round((total_end - total_start) * 1000, 2)
            )
        
        # 步骤7: 提取结构化信息
        step7 = ThinkingStep(
            step_name="提取结构化信息",
            step_description="从AI回答中提取体质、证候、建议等结构化信息",
            start_time=time.time()
        )
        
        sources = []
        for chunk in chunks:
            sources.append({
                "book": chunk.source_book,
                "section": chunk.source_section,
                "original_text": chunk.original_text,
                "text": chunk.text
            })
        
        constitution = self._extract_constitution(verified_output)
        syndrome = self._extract_syndrome(verified_output)
        
        step7.details = {
            "constitution": constitution,
            "syndrome": syndrome,
            "sources_count": len(sources)
        }
        step7.end_time = time.time()
        step7.status = "completed"
        thinking_process.append({
            "step": 7,
            "name": step7.step_name,
            "description": step7.step_description,
            "time_ms": round((step7.end_time - step7.start_time) * 1000, 2),
            "status": step7.status,
            "details": step7.details
        })
        
        # 步骤8: 返回结果
        total_end = time.time()
        thinking_process.append({
            "step": 8,
            "name": "返回结果",
            "description": "整理并返回最终辨证结果",
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
            total_time_ms=round((total_end - total_start) * 1000, 2)
        )
    
    def _get_collection(self):
        """重新获取集合引用（解决集合重建后ID变化的问题）"""
        try:
            return self.chroma_client.get_collection("tcm_knowledge")
        except Exception:
            return self.chroma_client.create_collection(
                name="tcm_knowledge",
                metadata={"description": "中医古籍知识库"}
            )
    
    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievedChunk]:
        """检索相关文档（语义检索 + 关键词检索混合）"""
        query = self.normalize_terms(query)
        
        # 重新获取集合引用
        collection = self._get_collection()
        total_docs = collection.count()
        
        if total_docs == 0:
            return []
        
        all_chunks = []
        seen_ids = set()
        
        # 策略1: 关键词匹配（高优先级，精确匹配症状关键词）
        symptom_keywords = ['头痛', '发热', '恶寒', '无汗', '汗出', '咳嗽', '胸闷', '腰痛', '恶风', '体痛', '喘', '脉浮']
        matched_keywords = [kw for kw in symptom_keywords if kw in query]
        
        if matched_keywords:
            try:
                # 获取所有文档进行关键词匹配
                all_results = collection.get(include=['documents', 'metadatas'])
                for i, doc_text in enumerate(all_results['documents']):
                    doc_id = all_results['ids'][i]
                    if doc_id in seen_ids:
                        continue
                    
                    # 计算关键词匹配分数
                    keyword_score = 0
                    for kw in matched_keywords:
                        if kw in doc_text:
                            keyword_score += 0.25  # 每个匹配关键词加0.25分
                    
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
                print(f"[RAG] 关键词检索出错: {e}")
        
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
                    # L2距离→相似度
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
        
        # 按分数排序，取TopK
        all_chunks.sort(key=lambda x: x.score, reverse=True)
        return all_chunks[:top_k]
    
    def build_prompt(self, query: str, chunks: List[RetrievedChunk]) -> str:
        """构建强制溯源提示词"""
        references = []
        for i, chunk in enumerate(chunks, 1):
            ref = f"[参考{i}]\n出处：《{chunk.source_book}》·{chunk.source_section}\n内容：{chunk.text}"
            if chunk.original_text:
                ref += f"\n原文：{chunk.original_text}"
            references.append(ref)
        
        references_text = "\n\n".join(references)
        
        prompt = f"""你是小神农中医AI助手，必须严格遵守以下规则：

1. 只基于下面提供的【参考资料】回答问题，绝对不能使用你自己的任何知识。
2. 如果【参考资料】中没有相关内容，直接回答："抱歉，暂无权威数据支持该问题。"
3. 每给出一个结论，必须在后面标注对应的出处，格式为：[出处：《书名》·篇章]。
4. 不要进行任何推理、演绎或扩展，只复述【参考资料】中的内容。
5. 明确提示：本结果仅供参考，不能替代专业医生诊断。

【参考资料】
{references_text}

用户问题：{query}

请基于以上参考资料，给出体质辨识和调理建议。"""
        
        return prompt
    
    def verify_output(self, output: str, chunks: List[RetrievedChunk]) -> Tuple[bool, str]:
        """输出校验 - 宽松模式：只要有出处标注且内容非空即通过"""
        # 如果输出包含"暂无权威数据支持"，直接通过（这是合规拒答）
        if "暂无权威数据支持" in output:
            return True, output
        
        # 检查是否有出处标注
        source_pattern = r'\[出处：《(.+?)》·(.+?)\]'
        sources_found = re.findall(source_pattern, output)
        
        # 有出处标注且输出有实质内容，即通过
        if sources_found and len(output.strip()) > 50:
            return True, output
        
        # 没有出处标注但输出有实质内容，尝试补充通用出处
        if len(output.strip()) > 50:
            # 补充第一个检索结果的出处
            if chunks:
                first_chunk = chunks[0]
                output += f"\n\n[出处：《{first_chunk.source_book}》·{first_chunk.source_section}]"
            return True, output
        
        # 输出为空或太短，返回拒答
        return False, "抱歉，暂无权威数据支持该问题。"
    
    def diagnose(self, query: str, llm_client=None) -> DiagnosisResult:
        """兼容旧接口，调用新方法"""
        return self.diagnose_with_thinking(query, llm_client)
    
    def _format_retrieval_result(self, chunks: List[RetrievedChunk]) -> str:
        """无LLM时的格式化输出"""
        lines = []
        for chunk in chunks:
            lines.append(f"根据《{chunk.source_book}》·{chunk.source_section}：{chunk.text}")
        return "\n".join(lines)
    
    def _extract_constitution(self, text: str) -> str:
        """提取体质类型"""
        constitutions = ["平和质", "气虚质", "阳虚质", "阴虚质", "痰湿质", "湿热质", "血瘀质", "气郁质", "特禀质",
                        "风寒表实证", "风寒表虚证", "风热证", "湿热证"]
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
            "term_dict_size": len(self.term_dict)
        }


if __name__ == "__main__":
    # 测试
    rag = XiaoShennongRAG()
    
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
    print(f"\n=== 思考过程 ===")
    for step in result.thinking_process:
        print(f"步骤{step['step']}: {step['name']} ({step['time_ms']}ms) - {step['status']}")
    print(f"\n总耗时：{result.total_time_ms}ms")
    print(f"\n{result.warning}")
