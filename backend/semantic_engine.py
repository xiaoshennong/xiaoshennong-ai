#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小神农语义匹配引擎 v1.0
基于Sentence-BERT的中文语义相似度搜索
支持：症状语义匹配、方剂语义匹配、跨模态检索
"""

import json
import os
import re
import numpy as np
from typing import List, Dict, Tuple, Optional

# 尝试加载sentence-transformers，如果不可用则使用fallback
HAS_EMBEDDING = False
embedding_model = None

# 尝试加载嵌入模型
try:
    from sentence_transformers import SentenceTransformer
    embedding_model = SentenceTransformer('shibing624/text2vec-base-chinese')
    HAS_EMBEDDING = True
    print(f"[SemanticEngine] 嵌入模型加载成功: text2vec-base-chinese")
except Exception as e:
    print(f"[SemanticEngine] 嵌入模型加载失败: {e}")
    print(f"[SemanticEngine] 将使用关键词fallback模式")


class SemanticMatcher:
    """语义匹配引擎 - 支持向量检索和关键词混合搜索"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.join(os.path.dirname(__file__), '..', 'data')
        self.embeddings = {}  # id -> vector
        self.texts = {}       # id -> text
        self.metadata = {}    # id -> metadata dict
        self.index_built = False
        
        # 中医同义词词典（用于关键词fallback）
        self.tcm_synonyms = {
            '失眠': ['不寐', '不得眠', '夜不能寐', '睡眠障碍', '入睡困难', '易醒', '早醒'],
            '头痛': ['头疼', '头胀痛', '偏头痛', '巅顶痛', '头重'],
            '胃痛': ['胃脘痛', '心下痛', '胃疼', '脘腹疼痛'],
            '腹泻': ['泄泻', '便溏', '拉肚子', '拉稀', '大便稀溏', '下利'],
            '便秘': ['大便不通', '便结', '排便困难', '大便干', '拉不出'],
            '咳嗽': ['咳', '干咳', '痰咳', '咳喘', '咳痰'],
            '发热': ['发烧', '身热', '潮热', '低热', '高热', '微热'],
            '乏力': ['没力气', '疲倦', '疲劳', '倦怠', '神疲', '没精神', '四肢无力'],
            '心悸': ['心慌', '心跳快', '心动悸', '心中悸动'],
            '胸闷': ['胸痞', '胸中痞闷', '胸口闷', '胸满'],
            '腰痛': ['腰酸', '腰背痛', '腰脊痛', '腰困'],
            '关节痛': ['痹痛', '关节疼痛', '骨节痛', '屈伸不利'],
            '月经不调': ['月经不准', '月经不规律', '经行先期', '经行后期', '经乱'],
            '痛经': ['经行腹痛', '来月经疼', '经痛', '经期腹痛'],
            '咽喉痛': ['咽痛', '喉痛', '嗓子疼', '喉咙痛', '咽喉肿痛'],
            '口苦': ['口苦干', '口中苦', '上火'],
            '恶心': ['呕吐', '想吐', '反胃', '干呕', '哕'],
            '食欲不振': ['吃不下', '没胃口', '不欲食', '纳呆', '食少', '吃饭不香'],
            '皮肤瘙痒': ['皮肤痒', '身痒', '痒疹', '风疹'],
            '水肿': ['浮肿', '肿胀', '水气', '水湿'],
            '眩晕': ['头晕', '头昏', '头眩', '眼花', '目眩'],
            '出汗': ['自汗', '盗汗', '多汗', '汗出', '冒汗'],
            '口干': ['口渴', '咽干', '舌燥', '口干咽燥'],
            '腹胀': ['脘腹胀满', '腹满', '肚子胀', '胀满'],
            '遗精': ['滑精', '梦遗', '精关不固'],
            '阳痿': ['阳事不举', '勃起障碍', '性功能减退'],
            '带下': ['白带', '带下病', '带下过多', '带下异常'],
            '不孕': ['不育', '无子', '断绪'],
            '消渴': ['糖尿病', '多饮多尿', '口渴多饮'],
        }
        
        # 反向映射：同义词 -> 标准词
        self.alias_to_standard = {}
        for std, aliases in self.tcm_synonyms.items():
            for alias in aliases:
                self.alias_to_standard[alias] = std
            self.alias_to_standard[std] = std
    
    def build_index(self, items: List[Dict], id_field: str = 'id', 
                    text_fields: List[str] = None, metadata_fields: List[str] = None):
        """
        构建语义索引
        items: 数据列表
        id_field: ID字段名
        text_fields: 用于生成嵌入的文本字段
        metadata_fields: 需要保留的元数据字段
        """
        if not HAS_EMBEDDING:
            # 无嵌入模型时，只构建关键词索引
            for item in items:
                item_id = item.get(id_field, '')
                if not item_id:
                    continue
                
                # 合并文本
                texts = []
                if text_fields:
                    for field in text_fields:
                        val = item.get(field, '')
                        if val:
                            if isinstance(val, list):
                                texts.extend([str(v) for v in val])
                            else:
                                texts.append(str(val))
                
                self.texts[item_id] = ' '.join(texts)
                
                # 保存元数据
                if metadata_fields:
                    self.metadata[item_id] = {k: item.get(k) for k in metadata_fields}
                else:
                    self.metadata[item_id] = item
            
            self.index_built = True
            print(f"[SemanticMatcher] 关键词索引构建完成: {len(self.texts)} 条")
            return
        
        # 有嵌入模型时，构建向量索引
        texts_to_embed = []
        ids = []
        
        for item in items:
            item_id = item.get(id_field, '')
            if not item_id:
                continue
            
            # 合并文本
            texts = []
            if text_fields:
                for field in text_fields:
                    val = item.get(field, '')
                    if val:
                        if isinstance(val, list):
                            texts.extend([str(v) for v in val])
                        else:
                            texts.append(str(val))
            
            full_text = ' '.join(texts)
            if not full_text.strip():
                continue
            
            self.texts[item_id] = full_text
            texts_to_embed.append(full_text)
            ids.append(item_id)
            
            # 保存元数据
            if metadata_fields:
                self.metadata[item_id] = {k: item.get(k) for k in metadata_fields}
            else:
                self.metadata[item_id] = item
        
        if texts_to_embed:
            print(f"[SemanticMatcher] 正在编码 {len(texts_to_embed)} 条数据...")
            vectors = embedding_model.encode(texts_to_embed, show_progress_bar=True)
            
            for i, item_id in enumerate(ids):
                self.embeddings[item_id] = vectors[i]
            
            self.index_built = True
            print(f"[SemanticMatcher] 向量索引构建完成: {len(self.embeddings)} 条, 维度 {vectors.shape[1]}")
    
    def semantic_search(self, query: str, top_k: int = 10, 
                        min_score: float = 0.3) -> List[Dict]:
        """
        语义搜索 - 返回最相似的结果
        """
        if not self.index_built:
            return []
        
        results = []
        
        if HAS_EMBEDDING and self.embeddings:
            # 向量搜索
            query_vec = embedding_model.encode([query])[0]
            
            for item_id, vec in self.embeddings.items():
                # 余弦相似度
                score = self._cosine_similarity(query_vec, vec)
                if score >= min_score:
                    results.append({
                        'id': item_id,
                        'score': float(score),
                        'text': self.texts.get(item_id, '')[:200],
                        'metadata': self.metadata.get(item_id, {})
                    })
            
            # 按分数排序
            results.sort(key=lambda x: x['score'], reverse=True)
            results = results[:top_k]
        
        # 补充关键词搜索（fallback或混合）
        keyword_results = self._keyword_search(query, top_k=top_k)
        
        # 合并结果，去重，按分数排序
        seen = {r['id'] for r in results}
        for kr in keyword_results:
            if kr['id'] not in seen:
                # 降低关键词搜索分数权重
                kr['score'] *= 0.7
                results.append(kr)
                seen.add(kr['id'])
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def _keyword_search(self, query: str, top_k: int = 10) -> List[Dict]:
        """关键词搜索 - 作为fallback"""
        results = []
        query_lower = query.lower()
        
        # 扩展查询词（同义词）
        expanded_terms = [query_lower]
        for alias, std in self.alias_to_standard.items():
            if alias in query_lower or std in query_lower:
                expanded_terms.extend([alias, std])
                # 添加该标准词的所有同义词
                if std in self.tcm_synonyms:
                    expanded_terms.extend(self.tcm_synonyms[std])
        
        expanded_terms = list(set(expanded_terms))
        
        for item_id, text in self.texts.items():
            text_lower = text.lower()
            score = 0
            matched_terms = []
            
            for term in expanded_terms:
                if term in text_lower:
                    score += 1
                    matched_terms.append(term)
            
            if score > 0:
                # 归一化分数
                normalized_score = min(score / len(expanded_terms), 1.0)
                results.append({
                    'id': item_id,
                    'score': float(normalized_score),
                    'text': text[:200],
                    'metadata': self.metadata.get(item_id, {}),
                    'matched_terms': matched_terms
                })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """计算余弦相似度"""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return np.dot(a, b) / (norm_a * norm_b)
    
    def expand_query(self, query: str) -> List[str]:
        """扩展查询词，包含同义词"""
        expanded = [query]
        
        # 检查查询中的每个词
        for alias, std in self.alias_to_standard.items():
            if alias in query or std in query:
                if std in self.tcm_synonyms:
                    expanded.extend(self.tcm_synonyms[std])
                expanded.append(std)
        
        return list(set(expanded))


class XiaoShennongSemanticEngine:
    """小神农语义搜索总引擎 - 管理多个索引"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.join(os.path.dirname(__file__), '..', 'data')
        
        # 各类型数据的语义匹配器
        self.symptom_matcher = SemanticMatcher(self.data_dir)
        self.drug_matcher = SemanticMatcher(self.data_dir)
        self.formula_matcher = SemanticMatcher(self.data_dir)
        self.acupoint_matcher = SemanticMatcher(self.data_dir)
        self.dietary_matcher = SemanticMatcher(self.data_dir)
        
        self.initialized = False
    
    def initialize(self, symptom_data=None, drug_data=None, formula_data=None, 
                   acupoint_data=None, dietary_data=None):
        """初始化所有索引"""
        print("[SemanticEngine] 开始构建语义索引...")
        
        # 症状索引
        if symptom_data:
            symptoms = symptom_data.get('symptoms', [])
            self.symptom_matcher.build_index(
                symptoms,
                id_field='id',
                text_fields=['name', 'aliases', 'common_syndromes', 'description'],
                metadata_fields=['id', 'name', 'pinyin', 'part', 'category', 'aliases', 'common_syndromes']
            )
        
        # 药物索引
        if drug_data:
            drugs = drug_data.get('drugs', [])
            self.drug_matcher.build_index(
                drugs,
                id_field='id',
                text_fields=['name', 'properties', 'functions', 'indications', 'meridian'],
                metadata_fields=['id', 'name', 'properties', 'functions', 'meridian']
            )
        
        # 方剂索引
        if formula_data:
            formulas = formula_data.get('formulas', [])
            self.formula_matcher.build_index(
                formulas,
                id_field='id',
                text_fields=['name', 'functions', 'indications', 'source', 'category'],
                metadata_fields=['id', 'name', 'functions', 'source', 'category']
            )
        
        # 穴位索引
        if acupoint_data:
            acupoints = acupoint_data.get('acupoints', [])
            self.acupoint_matcher.build_index(
                acupoints,
                id_field='id',
                text_fields=['name', 'location', 'indications', 'method', 'meridian'],
                metadata_fields=['id', 'name', 'location', 'meridian', 'indications']
            )
        
        # 食疗索引
        if dietary_data:
            dietary = dietary_data.get('dietary_therapies', [])
            self.dietary_matcher.build_index(
                dietary,
                id_field='id',
                text_fields=['name', 'indications', 'ingredients', 'method', 'contraindications'],
                metadata_fields=['id', 'name', 'indications', 'ingredients']
            )
        
        self.initialized = True
        print("[SemanticEngine] 语义索引构建完成!")
    
    def search_symptoms(self, query: str, top_k: int = 10) -> List[Dict]:
        """语义搜索症状"""
        return self.symptom_matcher.semantic_search(query, top_k=top_k, min_score=0.2)
    
    def search_drugs(self, query: str, top_k: int = 10) -> List[Dict]:
        """语义搜索药物"""
        return self.drug_matcher.semantic_search(query, top_k=top_k, min_score=0.2)
    
    def search_formulas(self, query: str, top_k: int = 10) -> List[Dict]:
        """语义搜索方剂"""
        return self.formula_matcher.semantic_search(query, top_k=top_k, min_score=0.2)
    
    def search_acupoints(self, query: str, top_k: int = 10) -> List[Dict]:
        """语义搜索穴位"""
        return self.acupoint_matcher.semantic_search(query, top_k=top_k, min_score=0.2)
    
    def search_dietary(self, query: str, top_k: int = 10) -> List[Dict]:
        """语义搜索食疗"""
        return self.dietary_matcher.semantic_search(query, top_k=top_k, min_score=0.2)
    
    def cross_search(self, query: str, top_k: int = 5) -> Dict[str, List[Dict]]:
        """跨类型综合语义搜索"""
        return {
            'symptoms': self.search_symptoms(query, top_k),
            'drugs': self.search_drugs(query, top_k),
            'formulas': self.search_formulas(query, top_k),
            'acupoints': self.search_acupoints(query, top_k),
            'dietary': self.search_dietary(query, top_k)
        }


# 单例模式
_semantic_engine = None

def get_semantic_engine():
    """获取语义引擎单例"""
    global _semantic_engine
    if _semantic_engine is None:
        _semantic_engine = XiaoShennongSemanticEngine()
    return _semantic_engine


if __name__ == '__main__':
    # 测试
    engine = XiaoShennongSemanticEngine()
    
    # 模拟数据
    test_symptoms = [
        {'id': 'SN-001-001-001', 'name': '不寐', 'aliases': ['失眠', '不得眠'], 
         'common_syndromes': ['心脾两虚', '阴虚火旺'], 'description': '睡眠障碍'},
        {'id': 'SN-001-001-002', 'name': '头痛', 'aliases': ['头疼'], 
         'common_syndromes': ['风寒头痛', '风热头痛'], 'description': '头部疼痛'},
    ]
    
    engine.initialize(
        symptom_data={'symptoms': test_symptoms}
    )
    
    results = engine.search_symptoms("睡不着", top_k=5)
    print("\n搜索结果:")
    for r in results:
        print(f"  {r['id']} {r['metadata'].get('name', '')} score={r['score']:.3f}")
