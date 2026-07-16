#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小神农 Agent 技能系统 v1.0
多Agent协作架构：症状Agent、药物Agent、方剂Agent、副作用Agent、患者Agent、共现Agent、聚类Agent
每个Agent具备思考能力和联网搜索能力（通过外部API）
"""

import json
import os
import re
import random
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# 导入联网搜索模块
try:
    from web_search_agent import get_web_search_agent, WebSearchAgent
    HAS_WEBSEARCH = True
except ImportError:
    HAS_WEBSEARCH = False
    print("[AgentSystem] 联网搜索模块未加载")


# ========== 基础Agent类 ==========

class BaseAgent:
    """所有Agent的基类 - 具备联网搜索能力"""
    
    def __init__(self, name: str, agent_id: str, data_dir: str = None):
        self.name = name
        self.agent_id = agent_id
        self.data_dir = data_dir or os.path.join(os.path.dirname(__file__), '..', 'data')
        self.thought_log = []  # 思考日志
        self.knowledge_cache = {}  # 知识缓存
        self.web_search = None  # 联网搜索实例
        self._init_web_search()
    
    def _init_web_search(self):
        """初始化联网搜索能力"""
        if HAS_WEBSEARCH:
            self.web_search = get_web_search_agent()
            if self.web_search.is_available():
                self.think('初始化', '联网搜索能力已启用', ['WebSearchAgent已配置'])
            else:
                self.think('初始化', '联网搜索能力未启用（未配置API密钥）', ['请设置 YUNWU_API_KEY 环境变量'])
        else:
            self.think('初始化', '联网搜索模块未加载', ['web_search_agent.py未找到'])
    
    def think(self, step: str, reasoning: str, evidence: List[str] = None):
        """记录思考过程"""
        thought = {
            'agent': self.name,
            'step': step,
            'reasoning': reasoning,
            'evidence': evidence or [],
            'timestamp': datetime.now().isoformat()
        }
        self.thought_log.append(thought)
        return thought
    
    def get_thoughts(self) -> List[Dict]:
        """获取完整思考链"""
        return self.thought_log
    
    def clear_thoughts(self):
        """清空思考日志"""
        self.thought_log = []
    
    def search_web(self, query: str, context: str = None) -> List[Dict]:
        """
        联网搜索接口 - 调用WebSearchAgent进行真实搜索
        
        Args:
            query: 搜索查询词
            context: 搜索上下文（如"中医临床"、"中药研究"等）
        
        Returns:
            搜索结果列表
        """
        if self.web_search and self.web_search.is_available():
            self.think('联网搜索', f'执行搜索: {query}', [f'上下文: {context or "通用"}'])
            results = self.web_search.search(query, context=context)
            self.think('搜索完成', f'获得 {len(results)} 条结果', [r.get('title', '') for r in results[:3]])
            return results
        else:
            self.think('联网搜索', '搜索不可用，使用本地知识库', ['API未配置'])
            return self._mock_web_search(query)
    
    def verify_with_web(self, claim: str) -> Dict:
        """
        联网验证 - 验证某个论断的真实性
        
        Args:
            claim: 需要验证的论断
        
        Returns:
            验证结果
        """
        if self.web_search and self.web_search.is_available():
            self.think('联网验证', f'验证论断: {claim}')
            result = self.web_search.verify_fact(claim)
            self.think('验证完成', f"结果: {result['status']}, 置信度: {result['confidence']}")
            return result
        else:
            return {
                'claim': claim,
                'status': 'unverified',
                'confidence': 0.0,
                'reason': '联网搜索未启用'
            }
    
    def _mock_web_search(self, query: str) -> List[Dict]:
        """模拟联网搜索 - 当真实搜索不可用时使用"""
        return []
    
    def validate_data(self, data: Dict, schema: Dict) -> Tuple[bool, List[str]]:
        """数据验证 - 批判性思维检查"""
        errors = []
        
        for field, required in schema.items():
            if required and field not in data:
                errors.append(f"缺少必填字段: {field}")
        
        return len(errors) == 0, errors
    
    def critical_evaluate(self, source: str, data: Dict) -> Dict:
        """
        批判性思维评估 - 三阶九维评级
        返回 A/B/C/D 评级和详细评估
        """
        evaluation = {
            'source': source,
            'timestamp': datetime.now().isoformat(),
            'dimensions': {},
            'overall_rating': 'D',
            'confidence': 0.0
        }
        
        # 一阶：来源可信度
        source_credibility = self._evaluate_source_credibility(source)
        evaluation['dimensions']['source_credibility'] = source_credibility
        
        # 二阶：数据完整性
        data_completeness = self._evaluate_data_completeness(data)
        evaluation['dimensions']['data_completeness'] = data_completeness
        
        # 三阶：逻辑一致性
        logical_consistency = self._evaluate_logical_consistency(data)
        evaluation['dimensions']['logical_consistency'] = logical_consistency
        
        # 综合评级
        scores = [
            source_credibility.get('score', 0),
            data_completeness.get('score', 0),
            logical_consistency.get('score', 0)
        ]
        avg_score = sum(scores) / len(scores)
        
        if avg_score >= 0.8:
            evaluation['overall_rating'] = 'A'
        elif avg_score >= 0.6:
            evaluation['overall_rating'] = 'B'
        elif avg_score >= 0.4:
            evaluation['overall_rating'] = 'C'
        else:
            evaluation['overall_rating'] = 'D'
        
        evaluation['confidence'] = avg_score
        
        return evaluation
    
    def _evaluate_source_credibility(self, source: str) -> Dict:
        """评估来源可信度"""
        # 高可信度来源
        high_cred = ['中医科学院', '三甲医院', '国家药典', '核心期刊', 'PubMed', 'Cochrane']
        # 中等可信度
        medium_cred = ['医案数据库', '临床指南', '教材', ' Wikipedia']
        
        score = 0.5
        level = 'medium'
        
        for hc in high_cred:
            if hc in source:
                score = 0.9
                level = 'high'
                break
        
        if level == 'medium':
            for mc in medium_cred:
                if mc in source:
                    score = 0.7
                    break
        
        return {'score': score, 'level': level, 'source_type': source}
    
    def _evaluate_data_completeness(self, data: Dict) -> Dict:
        """评估数据完整性"""
        if not data:
            return {'score': 0.0, 'missing_fields': ['all']}
        
        # 检查关键字段
        required_fields = ['id', 'name', 'source', 'evidence_level']
        missing = [f for f in required_fields if f not in data]
        
        score = 1.0 - (len(missing) * 0.2)
        score = max(0, score)
        
        return {'score': score, 'missing_fields': missing}
    
    def _evaluate_logical_consistency(self, data: Dict) -> Dict:
        """评估逻辑一致性"""
        # 检查数据内部矛盾
        inconsistencies = []
        
        # 示例：检查药物功效与禁忌是否矛盾
        if 'functions' in data and 'contraindications' in data:
            funcs = str(data['functions']).lower()
            contras = str(data['contraindications']).lower()
            # 如果功效说"温热"但禁忌说"热证慎用" - 这是合理的
            # 如果功效说"降血压"但禁忌说"低血压禁用" - 需要标记
        
        score = 1.0 if not inconsistencies else 0.7
        
        return {'score': score, 'inconsistencies': inconsistencies}


# ========== 症状Agent ==========

class SymptomAgent(BaseAgent):
    """症状Agent - 负责症状标准化、编码、关联分析"""
    
    def __init__(self, data_dir: str = None):
        super().__init__("症状Agent", "AG-SN-001", data_dir)
        self.symptom_db = {}
        self._load_symptom_db()
    
    def _load_symptom_db(self):
        """加载症状数据库"""
        try:
            with open(os.path.join(self.data_dir, 'symptom_codes_v3_full.json'), 'r', encoding='utf-8') as f:
                data = json.load(f)
                for s in data.get('symptoms', []):
                    self.symptom_db[s['id']] = s
        except Exception as e:
            self.think("数据加载", f"症状数据库加载失败: {e}")
    
    def standardize_symptom(self, raw_symptom: str) -> Dict:
        """
        Step 1: 症状标准化
        输入: 用户原始描述
        输出: 标准化症状编码 + 元数据
        新增: 本地未匹配时，联网搜索相关临床数据
        """
        self.think("症状标准化", f"开始标准化症状: '{raw_symptom}'")
        
        # 1. 清理输入
        cleaned = raw_symptom.strip().lower()
        self.think("数据清理", f"清理后: '{cleaned}'")
        
        # 2. 尝试直接匹配
        matched = None
        for sid, s in self.symptom_db.items():
            if s['name'] == cleaned or cleaned in s.get('aliases', []):
                matched = s
                self.think("直接匹配", f"找到精确匹配: {sid} {s['name']}")
                break
        
        # 3. 如果未匹配，尝试语义搜索
        if not matched:
            self.think("语义搜索", f"未找到精确匹配，尝试语义搜索")
            # 这里可以接入语义引擎
            # 简化版：模糊匹配
            for sid, s in self.symptom_db.items():
                if cleaned in s['name'] or any(cleaned in a for a in s.get('aliases', [])):
                    matched = s
                    self.think("模糊匹配", f"找到模糊匹配: {sid} {s['name']}")
                    break
        
        # 4. 如果仍未匹配，尝试联网搜索
        if not matched:
            self.think("联网搜索", f"本地数据库未找到 '{raw_symptom}'，尝试联网搜索相关临床数据")
            web_results = self.search_web(f"{raw_symptom} 症状 中医 辨证", context="中医症状研究")
            
            if web_results and web_results[0].get('credibility_score', 0) > 0.3:
                self.think("联网搜索完成", f"找到 {len(web_results)} 条网络数据", [r.get('title', '') for r in web_results[:2]])
                return {
                    'status': 'web_verified',
                    'raw_input': raw_symptom,
                    'suggested_id': self._generate_temp_id(raw_symptom),
                    'confidence': 0.5,
                    'needs_verification': True,
                    'web_sources': web_results[:3]  # 包含网络来源
                }
            else:
                self.think("新症状", f"'{raw_symptom}' 未在数据库中找到，标记为待录入")
                return {
                    'status': 'new',
                    'raw_input': raw_symptom,
                    'suggested_id': self._generate_temp_id(raw_symptom),
                    'confidence': 0.0,
                    'needs_verification': True
                }
        
        # 5. 返回标准化结果
        result = {
            'status': 'matched',
            'id': matched['id'],
            'name': matched['name'],
            'pinyin': matched.get('pinyin', ''),
            'category': matched.get('category', ''),
            'part': matched.get('part', ''),
            'aliases': matched.get('aliases', []),
            'common_syndromes': matched.get('common_syndromes', []),
            'confidence': 1.0,
            'needs_verification': False
        }
        
        self.think("标准化完成", f"症状 '{raw_symptom}' 标准化为 {result['id']} {result['name']}")
        return result
    
    def _generate_temp_id(self, raw_symptom: str) -> str:
        """生成临时ID"""
        # 使用哈希生成临时编码
        import hashlib
        h = hashlib.md5(raw_symptom.encode()).hexdigest()[:6]
        return f"SN-TEMP-{h.upper()}"
    
    def analyze_symptom_combinations(self, symptom_ids: List[str]) -> Dict:
        """
        分析症状组合 - 识别证型
        """
        self.think("症状组合分析", f"分析症状组合: {symptom_ids}")
        
        symptoms = [self.symptom_db.get(sid) for sid in symptom_ids if sid in self.symptom_db]
        
        # 收集所有常见证型
        syndrome_counts = {}
        for s in symptoms:
            for syndrome in s.get('common_syndromes', []):
                syndrome_counts[syndrome] = syndrome_counts.get(syndrome, 0) + 1
        
        # 按出现频率排序
        sorted_syndromes = sorted(syndrome_counts.items(), key=lambda x: x[1], reverse=True)
        
        result = {
            'symptom_count': len(symptoms),
            'possible_syndromes': [
                {'name': name, 'match_count': count, 'confidence': count / len(symptoms)}
                for name, count in sorted_syndromes[:5]
            ],
            'analysis': f"基于{len(symptoms)}个症状，识别{len(sorted_syndromes)}个可能证型"
        }
        
        self.think("组合分析完成", f"识别到 {len(sorted_syndromes)} 个可能证型")
        return result


# ========== 药物Agent ==========

class DrugAgent(BaseAgent):
    """药物Agent - 负责药物档案管理、功效统计、配伍分析"""
    
    def __init__(self, data_dir: str = None):
        super().__init__("药物Agent", "AG-DR-001", data_dir)
        self.drug_db = {}
        self.drug_effect_stats = {}  # 药物效果统计
        self._load_drug_db()
    
    def _load_drug_db(self):
        """加载药物数据库"""
        try:
            with open(os.path.join(self.data_dir, 'drug_codes_v3_full.json'), 'r', encoding='utf-8') as f:
                data = json.load(f)
                for d in data.get('drugs', []):
                    self.drug_db[d['id']] = d
        except Exception as e:
            self.think("数据加载", f"药物数据库加载失败: {e}")
    
    def get_drug_profile(self, drug_id: str) -> Dict:
        """
        获取药物完整档案
        按DR编码生成药物完整档案
        新增: 本地未找到时，联网搜索补充信息
        """
        self.think("药物档案查询", f"查询药物: {drug_id}")
        
        drug = self.drug_db.get(drug_id)
        if not drug:
            self.think("未找到", f"药物 {drug_id} 不在本地数据库中")
            
            # 尝试联网搜索补充信息
            web_results = self.search_web(f"{drug_id} 中药 功效 性味归经", context="中药研究")
            
            if web_results and web_results[0].get('credibility_score', 0) > 0.3:
                self.think("联网补充", f"从网络获取到 {len(web_results)} 条补充信息")
                return {
                    'status': 'web_supplemented',
                    'id': drug_id,
                    'name': drug_id,
                    'web_sources': web_results[:3],
                    'note': '本地数据库未找到，信息来自网络搜索，需谨慎验证'
                }
            
            return {'status': 'not_found', 'id': drug_id}
        
        # 获取效果统计
        stats = self.drug_effect_stats.get(drug_id, {})
        
        # 联网搜索最新研究数据补充
        web_research = []
        if self.web_search and self.web_search.is_available():
            drug_name = drug.get('name', '')
            if drug_name:
                web_research = self.search_web(f"{drug_name} 中药 现代研究 药理", context="中药现代研究")
                if web_research:
                    self.think("研究补充", f"获取到 {len(web_research)} 条最新研究数据")
        
        profile = {
            'status': 'found',
            'id': drug_id,
            'name': drug.get('name', ''),
            'properties': drug.get('properties', ''),
            'functions': drug.get('functions', ''),
            'meridian': drug.get('meridian', ''),
            'indications': drug.get('indications', []),
            'effect_statistics': stats,
            'contraindications': drug.get('contraindications', []),
            'source': drug.get('source', '未知'),
            'latest_research': web_research[:2] if web_research else []  # 最新研究补充
        }
        
        self.think("档案生成", f"药物 {drug['name']} 档案生成完成")
        return profile
    
    def update_effect_statistics(self, drug_id: str, outcome: Dict):
        """
        更新药物效果统计
        outcome: {'effective': bool, 'symptom_improvement': int, 'side_effects': List}
        """
        if drug_id not in self.drug_effect_stats:
            self.drug_effect_stats[drug_id] = {
                'total_cases': 0,
                'effective_cases': 0,
                'ineffective_cases': 0,
                'side_effect_cases': 0,
                'effectiveness_rate': 0.0,
                'symptom_improvement_avg': 0.0,
                'common_side_effects': {}
            }
        
        stats = self.drug_effect_stats[drug_id]
        stats['total_cases'] += 1
        
        if outcome.get('effective', False):
            stats['effective_cases'] += 1
        else:
            stats['ineffective_cases'] += 1
        
        if outcome.get('side_effects', []):
            stats['side_effect_cases'] += 1
            for se in outcome['side_effects']:
                stats['common_side_effects'][se] = stats['common_side_effects'].get(se, 0) + 1
        
        # 更新有效率
        stats['effectiveness_rate'] = stats['effective_cases'] / stats['total_cases']
        
        # 更新症状改善平均分
        improvement = outcome.get('symptom_improvement', 0)
        stats['symptom_improvement_avg'] = (
            (stats['symptom_improvement_avg'] * (stats['total_cases'] - 1) + improvement)
            / stats['total_cases']
        )
        
        self.think("统计更新", f"药物 {drug_id} 效果统计已更新，当前有效率: {stats['effectiveness_rate']:.1%}")
    
    def check_drug_interactions(self, drug_ids: List[str]) -> List[Dict]:
        """
        检查药物配伍禁忌
        """
        self.think("配伍检查", f"检查 {len(drug_ids)} 味药物的配伍")
        
        interactions = []
        drugs = [self.drug_db.get(did) for did in drug_ids if did in self.drug_db]
        
        # 简化版：检查十八反、十九畏
        contraindicated_pairs = [
            ('甘草', '甘遂'), ('甘草', '大戟'), ('甘草', '芫花'), ('甘草', '海藻'),  # 十八反
            ('乌头', '半夏'), ('乌头', '瓜蒌'), ('乌头', '贝母'), ('乌头', '白蔹'), ('乌头', '白及'),
            ('藜芦', '人参'), ('藜芦', '丹参'), ('藜芦', '玄参'), ('藜芦', '细辛'), ('藜芦', '芍药'),
            ('硫黄', '朴硝'), ('水银', '砒霜'), ('狼毒', '密陀僧'), ('巴豆', '牵牛'),  # 十九畏
            ('丁香', '郁金'), ('川乌', '草乌'), ('牙硝', '三棱'), ('官桂', '赤石脂'),
        ]
        
        for i, d1 in enumerate(drugs):
            for j, d2 in enumerate(drugs[i+1:], i+1):
                name1, name2 = d1.get('name', ''), d2.get('name', '')
                
                for pair in contraindicated_pairs:
                    if (pair[0] in name1 and pair[1] in name2) or (pair[0] in name2 and pair[1] in name1):
                        interactions.append({
                            'drug1': {'id': d1['id'], 'name': name1},
                            'drug2': {'id': d2['id'], 'name': name2},
                            'type': 'contraindicated',
                            'rule': f"{pair[0]}反{pair[1]}" if pair in [
                                ('甘草', '甘遂'), ('甘草', '大戟'), ('甘草', '芫花'), ('甘草', '海藻'),
                                ('乌头', '半夏'), ('乌头', '瓜蒌'), ('乌头', '贝母'), ('乌头', '白蔹'), ('乌头', '白及'),
                                ('藜芦', '人参'), ('藜芦', '丹参'), ('藜芦', '玄参'), ('藜芦', '细辛'), ('藜芦', '芍药')
                            ] else f"{pair[0]}畏{pair[1]}",
                            'severity': 'high',
                            'recommendation': '避免同用，如需使用需医师严格监控'
                        })
                        self.think("配伍禁忌", f"发现禁忌: {name1} 与 {name2}")
        
        return interactions


# ========== 方剂Agent ==========

class FormulaAgent(BaseAgent):
    """方剂Agent - 负责方剂档案、组成分析、疗效统计"""
    
    def __init__(self, data_dir: str = None):
        super().__init__("方剂Agent", "AG-FP-001", data_dir)
        self.formula_db = {}
        self._load_formula_db()
    
    def _load_formula_db(self):
        """加载方剂数据库"""
        try:
            with open(os.path.join(self.data_dir, 'formula_codes_v3_5k.json'), 'r', encoding='utf-8') as f:
                data = json.load(f)
                for formula in data.get('formulas', []):
                    self.formula_db[formula['id']] = formula
        except Exception as e:
            self.think("数据加载", f"方剂数据库加载失败: {e}")
    
    def get_formula_profile(self, formula_id: str) -> Dict:
        """
        获取方剂完整档案
        按FP编码生成方剂（引用药物ID）
        新增: 联网搜索方剂临床证据
        """
        self.think("方剂档案查询", f"查询方剂: {formula_id}")
        
        formula = self.formula_db.get(formula_id)
        if not formula:
            self.think("未找到", f"方剂 {formula_id} 不在本地数据库中")
            
            # 尝试联网搜索
            web_results = self.search_web(f"{formula_id} 方剂 组成 功效 临床应用", context="方剂临床研究")
            
            if web_results and web_results[0].get('credibility_score', 0) > 0.3:
                self.think("联网补充", f"从网络获取到 {len(web_results)} 条补充信息")
                return {
                    'status': 'web_supplemented',
                    'id': formula_id,
                    'web_sources': web_results[:3],
                    'note': '本地数据库未找到，信息来自网络搜索，需谨慎验证'
                }
            
            return {'status': 'not_found', 'id': formula_id}
        
        # 解析组成药物
        composition = formula.get('composition', [])
        drug_refs = []
        for comp in composition:
            drug_refs.append({
                'drug_id': comp.get('drug_id', ''),
                'name': comp.get('name', ''),
                'dosage': comp.get('dosage', '')
            })
        
        # 联网搜索方剂临床证据
        clinical_evidence = []
        if self.web_search and self.web_search.is_available():
            formula_name = formula.get('name', '')
            if formula_name:
                clinical_evidence = self.search_web(
                    f"{formula_name} 方剂 临床研究 疗效 有效率", 
                    context="方剂临床研究"
                )
                if clinical_evidence:
                    self.think("证据补充", f"获取到 {len(clinical_evidence)} 条临床证据")
        
        profile = {
            'status': 'found',
            'id': formula_id,
            'name': formula.get('name', ''),
            'source': formula.get('source', ''),
            'category': formula.get('category', ''),
            'functions': formula.get('functions', ''),
            'indications': formula.get('indications', []),
            'composition': drug_refs,
            'modifications': formula.get('modifications', []),
            'contraindications': formula.get('contraindications', []),
            'clinical_evidence': clinical_evidence[:2] if clinical_evidence else []  # 临床证据
        }
        
        self.think("档案生成", f"方剂 {formula['name']} 档案生成完成，含{len(drug_refs)}味药")
        return profile
    
    def find_formulas_by_symptoms(self, symptom_ids: List[str]) -> List[Dict]:
        """根据症状查找相关方剂"""
        self.think("方剂检索", f"根据症状检索方剂: {symptom_ids}")
        
        matches = []
        for fid, formula in self.formula_db.items():
            indications = set(formula.get('indications', []))
            query_symptoms = set(symptom_ids)
            
            match_count = len(indications & query_symptoms)
            if match_count > 0:
                matches.append({
                    'id': fid,
                    'name': formula.get('name', ''),
                    'match_count': match_count,
                    'score': match_count / len(query_symptoms) if query_symptoms else 0,
                    'source': formula.get('source', '')
                })
        
        matches.sort(key=lambda x: x['score'], reverse=True)
        self.think("检索完成", f"找到 {len(matches)} 个相关方剂")
        return matches[:10]


# ========== 副作用Agent ==========

class AdverseEffectAgent(BaseAgent):
    """副作用Agent - 负责药物副作用收集、症状共现分析"""
    
    def __init__(self, data_dir: str = None):
        super().__init__("副作用Agent", "AG-AD-001", data_dir)
        self.adverse_db = {}  # 药物ID -> 副作用列表
        self.cooccurrence_matrix = {}  # 症状共现矩阵
    
    def record_adverse_effect(self, drug_id: str, patient_id: str, 
                              symptoms: List[str], onset_time: str, severity: int = 1):
        """
        记录副作用事件
        onset_time: 用药后多久出现（分钟/小时/天）
        severity: 1-5 严重程度
        """
        if drug_id not in self.adverse_db:
            self.adverse_db[drug_id] = []
        
        event = {
            'patient_id': patient_id,
            'symptoms': symptoms,
            'onset_time': onset_time,
            'severity': severity,
            'recorded_at': datetime.now().isoformat()
        }
        
        self.adverse_db[drug_id].append(event)
        
        # 更新症状共现
        for s1 in symptoms:
            if s1 not in self.cooccurrence_matrix:
                self.cooccurrence_matrix[s1] = {}
            for s2 in symptoms:
                if s1 != s2:
                    self.cooccurrence_matrix[s1][s2] = self.cooccurrence_matrix[s1].get(s2, 0) + 1
        
        self.think("副作用记录", f"药物 {drug_id} 记录副作用: {symptoms}, 严重程度 {severity}")
    
    def analyze_cooccurrence(self, symptom: str) -> Dict:
        """
        分析症状共现强度
        关键设计：失眠+心烦强度0.81（正常），失眠+腹泻强度0.15（异常），异常共现自动触发副作用警报
        """
        self.think("共现分析", f"分析症状 '{symptom}' 的共现模式")
        
        cooccur = self.cooccurrence_matrix.get(symptom, {})
        total = sum(cooccur.values())
        
        if total == 0:
            return {'symptom': symptom, 'cooccurrences': [], 'alert': False}
        
        results = []
        for other_symptom, count in cooccur.items():
            strength = count / total
            
            # 判断是否正常共现
            # 正常共现：同一证型的症状（如失眠+心烦=心阴虚）
            # 异常共现：不同系统的症状（如失眠+腹泻=可能副作用）
            is_normal = self._is_normal_cooccurrence(symptom, other_symptom)
            
            alert = not is_normal and strength > 0.3  # 异常且强度高，触发警报
            
            results.append({
                'symptom': other_symptom,
                'count': count,
                'strength': round(strength, 3),
                'is_normal': is_normal,
                'alert': alert
            })
        
        results.sort(key=lambda x: x['strength'], reverse=True)
        
        # 检查是否有异常高共现
        abnormal_high = [r for r in results if r['alert']]
        
        return {
            'symptom': symptom,
            'cooccurrences': results[:10],
            'alert_count': len(abnormal_high),
            'alerts': abnormal_high[:5]
        }
    
    def _is_normal_cooccurrence(self, s1: str, s2: str) -> bool:
        """判断两个症状共现是否正常（基于中医证型知识）"""
        # 简化版：常见正常共现对
        normal_pairs = [
            ('失眠', '心烦'), ('失眠', '心悸'), ('失眠', '健忘'),  # 心阴虚
            ('头痛', '眩晕'), ('头痛', '恶心'),  # 肝阳上亢
            ('胃痛', '腹胀'), ('胃痛', '恶心'), ('胃痛', '食欲不振'),  # 脾胃病
            ('咳嗽', '痰多'), ('咳嗽', '胸闷'),  # 肺病
            ('腰痛', '乏力'), ('腰痛', '膝软'),  # 肾虚
        ]
        
        for pair in normal_pairs:
            if (s1 in pair and s2 in pair) or (s2 in pair and s1 in pair):
                return True
        
        return False
    
    def time_window_analysis(self, drug_id: str) -> Dict:
        """
        时间窗口分层分析
        <30分钟急性过敏 / 1-3天常见副作用 / >7天慢性反应
        """
        self.think("时间窗口分析", f"分析药物 {drug_id} 的副作用时间分布")
        
        events = self.adverse_db.get(drug_id, [])
        
        windows = {
            'acute': {'time': '<30分钟', 'events': [], 'type': '急性过敏/毒性反应'},
            'short_term': {'time': '30分钟-3天', 'events': [], 'type': '常见副作用'},
            'medium_term': {'time': '3-7天', 'events': [], 'type': '亚急性反应'},
            'chronic': {'time': '>7天', 'events': [], 'type': '慢性反应/蓄积毒性'}
        }
        
        for event in events:
            onset = event['onset_time']
            # 简化解析
            if '分钟' in onset and self._extract_number(onset) < 30:
                windows['acute']['events'].append(event)
            elif '小时' in onset or ('天' in onset and self._extract_number(onset) <= 3):
                windows['short_term']['events'].append(event)
            elif '天' in onset and 3 < self._extract_number(onset) <= 7:
                windows['medium_term']['events'].append(event)
            else:
                windows['chronic']['events'].append(event)
        
        return {
            'drug_id': drug_id,
            'total_events': len(events),
            'time_distribution': {
                k: {
                    'count': len(v['events']),
                    'type': v['type'],
                    'common_symptoms': self._top_symptoms(v['events'])
                }
                for k, v in windows.items()
            }
        }
    
    def _extract_number(self, text: str) -> int:
        """从文本提取数字"""
        nums = re.findall(r'\d+', text)
        return int(nums[0]) if nums else 0
    
    def _top_symptoms(self, events: List[Dict]) -> List[str]:
        """统计最常见的症状"""
        symptom_counts = {}
        for e in events:
            for s in e.get('symptoms', []):
                symptom_counts[s] = symptom_counts.get(s, 0) + 1
        
        sorted_symptoms = sorted(symptom_counts.items(), key=lambda x: x[1], reverse=True)
        return [s[0] for s in sorted_symptoms[:5]]


# ========== 患者Agent ==========

class PatientAgent(BaseAgent):
    """患者Agent - 负责模拟患者档案、相似患者匹配、时间线管理"""
    
    def __init__(self, data_dir: str = None):
        super().__init__("患者Agent", "AG-PT-001", data_dir)
        self.patient_db = {}  # 患者ID -> 档案
    
    def create_patient_profile(self, patient_id: str, basic_info: Dict) -> Dict:
        """
        生成模拟患者档案（时间线）
        格式: PT-YYYYMMDD-XXX
        """
        self.think("患者建档", f"创建患者档案: {patient_id}")
        
        profile = {
            'id': patient_id,
            'created_at': datetime.now().isoformat(),
            'basic_info': basic_info,
            'timeline': [],  # 就诊时间线
            'symptom_history': [],
            'medication_history': [],
            'effectiveness_records': []
        }
        
        self.patient_db[patient_id] = profile
        return profile
    
    def add_timeline_event(self, patient_id: str, event: Dict):
        """添加时间线事件"""
        if patient_id not in self.patient_db:
            self.think("错误", f"患者 {patient_id} 不存在")
            return False
        
        event['recorded_at'] = datetime.now().isoformat()
        self.patient_db[patient_id]['timeline'].append(event)
        
        # 分类存储
        if event.get('type') == 'symptom':
            self.patient_db[patient_id]['symptom_history'].append(event)
        elif event.get('type') == 'medication':
            self.patient_db[patient_id]['medication_history'].append(event)
        elif event.get('type') == 'effectiveness':
            self.patient_db[patient_id]['effectiveness_records'].append(event)
        
        self.think("时间线更新", f"患者 {patient_id} 添加 {event.get('type')} 事件")
        return True
    
    def find_similar_patients(self, patient_id: str, top_k: int = 5) -> List[Dict]:
        """
        相似患者参照
        PT-20250715-003同方同反应，调整处方后痊愈，为当前患者提供可复现方案
        """
        self.think("相似患者搜索", f"为患者 {patient_id} 寻找相似患者")
        
        if patient_id not in self.patient_db:
            return []
        
        target = self.patient_db[patient_id]
        target_symptoms = set()
        for e in target.get('symptom_history', []):
            target_symptoms.update(e.get('symptoms', []))
        
        similarities = []
        for pid, profile in self.patient_db.items():
            if pid == patient_id:
                continue
            
            other_symptoms = set()
            for e in profile.get('symptom_history', []):
                other_symptoms.update(e.get('symptoms', []))
            
            # Jaccard相似度
            intersection = len(target_symptoms & other_symptoms)
            union = len(target_symptoms | other_symptoms)
            similarity = intersection / union if union > 0 else 0
            
            if similarity > 0.3:  # 至少30%症状重叠
                # 检查是否有疗效记录
                effectiveness = profile.get('effectiveness_records', [])
                last_outcome = effectiveness[-1] if effectiveness else None
                
                similarities.append({
                    'patient_id': pid,
                    'similarity': round(similarity, 3),
                    'common_symptoms': list(target_symptoms & other_symptoms),
                    'outcome': last_outcome.get('result', 'unknown') if last_outcome else 'unknown',
                    'treatment': last_outcome.get('treatment', '') if last_outcome else ''
                })
        
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        self.think("相似患者找到", f"找到 {len(similarities)} 个相似患者")
        return similarities[:top_k]


# ========== 共现Agent ==========

class CooccurrenceAgent(BaseAgent):
    """共现Agent - 分析症状共现强度、聚类预测"""
    
    def __init__(self, data_dir: str = None):
        super().__init__("共现Agent", "AG-CO-001", data_dir)
        self.cooccurrence_data = {}  # 症状对 -> 统计
        self.patient_groups = {}     # 患者群聚类
    
    def calculate_cooccurrence_strength(self, symptom1: str, symptom2: str, 
                                        patient_pool: List[Dict]) -> float:
        """
        计算症状共现强度
        失眠+心烦强度0.81（正常），失眠+腹泻强度0.15（异常）
        """
        self.think("共现计算", f"计算 {symptom1} 与 {symptom2} 的共现强度")
        
        both_count = 0
        s1_count = 0
        s2_count = 0
        total = len(patient_pool)
        
        for patient in patient_pool:
            symptoms = set(patient.get('symptoms', []))
            has_s1 = symptom1 in symptoms
            has_s2 = symptom2 in symptoms
            
            if has_s1:
                s1_count += 1
            if has_s2:
                s2_count += 1
            if has_s1 and has_s2:
                both_count += 1
        
        # 点互信息（PMI）
        if both_count == 0 or s1_count == 0 or s2_count == 0:
            pmi = -5.0
        else:
            p_both = both_count / total
            p_s1 = s1_count / total
            p_s2 = s2_count / total
            pmi = np.log(p_both / (p_s1 * p_s2)) if p_both > 0 and p_s1 > 0 and p_s2 > 0 else -5.0
        
        # 归一化到0-1
        strength = max(0, min(1, (pmi + 5) / 10))
        
        self.think("共现结果", f"共现强度: {strength:.3f}")
        return strength
    
    def cluster_prediction(self, patient_symptoms: List[str], 
                           cluster_data: Dict) -> Dict:
        """
        聚类预测
        心阴虚失眠群中腹泻发生率3.2%，脾胃虚寒者风险放大4.5倍
        """
        self.think("聚类预测", f"基于症状 {patient_symptoms} 进行聚类预测")
        
        # 匹配患者所属聚类
        matched_cluster = None
        for cluster_id, cluster in cluster_data.items():
            cluster_symptoms = set(cluster.get('core_symptoms', []))
            patient_symptoms_set = set(patient_symptoms)
            overlap = len(cluster_symptoms & patient_symptoms_set)
            
            if overlap >= len(cluster_symptoms) * 0.5:  # 50%核心症状匹配
                matched_cluster = cluster
                break
        
        if not matched_cluster:
            return {'cluster': 'unknown', 'risk_predictions': []}
        
        # 预测风险
        risks = []
        for risk in matched_cluster.get('associated_risks', []):
            base_rate = risk.get('base_rate', 0)
            risk_factors = risk.get('risk_factors', [])
            
            # 检查风险因子
            multiplier = 1.0
            for factor in risk_factors:
                if factor['symptom'] in patient_symptoms:
                    multiplier *= factor.get('multiplier', 1.0)
            
            adjusted_rate = min(1.0, base_rate * multiplier)
            
            risks.append({
                'risk_symptom': risk['symptom'],
                'base_rate': base_rate,
                'adjusted_rate': round(adjusted_rate, 4),
                'multiplier': round(multiplier, 2),
                'risk_level': 'high' if adjusted_rate > 0.5 else 'medium' if adjusted_rate > 0.2 else 'low'
            })
        
        return {
            'cluster': matched_cluster.get('name', ''),
            'cluster_id': matched_cluster.get('id', ''),
            'risk_predictions': risks
        }


# ========== 聚类Agent ==========

class ClusteringAgent(BaseAgent):
    """聚类Agent - 基于患者群做相似度聚类"""
    
    def __init__(self, data_dir: str = None):
        super().__init__("聚类Agent", "AG-CL-001", data_dir)
        self.clusters = {}  # 聚类ID -> 聚类数据
    
    def create_cluster(self, cluster_id: str, name: str, 
                       core_symptoms: List[str], description: str) -> Dict:
        """创建患者聚类"""
        cluster = {
            'id': cluster_id,
            'name': name,
            'core_symptoms': core_symptoms,
            'description': description,
            'patients': [],
            'associated_risks': [],
            'treatment_outcomes': {}
        }
        
        self.clusters[cluster_id] = cluster
        self.think("聚类创建", f"创建聚类 {cluster_id}: {name}")
        return cluster
    
    def add_patient_to_cluster(self, cluster_id: str, patient_id: str, 
                               symptoms: List[str], outcome: Dict):
        """添加患者到聚类"""
        if cluster_id not in self.clusters:
            self.think("错误", f"聚类 {cluster_id} 不存在")
            return False
        
        self.clusters[cluster_id]['patients'].append({
            'patient_id': patient_id,
            'symptoms': symptoms,
            'outcome': outcome
        })
        
        # 更新治疗结果统计
        treatment = outcome.get('treatment', 'unknown')
        result = outcome.get('result', 'unknown')
        
        if treatment not in self.clusters[cluster_id]['treatment_outcomes']:
            self.clusters[cluster_id]['treatment_outcomes'][treatment] = {
                'total': 0, 'effective': 0, 'ineffective': 0
            }
        
        self.clusters[cluster_id]['treatment_outcomes'][treatment]['total'] += 1
        if result == 'effective':
            self.clusters[cluster_id]['treatment_outcomes'][treatment]['effective'] += 1
        else:
            self.clusters[cluster_id]['treatment_outcomes'][treatment]['ineffective'] += 1
        
        self.think("聚类更新", f"患者 {patient_id} 加入聚类 {cluster_id}")
        return True
    
    def get_cluster_statistics(self, cluster_id: str) -> Dict:
        """获取聚类统计"""
        if cluster_id not in self.clusters:
            return {'status': 'not_found'}
        
        cluster = self.clusters[cluster_id]
        
        # 计算各治疗有效率
        treatment_stats = {}
        for treatment, stats in cluster['treatment_outcomes'].items():
            total = stats['total']
            effective = stats['effective']
            treatment_stats[treatment] = {
                'total_cases': total,
                'effective_cases': effective,
                'effectiveness_rate': round(effective / total, 3) if total > 0 else 0
            }
        
        return {
            'cluster_id': cluster_id,
            'name': cluster['name'],
            'patient_count': len(cluster['patients']),
            'core_symptoms': cluster['core_symptoms'],
            'treatment_statistics': treatment_stats
        }


# ========== Agent协调器 ==========

class AgentCoordinator:
    """Agent协调器 - 管理所有Agent协作"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir
        self.agents = {
            'symptom': SymptomAgent(data_dir),
            'drug': DrugAgent(data_dir),
            'formula': FormulaAgent(data_dir),
            'adverse': AdverseEffectAgent(data_dir),
            'patient': PatientAgent(data_dir),
            'cooccurrence': CooccurrenceAgent(data_dir),
            'clustering': ClusteringAgent(data_dir)
        }
    
    def get_agent(self, agent_type: str) -> BaseAgent:
        """获取指定Agent"""
        return self.agents.get(agent_type)
    
    def full_analysis(self, user_input: str, patient_id: str = None) -> Dict:
        """
        完整分析流程 - 多Agent协作
        """
        # 1. 症状Agent标准化
        symptom_agent = self.agents['symptom']
        symptom_agent.clear_thoughts()
        
        std_symptom = symptom_agent.standardize_symptom(user_input)
        
        # 2. 如果找到症状，继续分析
        if std_symptom['status'] == 'matched':
            # 方剂Agent查找相关方剂
            formula_agent = self.agents['formula']
            formula_agent.clear_thoughts()
            
            related_formulas = formula_agent.find_formulas_by_symptoms([std_symptom['id']])
            
            # 收集所有思考过程
            thoughts = []
            thoughts.extend(symptom_agent.get_thoughts())
            thoughts.extend(formula_agent.get_thoughts())
            
            return {
                'status': 'success',
                'symptom': std_symptom,
                'related_formulas': related_formulas,
                'thought_process': thoughts,
                'next_steps': ['查找相关药物', '查找穴位', '查找食疗']
            }
        
        return {
            'status': 'new_symptom',
            'symptom': std_symptom,
            'thought_process': symptom_agent.get_thoughts(),
            'recommendation': '该症状不在数据库中，建议专家审核后录入'
        }
    
    def get_all_thoughts(self) -> List[Dict]:
        """获取所有Agent的思考日志"""
        all_thoughts = []
        for agent in self.agents.values():
            all_thoughts.extend(agent.get_thoughts())
        return all_thoughts


# 单例
_coordinator = None

def get_agent_coordinator():
    global _coordinator
    if _coordinator is None:
        _coordinator = AgentCoordinator()
    return _coordinator


if __name__ == '__main__':
    # 测试Agent系统
    coord = AgentCoordinator()
    
    # 测试症状标准化
    result = coord.full_analysis("失眠")
    print("\n=== 分析结果 ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 测试药物配伍
    drug_agent = coord.get_agent('drug')
    # 模拟药物ID
    interactions = drug_agent.check_drug_interactions(['DR-001', 'DR-002'])
    print("\n=== 配伍检查结果 ===")
    print(json.dumps(interactions, ensure_ascii=False, indent=2))
