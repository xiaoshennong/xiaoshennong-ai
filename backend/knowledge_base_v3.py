#!/usr/bin/env python3
"""
小神农中医AI - 超大规模结构化知识库 v3.0
直接加载JSON数据到内存，无需向量数据库
支持快速症状匹配、方剂推荐、药物查询
"""

import os
import json
import sys
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher

sys.dont_write_bytecode = True

# 项目路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")


class MassiveKnowledgeBase:
    """
    超大规模中医知识库
    直接加载JSON数据，内存索引，毫秒级查询
    """
    
    def __init__(self):
        self.symptoms = {}  # 症状库
        self.drugs = {}     # 药物库
        self.formulas = {}  # 方剂库
        self.cases = []     # 医案库
        self.texts = []     # 古籍库
        
        # 症状名称到ID的索引
        self.symptom_name_index = {}  # name -> id
        self.symptom_alias_index = {}  # alias -> id
        
        # 症状到方剂的索引
        self.symptom_to_formulas = {}  # symptom_id -> [formula_ids]
        # 症状到药物的索引
        self.symptom_to_drugs = {}     # symptom_id -> [drug_ids]
        
        self._loaded = False
        self._stats = {}
    
    def load_all(self):
        """加载所有数据"""
        if self._loaded:
            return
        
        print("[知识库] 开始加载数据...")
        
        # 1. 加载症状（使用合并后的数据）
        self._load_symptoms('merged_symptoms.json')
        
        # 2. 加载药物（使用合并后的数据）
        self._load_drugs('merged_drugs.json')
        
        # 3. 加载方剂（使用合并后的数据）
        self._load_formulas('merged_formulas.json')
        
        # 4. 加载医案（只加载前1000条避免内存过大）
        self._load_cases(max_count=1000)
        
        # 5. 加载古籍（只加载前1000条）
        self._load_texts(max_count=1000)
        
        # 6. 构建索引
        self._build_indexes()
        
        self._loaded = True
        
        self._stats = {
            'symptoms': len(self.symptoms),
            'drugs': len(self.drugs),
            'formulas': len(self.formulas),
            'cases': len(self.cases),
            'texts': len(self.texts),
        }
        
        print(f"[知识库] 加载完成!")
        print(f"  症状: {self._stats['symptoms']}")
        print(f"  药物: {self._stats['drugs']}")
        print(f"  方剂: {self._stats['formulas']}")
        print(f"  医案: {self._stats['cases']}")
        print(f"  古籍: {self._stats['texts']}")
    
    def _load_symptoms(self, filename='extended_symptoms.json'):
        """加载症状数据"""
        filepath = os.path.join(RAW_DIR, filename)
        if not os.path.exists(filepath):
            print(f"[警告] 症状文件不存在: {filepath}")
            return
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.symptoms = data
        
        # 构建索引
        for sid, info in data.items():
            self.symptom_name_index[info['name']] = sid
            for alias in info.get('aliases', []):
                self.symptom_alias_index[alias] = sid
        
        print(f"[症状] 加载 {len(data)} 个")
    
    def _load_drugs(self, filename='extended_drugs.json'):
        """加载药物数据"""
        filepath = os.path.join(RAW_DIR, filename)
        if not os.path.exists(filepath):
            return
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.drugs = data
        print(f"[药物] 加载 {len(data)} 个")
    
    def _load_formulas(self, filename='extended_formulas.json'):
        """加载方剂数据"""
        filepath = os.path.join(RAW_DIR, filename)
        if not os.path.exists(filepath):
            return
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.formulas = data
        print(f"[方剂] 加载 {len(data)} 个")
    
    def _load_cases(self, max_count=1000):
        """加载医案数据"""
        count = 0
        for i in range(1, 6):
            filepath = os.path.join(RAW_DIR, f'medical_cases_batch_{i}.json')
            if not os.path.exists(filepath):
                continue
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for case in data:
                if count >= max_count:
                    break
                self.cases.append(case)
                count += 1
            
            if count >= max_count:
                break
        
        print(f"[医案] 加载 {len(self.cases)} 个")
    
    def _load_texts(self, max_count=1000):
        """加载古籍数据"""
        count = 0
        for i in range(1, 6):
            filepath = os.path.join(RAW_DIR, f'classical_texts_batch_{i}.json')
            if not os.path.exists(filepath):
                continue
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for text in data:
                if count >= max_count:
                    break
                self.texts.append(text)
                count += 1
            
            if count >= max_count:
                break
        
        print(f"[古籍] 加载 {len(self.texts)} 条")
    
    def _build_indexes(self):
        """构建症状-方剂/药物索引"""
        # 症状->方剂
        for fid, formula in self.formulas.items():
            for sid in formula.get('indications', []):
                if sid not in self.symptom_to_formulas:
                    self.symptom_to_formulas[sid] = []
                self.symptom_to_formulas[sid].append(fid)
        
        # 症状->药物
        for did, drug in self.drugs.items():
            for sid in drug.get('indications', []):
                if sid not in self.symptom_to_drugs:
                    self.symptom_to_drugs[sid] = []
                self.symptom_to_drugs[sid].append(did)
        
        print(f"[索引] 构建完成")
    
    def find_symptoms_by_text(self, text: str) -> List[Dict]:
        """从文本中识别症状"""
        text = text.lower()
        matched = []
        seen = set()
        
        # 直接匹配别名
        for alias, sid in self.symptom_alias_index.items():
            if alias in text and sid not in seen:
                info = self.symptoms.get(sid, {})
                matched.append({
                    'id': sid,
                    'name': info.get('name', ''),
                    'matched_alias': alias,
                    'classic_refs': info.get('classic_refs', [])
                })
                seen.add(sid)
        
        # 按名称长度排序（长的优先）
        matched.sort(key=lambda x: len(x['name']), reverse=True)
        return matched
    
    def find_formulas_by_symptoms(self, symptom_ids: List[str]) -> List[Dict]:
        """根据症状查找方剂"""
        formula_scores = {}
        
        for sid in symptom_ids:
            for fid in self.symptom_to_formulas.get(sid, []):
                formula_scores[fid] = formula_scores.get(fid, 0) + 1
        
        # 计算匹配度并排序
        results = []
        for fid, score in formula_scores.items():
            formula = self.formulas.get(fid, {})
            indications = formula.get('indications', [])
            if not indications:
                continue
            
            match_rate = score / len(indications)
            results.append({
                'id': fid,
                'name': formula.get('name', ''),
                'source': formula.get('source', ''),
                'syndrome': formula.get('syndrome', ''),
                'match_score': match_rate,
                'matched_symptoms': [sid for sid in symptom_ids if sid in indications],
                'contraindications': formula.get('contraindications', [])
            })
        
        results.sort(key=lambda x: x['match_score'], reverse=True)
        return results
    
    def find_drugs_by_symptoms(self, symptom_ids: List[str]) -> List[Dict]:
        """根据症状查找药物"""
        drug_scores = {}
        
        for sid in symptom_ids:
            for did in self.symptom_to_drugs.get(sid, []):
                drug_scores[did] = drug_scores.get(did, 0) + 1
        
        results = []
        for did, score in drug_scores.items():
            drug = self.drugs.get(did, {})
            indications = drug.get('indications', [])
            if not indications:
                continue
            
            match_rate = score / len(indications)
            results.append({
                'id': did,
                'name': drug.get('name', ''),
                'properties': drug.get('properties', {}),
                'match_score': match_rate,
                'matched_symptoms': [sid for sid in symptom_ids if sid in indications],
                'contraindications': drug.get('contraindications', [])
            })
        
        results.sort(key=lambda x: x['match_score'], reverse=True)
        return results
    
    def get_formula_detail(self, formula_id: str) -> Optional[Dict]:
        """获取方剂详情"""
        formula = self.formulas.get(formula_id)
        if not formula:
            return None
        
        # 解析组成药物
        composition = []
        for did, amount in formula.get('composition', {}).items():
            drug = self.drugs.get(did, {})
            composition.append({
                'id': did,
                'name': drug.get('name', did),
                'amount': amount
            })
        
        return {
            'id': formula_id,
            'name': formula.get('name', ''),
            'source': formula.get('source', ''),
            'syndrome': formula.get('syndrome', ''),
            'composition': composition,
            'indications': formula.get('indications', []),
            'contraindications': formula.get('contraindications', []),
            'effectiveness_stats': formula.get('effectiveness_stats', {})
        }
    
    def get_drug_detail(self, drug_id: str) -> Optional[Dict]:
        """获取药物详情"""
        drug = self.drugs.get(drug_id)
        if not drug:
            return None
        
        return {
            'id': drug_id,
            'name': drug.get('name', ''),
            'properties': drug.get('properties', {}),
            'indications': drug.get('indications', []),
            'contraindications': drug.get('contraindications', []),
            'effectiveness_stats': drug.get('effectiveness_stats', {})
        }
    
    def search_cases(self, symptom_ids: List[str], limit: int = 5) -> List[Dict]:
        """搜索相似医案"""
        scored_cases = []
        
        for case in self.cases:
            case_symptoms = case.get('symptoms', [])
            matched = [sid for sid in symptom_ids if sid in case_symptoms]
            if matched:
                score = len(matched) / max(len(case_symptoms), len(symptom_ids))
                scored_cases.append((score, case))
        
        scored_cases.sort(key=lambda x: x[0], reverse=True)
        return [case for _, case in scored_cases[:limit]]
    
    def search_texts(self, query: str, limit: int = 5) -> List[Dict]:
        """搜索古籍条文"""
        scored_texts = []
        
        for text in self.texts:
            content = text.get('text', '')
            # 简单相似度计算
            score = SequenceMatcher(None, query.lower(), content.lower()).ratio()
            scored_texts.append((score, text))
        
        scored_texts.sort(key=lambda x: x[0], reverse=True)
        return [text for _, text in scored_texts[:limit]]
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self._stats


# 全局单例
_kb_instance = None

def get_knowledge_base() -> MassiveKnowledgeBase:
    """获取知识库单例"""
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = MassiveKnowledgeBase()
        _kb_instance.load_all()
    return _kb_instance


if __name__ == '__main__':
    kb = get_knowledge_base()
    
    # 测试查询
    print("\n[测试] 查询症状 '头痛发热'")
    symptoms = kb.find_symptoms_by_text('头痛发热')
    print(f"  识别到 {len(symptoms)} 个症状:")
    for s in symptoms[:5]:
        print(f"    {s['id']}: {s['name']}")
    
    if symptoms:
        symptom_ids = [s['id'] for s in symptoms]
        
        print(f"\n[测试] 匹配方剂")
        formulas = kb.find_formulas_by_symptoms(symptom_ids)
        for f in formulas[:3]:
            print(f"    {f['name']} (匹配度: {f['match_score']:.2f})")
        
        print(f"\n[测试] 匹配药物")
        drugs = kb.find_drugs_by_symptoms(symptom_ids)
        for d in drugs[:3]:
            print(f"    {d['name']} (匹配度: {d['match_score']:.2f})")
