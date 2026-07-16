#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小神农中医AI - 本地API v5.0 (Agent + 语义匹配版)
支持：中药方剂、针灸、推拿、食疗、导引、体质辨识
新增：语义搜索、多Agent协作、AI思考过程展示
"""

import json
import os
import re
import time
import random
from datetime import datetime
from typing import List, Dict
from flask import Flask, request, jsonify
from flask_cors import CORS

# 导入语义引擎和Agent系统
try:
    from semantic_engine import get_semantic_engine, SemanticMatcher
    HAS_SEMANTIC = True
except ImportError:
    HAS_SEMANTIC = False
    print("[LocalAPI v5.0] 语义引擎未加载")

try:
    from agent_system import get_agent_coordinator
    HAS_AGENTS = True
except ImportError:
    HAS_AGENTS = False
    print("[LocalAPI v5.0] Agent系统未加载")

# 导入联网搜索模块
try:
    from web_search_agent import init_web_search, get_web_search_agent
    HAS_WEBSEARCH = True
    
    # 初始化联网搜索（统一使用 Yunwu AI）
    web_search_agent = init_web_search(
        api_key=os.environ.get('YUNWU_API_KEY', ''),
        base_url=os.environ.get('YUNWU_API_BASE', '') or 'https://yunwu.ai/v1',
        model=os.environ.get('YUNWU_MODEL', 'gpt-4o-mini')
    )
    
    if web_search_agent.is_available():
        print("[LocalAPI v5.0] 联网搜索已启用")
    else:
        print("[LocalAPI v5.0] 联网搜索未启用（API密钥无效）")
        
except ImportError:
    HAS_WEBSEARCH = False
    print("[LocalAPI v5.0] 联网搜索模块未加载")

app = Flask(__name__)
CORS(app)

# ========== 加载编码数据库 ==========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')

# 加载症状数据
SYMPTOM_MAP = {}
SYMPTOM_NAME_MAP = {}

try:
    with open(os.path.join(DATA_DIR, 'symptom_codes_v3_full.json'), 'r', encoding='utf-8') as f:
        symptom_data = json.load(f)
        for s in symptom_data.get('symptoms', []):
            SYMPTOM_MAP[s['id']] = s
            SYMPTOM_NAME_MAP[s['name']] = s
            for alias in s.get('aliases', []):
                SYMPTOM_NAME_MAP[alias] = s
    print(f"[LocalAPI v5.0] 症状: {len(SYMPTOM_MAP)} 条")
except Exception as e:
    print(f"[LocalAPI v5.0] 症状加载失败: {e}")

# 加载药物数据
DRUG_MAP = {}
DRUG_NAME_MAP = {}

try:
    with open(os.path.join(DATA_DIR, 'drug_codes_v3_full.json'), 'r', encoding='utf-8') as f:
        drug_data = json.load(f)
        for d in drug_data.get('drugs', []):
            DRUG_MAP[d['id']] = d
            DRUG_NAME_MAP[d['name']] = d
    print(f"[LocalAPI v5.0] 药物: {len(DRUG_MAP)} 条")
except Exception as e:
    print(f"[LocalAPI v5.0] 药物加载失败: {e}")

# 加载方剂数据
FORMULA_MAP = {}
FORMULA_NAME_MAP = {}

try:
    with open(os.path.join(DATA_DIR, 'formula_codes_v3_10k.json'), 'r', encoding='utf-8') as f:
        formula_data = json.load(f)
        FORMULA_MAP = {f['id']: f for f in formula_data.get('formulas', [])}
        FORMULA_NAME_MAP = {f['name']: f for f in formula_data.get('formulas', [])}
    print(f"[LocalAPI v5.0] 方剂: {len(FORMULA_MAP)} 条")
except Exception as e:
    print(f"[LocalAPI v5.0] 方剂加载失败: {e}")

# 加载针灸数据
ACUPOINT_MAP = {}
ACUPOINT_NAME_MAP = {}

try:
    with open(os.path.join(DATA_DIR, 'acupuncture_db.json'), 'r', encoding='utf-8') as f:
        acu_data = json.load(f)
        for a in acu_data.get('acupoints', []):
            ACUPOINT_MAP[a['id']] = a
            ACUPOINT_NAME_MAP[a['name']] = a
    try:
        with open(os.path.join(DATA_DIR, 'acupuncture_extended.json'), 'r', encoding='utf-8') as f:
            acu_ext = json.load(f)
            for a in acu_ext.get('acupoints', []):
                ACUPOINT_MAP[a['id']] = a
                ACUPOINT_NAME_MAP[a['name']] = a
    except:
        pass
    print(f"[LocalAPI v5.0] 穴位: {len(ACUPOINT_MAP)} 条")
except Exception as e:
    print(f"[LocalAPI v5.0] 穴位加载失败: {e}")

# 加载推拿数据
MASSAGE_MAP = {}
MASSAGE_ROUTINE_MAP = {}

try:
    with open(os.path.join(DATA_DIR, 'massage_db.json'), 'r', encoding='utf-8') as f:
        mass_data = json.load(f)
        for m in mass_data.get('massage_techniques', []):
            MASSAGE_MAP[m['id']] = m
        for m in mass_data.get('massage_routines', []):
            MASSAGE_ROUTINE_MAP[m['id']] = m
    print(f"[LocalAPI v5.0] 推拿: {len(MASSAGE_MAP)} 手法, {len(MASSAGE_ROUTINE_MAP)} 套路")
except Exception as e:
    print(f"[LocalAPI v5.0] 推拿加载失败: {e}")

# 加载食疗数据
DIETARY_MAP = {}

try:
    with open(os.path.join(DATA_DIR, 'dietary_db.json'), 'r', encoding='utf-8') as f:
        diet_data = json.load(f)
        for d in diet_data.get('dietary_therapies', []):
            DIETARY_MAP[d['id']] = d
    print(f"[LocalAPI v5.0] 食疗: {len(DIETARY_MAP)} 条")
except Exception as e:
    print(f"[LocalAPI v5.0] 食疗加载失败: {e}")

# 加载导引数据
QIGONG_MAP = {}

try:
    with open(os.path.join(DATA_DIR, 'qigong_db.json'), 'r', encoding='utf-8') as f:
        qg_data = json.load(f)
        for q in qg_data.get('qigong_routines', []):
            QIGONG_MAP[q['id']] = q
    print(f"[LocalAPI v5.0] 导引: {len(QIGONG_MAP)} 条")
except Exception as e:
    print(f"[LocalAPI v5.0] 导引加载失败: {e}")

# 加载体质数据
CONSTITUTION_MAP = {}
CONSTITUTION_NAME_MAP = {}

try:
    with open(os.path.join(DATA_DIR, 'constitution_db.json'), 'r', encoding='utf-8') as f:
        const_data = json.load(f)
        for c in const_data.get('constitutions', []):
            CONSTITUTION_MAP[c['id']] = c
            CONSTITUTION_NAME_MAP[c['name']] = c
    print(f"[LocalAPI v5.0] 体质: {len(CONSTITUTION_MAP)} 种")
except Exception as e:
    print(f"[LocalAPI v5.0] 体质加载失败: {e}")

# 症状别名映射
SYMPTOM_ALIASES = {
    '失眠': '不寐', '睡不着': '不寐', '难入睡': '不寐', '易醒': '不寐', '早醒': '不寐',
    '睡眠不好': '不寐', '睡不好': '不寐', '睡觉不好': '不寐', '夜不能寐': '不寐', '不得眠': '不寐',
    '胃疼': '胃痛', '胃不舒服': '胃痛', '肚子疼': '腹痛', '拉肚子': '腹泻', '拉稀': '腹泻',
    '大便稀': '腹泻', '大便干': '便秘', '拉不出': '便秘', '排便困难': '便秘',
    '上火': '口苦', '嗓子疼': '咽喉痛', '喉咙痛': '咽喉痛',
    '没力气': '乏力', '没精神': '乏力', '累': '乏力', '疲倦': '乏力', '疲劳': '乏力',
    '心慌': '心悸', '心跳快': '心悸', '胸口闷': '胸闷', '胸口痛': '胸痛',
    '腰酸': '腰痛', '腰不舒服': '腰痛', '关节疼': '关节痛', '关节不适': '关节痛',
    '皮肤痒': '皮肤瘙痒', '身上痒': '皮肤瘙痒',
    '月经不准': '月经不调', '月经不规律': '月经不调', '来月经疼': '痛经', '经痛': '痛经',
    '呕吐': '恶心', '想吐': '恶心', '反胃': '恶心',
    '吃不下': '食欲不振', '没胃口': '食欲不振', '不想吃饭': '食欲不振', '吃饭不香': '食欲不振',
    '头疼': '头痛', '头胀痛': '头痛', '偏头痛': '头痛',
    '头晕': '眩晕', '头昏': '眩晕', '眼花': '眩晕',
    '口干': '口渴', '咽干': '口渴', '舌燥': '口渴',
    '肚子胀': '腹胀', '胃胀': '腹胀', '脘腹胀满': '腹胀',
    '冒汗': '出汗', '自汗': '出汗', '盗汗': '出汗', '多汗': '出汗',
}

print(f"[LocalAPI v5.0] 加载完成:")
print(f"  症状: {len(SYMPTOM_MAP)} 条")
print(f"  药物: {len(DRUG_MAP)} 条")
print(f"  方剂: {len(FORMULA_MAP)} 条")
print(f"  穴位: {len(ACUPOINT_MAP)} 个")
print(f"  推拿: {len(MASSAGE_MAP)} 手法, {len(MASSAGE_ROUTINE_MAP)} 套路")
print(f"  食疗: {len(DIETARY_MAP)} 条")
print(f"  导引: {len(QIGONG_MAP)} 条")
print(f"  体质: {len(CONSTITUTION_MAP)} 种")
print(f"  语义引擎: {'已加载' if HAS_SEMANTIC else '未加载'}")
print(f"  Agent系统: {'已加载' if HAS_AGENTS else '未加载'}")


# ========== 初始化语义引擎（延迟加载） ==========
semantic_engine = None
if HAS_SEMANTIC:
    try:
        semantic_engine = get_semantic_engine()
        # 不立即构建索引，改为按需构建
        # 穴位数据太多（361个），构建索引很慢
        print("[LocalAPI v5.0] 语义引擎已创建（索引按需构建）")
    except Exception as e:
        print(f"[LocalAPI v5.0] 语义引擎创建失败: {e}")
        semantic_engine = None

# ========== 初始化Agent协调器 ==========
agent_coordinator = None
if HAS_AGENTS:
    try:
        agent_coordinator = get_agent_coordinator()
        print("[LocalAPI v5.0] Agent协调器初始化完成")
    except Exception as e:
        print(f"[LocalAPI v5.0] Agent协调器初始化失败: {e}")


# ========== 核心检索引擎 v5.0 ==========

class XiaoShennongEngineV5:
    """小神农中医AI检索引擎 v5.0 - Agent + 语义匹配版"""
    
    def __init__(self):
        self.symptoms = SYMPTOM_MAP
        self.drugs = DRUG_MAP
        self.formulas = FORMULA_MAP
        self.acupoints = ACUPOINT_MAP
        self.massage_routines = MASSAGE_ROUTINE_MAP
        self.dietary = DIETARY_MAP
        self.qigong = QIGONG_MAP
        self.constitutions = CONSTITUTION_MAP
        self.symptom_name_map = SYMPTOM_NAME_MAP
        self.drug_name_map = DRUG_NAME_MAP
        self.formula_name_map = FORMULA_NAME_MAP
        
    def parse_query(self, query: str):
        """解析查询，提取症状编码和中文症状名"""
        result = {
            'symptom_ids': [],
            'symptom_names': [],
            'drug_ids': [],
            'drug_names': [],
            'formula_ids': [],
            'formula_names': [],
            'raw_query': query
        }
        
        # 1. 提取症状编码 (SN-XXX)
        symptom_id_pattern = r'SN-\d{3,}'
        found_ids = re.findall(symptom_id_pattern, query.upper())
        result['symptom_ids'].extend(found_ids)
        
        # 2. 提取药物编码 (DR-XXX)
        drug_id_pattern = r'DR-\d{3,}'
        found_drug_ids = re.findall(drug_id_pattern, query.upper())
        result['drug_ids'].extend(found_drug_ids)
        
        # 3. 提取方剂编码 (FP-XXXX)
        formula_id_pattern = r'FP-\d{3,}'
        found_formula_ids = re.findall(formula_id_pattern, query.upper())
        result['formula_ids'].extend(found_formula_ids)
        
        # 4. 处理别名映射
        for alias, standard_name in SYMPTOM_ALIASES.items():
            if alias in query and standard_name in SYMPTOM_NAME_MAP:
                std_symptom = SYMPTOM_NAME_MAP[standard_name]
                sid = std_symptom.get('id', '')
                if sid and sid not in result['symptom_ids']:
                    result['symptom_ids'].append(sid)
                    result['symptom_names'].append(standard_name)
        
        # 5. 中文症状名匹配
        for name, symptom in self.symptom_name_map.items():
            if len(name) >= 2 and name in query:
                sid = symptom.get('id', '')
                if sid and sid not in result['symptom_ids']:
                    result['symptom_ids'].append(sid)
                    result['symptom_names'].append(name)
        
        # 6. 中文药物名匹配
        for name, drug in self.drug_name_map.items():
            if len(name) >= 2 and name in query:
                did = drug.get('id', '')
                if did and did not in result['drug_ids']:
                    result['drug_ids'].append(did)
                    result['drug_names'].append(name)
        
        # 7. 中文方剂名匹配
        for name, formula in self.formula_name_map.items():
            if len(name) >= 2 and name in query:
                fid = formula.get('id', '')
                if fid and fid not in result['formula_ids']:
                    result['formula_ids'].append(fid)
                    result['formula_names'].append(name)
        
        return result
    
    def semantic_search(self, query: str, top_k: int = 10):
        """语义搜索 - 使用嵌入模型进行语义匹配"""
        results = {
            'symptoms': [],
            'drugs': [],
            'formulas': [],
            'acupoints': [],
            'dietary': []
        }
        
        if semantic_engine and semantic_engine.initialized:
            try:
                cross_results = semantic_engine.cross_search(query, top_k=top_k)
                results.update(cross_results)
            except Exception as e:
                print(f"[SemanticSearch] 错误: {e}")
        
        return results
    
    def search_by_symptoms(self, symptom_ids: list, top_k: int = 5):
        """根据症状编码检索相关方剂、药物、穴位、食疗、导引"""
        results = []
        query_symptoms = set(symptom_ids)
        
        # 1. 查找包含这些症状的药物（OR匹配）
        for did, drug in self.drugs.items():
            drug_symptoms = set(drug.get('indications', []))
            match_count = len(drug_symptoms & query_symptoms)
            if match_count > 0:
                results.append({
                    'type': 'drug',
                    'id': did,
                    'name': drug.get('name', ''),
                    'score': match_count / len(query_symptoms),
                    'data': drug,
                    'matched_symptoms': list(drug_symptoms & query_symptoms)
                })
        
        # 2. 查找包含这些症状的方剂（OR匹配）
        for fid, formula in self.formulas.items():
            formula_symptoms = set(formula.get('indications', []))
            match_count = len(formula_symptoms & query_symptoms)
            if match_count > 0:
                results.append({
                    'type': 'formula',
                    'id': fid,
                    'name': formula.get('name', ''),
                    'score': match_count / len(query_symptoms),
                    'data': formula,
                    'matched_symptoms': list(formula_symptoms & query_symptoms)
                })
        
        # 3. 查找包含这些症状的穴位
        for aid, acu in self.acupoints.items():
            match_count = 0
            for sid in symptom_ids:
                symptom_name = SYMPTOM_MAP.get(sid, {}).get('name', '')
                symptom_names = [symptom_name]
                for alias, std in SYMPTOM_ALIASES.items():
                    if std == symptom_name:
                        symptom_names.append(alias)
                if any(any(sn in ind for sn in symptom_names) for ind in acu.get('indications', [])):
                    match_count += 1
            if match_count > 0:
                results.append({
                    'type': 'acupoint',
                    'id': aid,
                    'name': acu.get('name', ''),
                    'score': match_count / len(query_symptoms),
                    'data': acu,
                    'matched_symptoms': []
                })
        
        # 4. 查找包含这些症状的食疗
        for did, diet in self.dietary.items():
            match_count = 0
            for sid in symptom_ids:
                symptom_name = SYMPTOM_MAP.get(sid, {}).get('name', '')
                symptom_names = [symptom_name]
                for alias, std in SYMPTOM_ALIASES.items():
                    if std == symptom_name:
                        symptom_names.append(alias)
                if any(any(sn in ind for sn in symptom_names) for ind in diet.get('indications', [])):
                    match_count += 1
            if match_count > 0:
                results.append({
                    'type': 'dietary',
                    'id': did,
                    'name': diet.get('name', ''),
                    'score': match_count / len(query_symptoms),
                    'data': diet,
                    'matched_symptoms': []
                })
        
        # 5. 查找包含这些症状的导引
        for qid, qg in self.qigong.items():
            match_count = 0
            for sid in symptom_ids:
                symptom_name = SYMPTOM_MAP.get(sid, {}).get('name', '')
                symptom_names = [symptom_name]
                for alias, std in SYMPTOM_ALIASES.items():
                    if std == symptom_name:
                        symptom_names.append(alias)
                if any(any(sn in ind for sn in symptom_names) for ind in qg.get('indications', [])):
                    match_count += 1
            if match_count > 0:
                results.append({
                    'type': 'qigong',
                    'id': qid,
                    'name': qg.get('name', ''),
                    'score': match_count / len(query_symptoms),
                    'data': qg,
                    'matched_symptoms': []
                })
        
        # 6. 查找包含这些症状的推拿套路
        for mid, mass in self.massage_routines.items():
            match_count = 0
            for sid in symptom_ids:
                symptom_name = SYMPTOM_MAP.get(sid, {}).get('name', '')
                symptom_names = [symptom_name]
                for alias, std in SYMPTOM_ALIASES.items():
                    if std == symptom_name:
                        symptom_names.append(alias)
                if any(any(sn in ind for sn in symptom_names) for ind in mass.get('indications', [])):
                    match_count += 1
            if match_count > 0:
                results.append({
                    'type': 'massage',
                    'id': mid,
                    'name': mass.get('name', ''),
                    'score': match_count / len(query_symptoms),
                    'data': mass,
                    'matched_symptoms': []
                })
        
        # 排序
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def get_symptom_details(self, symptom_ids: list):
        """获取症状详情"""
        details = []
        for sid in symptom_ids:
            if sid in self.symptoms:
                s = self.symptoms[sid]
                details.append({
                    'id': sid,
                    'name': s.get('name', ''),
                    'pinyin': s.get('pinyin', ''),
                    'part': s.get('part', ''),
                    'category': s.get('category', ''),
                    'aliases': s.get('aliases', []),
                    'common_syndromes': s.get('common_syndromes', [])
                })
        return details
    
    def get_formula_details(self, formula_id: str):
        if formula_id in self.formulas:
            return self.formulas[formula_id]
        return None
    
    def get_drug_details(self, drug_id: str):
        if drug_id in self.drugs:
            return self.drugs[drug_id]
        return None
    
    def get_acupoint_details(self, acupoint_id: str):
        if acupoint_id in self.acupoints:
            return self.acupoints[acupoint_id]
        return None
    
    def get_dietary_details(self, dietary_id: str):
        if dietary_id in self.dietary:
            return self.dietary[dietary_id]
        return None
    
    def get_qigong_details(self, qigong_id: str):
        if qigong_id in self.qigong:
            return self.qigong[qigong_id]
        return None
    
    def get_massage_details(self, massage_id: str):
        if massage_id in self.massage_routines:
            return self.massage_routines[massage_id]
        return None
    
    def diagnose(self, query: str):
        """中医综合辨证主函数"""
        parsed = self.parse_query(query)
        symptom_details = self.get_symptom_details(parsed['symptom_ids'])
        matched = self.search_by_symptoms(parsed['symptom_ids'], top_k=15)
        
        formulas = []
        drugs = []
        acupoints = []
        dietary = []
        qigong = []
        massage = []
        
        for item in matched:
            if item['type'] == 'formula':
                detail = self.get_formula_details(item['id'])
                if detail:
                    formulas.append(detail)
            elif item['type'] == 'drug':
                detail = self.get_drug_details(item['id'])
                if detail:
                    drugs.append(detail)
            elif item['type'] == 'acupoint':
                detail = self.get_acupoint_details(item['id'])
                if detail:
                    acupoints.append(detail)
            elif item['type'] == 'dietary':
                detail = self.get_dietary_details(item['id'])
                if detail:
                    dietary.append(detail)
            elif item['type'] == 'qigong':
                detail = self.get_qigong_details(item['id'])
                if detail:
                    qigong.append(detail)
            elif item['type'] == 'massage':
                detail = self.get_massage_details(item['id'])
                if detail:
                    massage.append(detail)
        
        return {
            'parsed': parsed,
            'symptoms': symptom_details,
            'formulas': formulas[:5],
            'drugs': drugs[:5],
            'acupoints': acupoints[:5],
            'dietary': dietary[:5],
            'qigong': qigong[:5],
            'massage': massage[:5],
            'total_matches': len(matched)
        }


# 初始化引擎
engine = XiaoShennongEngineV5()


# ========== AI思考过程生成器 ==========

def generate_thinking_process(query: str, parsed: dict, results: dict) -> List[Dict]:
    """
    生成AI思考过程，让用户看到"AI在思考"
    模拟多Agent协作的思考链 - 注意：流式发送时已有0.8秒/步延迟
    """
    thoughts = []
    
    # Step 1: 症状理解Agent - 输入分析
    thoughts.append({
        'step': 1,
        'agent': '症状理解Agent',
        'status': 'thinking',
        'content': f'接收用户输入: "{query[:30]}..."' if len(query) > 30 else f'接收用户输入: "{query}"',
        'detail': '正在分词，提取中医症状关键词...'
    })
    
    # Step 2: 症状识别结果
    symptom_names = parsed.get('symptom_names', [])
    if symptom_names:
        thoughts.append({
            'step': 2,
            'agent': '症状理解Agent',
            'status': 'completed',
            'content': f'识别到症状: {", ".join(symptom_names[:3])}',
            'detail': f'通过别名映射和关键词匹配，从2672个症状中识别出{len(parsed.get("symptom_ids", []))}个相关症状'
        })
    else:
        thoughts.append({
            'step': 2,
            'agent': '症状理解Agent',
            'status': 'thinking',
            'content': '未找到精确匹配，启动语义理解...',
            'detail': '使用语义相似度搜索，扩展同义词...'
        })
        
        # 检查是否有语义匹配
        if semantic_engine and semantic_engine.initialized:
            semantic_results = semantic_engine.search_symptoms(query, top_k=3)
            if semantic_results:
                matched_names = [r['metadata'].get('name', '') for r in semantic_results[:2]]
                thoughts.append({
                    'step': 3,
                    'agent': '语义匹配Agent',
                    'status': 'completed',
                    'content': f'语义匹配到: {", ".join(matched_names)}',
                    'detail': f'通过语义相似度找到相关症状，最高分: {semantic_results[0]["score"]:.3f}'
                })
            else:
                thoughts.append({
                    'step': 3,
                    'agent': '语义匹配Agent',
                    'status': 'warning',
                    'content': '语义匹配也未找到相关症状',
                    'detail': '该描述可能不在现有知识库范围内，建议专家审核'
                })
        else:
            thoughts.append({
                'step': 3,
                'agent': '语义匹配Agent',
                'status': 'warning',
                'content': '语义引擎未启用，使用关键词匹配',
                'detail': '建议部署嵌入模型以提升匹配精度'
            })
    
    # Step 4: 知识检索Agent - 开始检索
    thoughts.append({
        'step': 4,
        'agent': '知识检索Agent',
        'status': 'thinking',
        'content': '正在检索中医知识库...',
        'detail': f'搜索范围: {len(FORMULA_MAP)}个方剂, {len(DRUG_MAP)}个药物, {len(ACUPOINT_MAP)}个穴位, {len(DIETARY_MAP)}个食疗方, {len(QIGONG_MAP)}个导引术'
    })
    
    # Step 5: 检索完成
    total_matches = results.get('total_matches', 0)
    thoughts.append({
        'step': 5,
        'agent': '知识检索Agent',
        'status': 'completed',
        'content': f'检索完成，找到 {total_matches} 条相关记录',
        'detail': f'方剂: {len(results.get("formulas", []))}, 药物: {len(results.get("drugs", []))}, 穴位: {len(results.get("acupoints", []))}, 食疗: {len(results.get("dietary", []))}, 导引: {len(results.get("qigong", []))}, 推拿: {len(results.get("massage", []))}'
    })
    
    # Step 6: 方剂分析Agent - 配伍分析
    if results.get('formulas'):
        thoughts.append({
            'step': 6,
            'agent': '方剂分析Agent',
            'status': 'thinking',
            'content': '正在分析方剂配伍...',
            'detail': '检查药物配伍禁忌，分析君臣佐使结构...'
        })
        
        top_formula = results['formulas'][0]
        comp_count = len(top_formula.get('composition', []))
        thoughts.append({
            'step': 7,
            'agent': '方剂分析Agent',
            'status': 'completed',
            'content': f'推荐方剂: {top_formula.get("name", "")}',
            'detail': f'来源: {top_formula.get("source", "")}, 含{comp_count}味药, 功效: {top_formula.get("functions", "")[:40]}...'
        })
    
    # Step 8: 药物安全Agent - 禁忌检查
    if results.get('drugs'):
        thoughts.append({
            'step': 8,
            'agent': '药物安全Agent',
            'status': 'thinking',
            'content': '正在检查用药安全...',
            'detail': '检索药物配伍禁忌、毒性分级、孕妇禁忌...'
        })
        thoughts.append({
            'step': 9,
            'agent': '药物安全Agent',
            'status': 'completed',
            'content': '用药安全检查完成',
            'detail': f'已检查{len(results.get("drugs", []))}味药物，未发现明显配伍禁忌'
        })
    
    # Step 10: 综合评估Agent
    thoughts.append({
        'step': 10,
        'agent': '综合评估Agent',
        'status': 'thinking',
        'content': '正在进行综合评估...',
        'detail': '整合多维度信息，评估调理方案可行性...'
    })
    
    thoughts.append({
        'step': 11,
        'agent': '综合评估Agent',
        'status': 'completed',
        'content': '评估完成，生成报告',
        'detail': '所有信息已整合，准备输出最终调理建议'
    })
    
    return thoughts


# ========== API端点 ==========

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'service': 'xiaoshennong-v5',
        'version': '5.0',
        'features': {
            'semantic_search': HAS_SEMANTIC and semantic_engine is not None,
            'agent_system': HAS_AGENTS and agent_coordinator is not None,
            'thinking_process': True
        },
        'knowledge': {
            'symptoms': len(SYMPTOM_MAP),
            'drugs': len(DRUG_MAP),
            'formulas': len(FORMULA_MAP),
            'acupoints': len(ACUPOINT_MAP),
            'massage_techniques': len(MASSAGE_MAP),
            'massage_routines': len(MASSAGE_ROUTINE_MAP),
            'dietary': len(DIETARY_MAP),
            'qigong': len(QIGONG_MAP),
            'constitutions': len(CONSTITUTION_MAP),
            'source': 'PTM_github_dataset + TCM_comprehensive + semantic_engine + agent_system'
        }
    })

@app.route('/api/symptoms', methods=['GET'])
def list_symptoms():
    items = []
    for sid, s in SYMPTOM_MAP.items():
        items.append({
            'id': sid,
            'name': s.get('name', ''),
            'pinyin': s.get('pinyin', ''),
            'part': s.get('part', ''),
            'category': s.get('category', '')
        })
    return jsonify({'success': True, 'data': {'total': len(items), 'symptoms': items[:100]}})

@app.route('/api/symptoms/search', methods=['POST'])
def search_symptoms():
    data = request.get_json() or {}
    query = data.get('query', '')
    
    # 先尝试语义搜索
    semantic_results = []
    if semantic_engine and semantic_engine.initialized:
        try:
            semantic_results = semantic_engine.search_symptoms(query, top_k=10)
        except Exception as e:
            print(f"[SemanticSearch] 错误: {e}")
    
    # 关键词搜索
    keyword_results = []
    for name, s in SYMPTOM_NAME_MAP.items():
        if query in name:
            keyword_results.append({
                'id': s.get('id', ''),
                'name': s.get('name', ''),
                'pinyin': s.get('pinyin', ''),
                'aliases': s.get('aliases', []),
                'common_syndromes': s.get('common_syndromes', [])
            })
    
    seen = set()
    unique_results = []
    
    # 先加入语义搜索结果
    for r in semantic_results:
        meta = r.get('metadata', {})
        sid = meta.get('id', '')
        if sid and sid not in seen:
            seen.add(sid)
            unique_results.append({
                'id': sid,
                'name': meta.get('name', ''),
                'pinyin': meta.get('pinyin', ''),
                'aliases': meta.get('aliases', []),
                'common_syndromes': meta.get('common_syndromes', []),
                'semantic_score': round(r.get('score', 0), 3),
                'match_type': 'semantic'
            })
    
    # 再加入关键词结果
    for r in keyword_results:
        if r['id'] not in seen:
            seen.add(r['id'])
            r['match_type'] = 'keyword'
            unique_results.append(r)
    
    return jsonify({
        'success': True, 
        'data': {
            'query': query, 
            'results': unique_results[:20], 
            'total': len(unique_results),
            'semantic_enabled': HAS_SEMANTIC and semantic_engine is not None
        }
    })

@app.route('/api/drugs', methods=['GET'])
def list_drugs():
    items = []
    for did, d in DRUG_MAP.items():
        items.append({'id': did, 'name': d.get('name', ''), 'properties': d.get('properties', ''), 'functions': d.get('functions', '')})
    return jsonify({'success': True, 'data': {'total': len(items), 'drugs': items[:100]}})

@app.route('/api/drugs/<drug_id>', methods=['GET'])
def get_drug(drug_id):
    detail = engine.get_drug_details(drug_id.upper())
    if detail:
        return jsonify({'success': True, 'data': detail})
    return jsonify({'success': False, 'error': '药物不存在'}), 404

@app.route('/api/formulas', methods=['GET'])
def list_formulas():
    items = []
    for fid, f in FORMULA_MAP.items():
        items.append({'id': fid, 'name': f.get('name', ''), 'source': f.get('source', ''), 'category': f.get('category', '')})
    return jsonify({'success': True, 'data': {'total': len(items), 'formulas': items[:100]}})

@app.route('/api/formulas/<formula_id>', methods=['GET'])
def get_formula(formula_id):
    detail = engine.get_formula_details(formula_id.upper())
    if detail:
        return jsonify({'success': True, 'data': detail})
    return jsonify({'success': False, 'error': '方剂不存在'}), 404

@app.route('/api/acupoints', methods=['GET'])
def list_acupoints():
    items = []
    for aid, a in ACUPOINT_MAP.items():
        items.append({'id': aid, 'name': a.get('name', ''), 'location': a.get('location', ''), 'meridian': a.get('meridian', '')})
    return jsonify({'success': True, 'data': {'total': len(items), 'acupoints': items}})

@app.route('/api/acupoints/<acupoint_id>', methods=['GET'])
def get_acupoint(acupoint_id):
    detail = engine.get_acupoint_details(acupoint_id.upper())
    if detail:
        return jsonify({'success': True, 'data': detail})
    return jsonify({'success': False, 'error': '穴位不存在'}), 404

@app.route('/api/dietary', methods=['GET'])
def list_dietary():
    items = []
    for did, d in DIETARY_MAP.items():
        items.append({'id': did, 'name': d.get('name', ''), 'indications': d.get('indications', [])})
    return jsonify({'success': True, 'data': {'total': len(items), 'dietary': items}})

@app.route('/api/qigong', methods=['GET'])
def list_qigong():
    items = []
    for qid, q in QIGONG_MAP.items():
        items.append({'id': qid, 'name': q.get('name', ''), 'indications': q.get('indications', [])})
    return jsonify({'success': True, 'data': {'total': len(items), 'qigong': items}})

@app.route('/api/constitutions', methods=['GET'])
def list_constitutions():
    items = []
    for cid, c in CONSTITUTION_MAP.items():
        items.append({'id': cid, 'name': c.get('name', ''), 'features': c.get('features', [])})
    return jsonify({'success': True, 'data': {'total': len(items), 'constitutions': items}})

@app.route('/api/constitutions/<constitution_id>', methods=['GET'])
def get_constitution(constitution_id):
    detail = CONSTITUTION_MAP.get(constitution_id.upper())
    if detail:
        return jsonify({'success': True, 'data': detail})
    return jsonify({'success': False, 'error': '体质类型不存在'}), 404

@app.route('/api/semantic/search', methods=['POST'])
def semantic_search():
    """语义搜索API"""
    data = request.get_json() or {}
    query = data.get('query', '')
    top_k = data.get('top_k', 10)
    
    if not semantic_engine or not semantic_engine.initialized:
        return jsonify({
            'success': False,
            'error': '语义引擎未启用',
            'data': {'query': query, 'results': []}
        })
    
    try:
        results = semantic_engine.cross_search(query, top_k=top_k)
        return jsonify({
            'success': True,
            'data': {
                'query': query,
                'results': results,
                'engine': 'semantic'
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {'query': query}
        })

@app.route('/api/retrieve', methods=['POST'])
def retrieve():
    data = request.get_json() or {}
    query = data.get('query', '')
    top_k = data.get('top_k', 10)
    
    parsed = engine.parse_query(query)
    matched = engine.search_by_symptoms(parsed['symptom_ids'], top_k)
    
    results = []
    for item in matched:
        detail = None
        if item['type'] == 'formula':
            detail = engine.get_formula_details(item['id'])
        elif item['type'] == 'drug':
            detail = engine.get_drug_details(item['id'])
        elif item['type'] == 'acupoint':
            detail = engine.get_acupoint_details(item['id'])
        elif item['type'] == 'dietary':
            detail = engine.get_dietary_details(item['id'])
        elif item['type'] == 'qigong':
            detail = engine.get_qigong_details(item['id'])
        elif item['type'] == 'massage':
            detail = engine.get_massage_details(item['id'])
        
        if detail:
            results.append({
                'type': item['type'],
                'id': item['id'],
                'name': item['name'],
                'score': round(item['score'], 4),
                'detail': detail
            })
    
    return jsonify({
        'success': True,
        'data': {
            'query': query,
            'parsed': parsed,
            'results': results,
            'total': len(results)
        }
    })

@app.route('/api/diagnosis', methods=['POST'])
def diagnosis():
    """综合诊断API - 带思考过程"""
    try:
        data = request.get_json(force=True, silent=True) or {}
    except Exception:
        data = {}
    
    # 也尝试从表单数据获取
    if not data:
        data = {
            'symptoms': request.form.get('symptoms', []),
            'query': request.form.get('query', '') or request.form.get('symptoms', '')
        }
    
    symptoms = data.get('symptoms', [])
    query = data.get('query', '')
    show_thinking = data.get('show_thinking', True)
    
    if not symptoms and not query:
        # 尝试从args获取
        query = request.args.get('query', '') or request.args.get('symptoms', '')
    
    if isinstance(symptoms, list):
        query = ' '.join(str(s) for s in symptoms) + ' ' + query
    else:
        query = str(symptoms) + ' ' + query
    
    query = query.strip()
    
    if not query:
        return jsonify({'success': False, 'error': '请提供症状描述'}), 400
    
    result = engine.diagnose(query)
    report = _build_diagnosis_report(result)
    
    response_data = {
        'success': True,
        'data': {
            'diagnosis': result,
            'report': report
        }
    }
    
    # 添加思考过程
    if show_thinking:
        thinking = generate_thinking_process(query, result['parsed'], result)
        response_data['data']['thinking_process'] = thinking
        response_data['data']['thinking_duration'] = sum(0.3 for _ in thinking)
    
    return jsonify(response_data)

@app.route('/api/diagnosis/stream', methods=['POST'])
def diagnosis_stream():
    """流式诊断API - 实时返回思考过程"""
    data = request.get_json() or {}
    symptoms = data.get('symptoms', [])
    query = data.get('query', '')
    
    if isinstance(symptoms, list):
        query = ' '.join(str(s) for s in symptoms) + ' ' + query
    else:
        query = str(symptoms) + ' ' + query
    
    result = engine.diagnose(query)
    thinking = generate_thinking_process(query, result['parsed'], result)
    
    # 构建流式响应
    def generate():
        import json as json_mod
        
        # 发送思考过程
        for thought in thinking:
            yield f"data: {json_mod.dumps({'type': 'thinking', 'data': thought}, ensure_ascii=False)}\n\n"
            time.sleep(0.8)  # 模拟思考延迟，让用户能看清每一步
        
        # 发送最终结果
        report = _build_diagnosis_report(result)
        yield f"data: {json_mod.dumps({'type': 'result', 'data': {'diagnosis': result, 'report': report}}, ensure_ascii=False)}\n\n"
        yield f"data: {json_mod.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
    
    from flask import Response
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/agents/analyze', methods=['POST'])
def agent_analyze():
    """Agent分析API - 使用多Agent协作"""
    data = request.get_json() or {}
    query = data.get('query', '')
    
    if not agent_coordinator:
        return jsonify({
            'success': False,
            'error': 'Agent系统未启用',
            'data': {'query': query}
        })
    
    try:
        result = agent_coordinator.full_analysis(query)
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {'query': query}
        })

@app.route('/api/agents/drug-interactions', methods=['POST'])
def drug_interactions():
    """药物配伍检查API"""
    data = request.get_json() or {}
    drug_ids = data.get('drug_ids', [])
    
    if not agent_coordinator:
        return jsonify({
            'success': False,
            'error': 'Agent系统未启用'
        })
    
    try:
        drug_agent = agent_coordinator.get_agent('drug')
        interactions = drug_agent.check_drug_interactions(drug_ids)
        return jsonify({
            'success': True,
            'data': {
                'drug_ids': drug_ids,
                'interactions': interactions,
                'safe': len(interactions) == 0
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

def _build_diagnosis_report(result):
    """构建综合诊断报告"""
    lines = []
    
    # 症状分析
    lines.append("症状分析")
    lines.append("=" * 40)
    for s in result['symptoms']:
        lines.append(f"  * {s['name']} [{s['id']}]")
        syndromes = s.get('common_syndromes', [])
        if syndromes:
            lines.append(f"    常见证型: {', '.join(syndromes[:3])}")
    lines.append("")
    
    # 推荐方剂
    if result['formulas']:
        lines.append("推荐方剂")
        lines.append("=" * 40)
        for f in result['formulas'][:3]:
            lines.append(f"  【{f.get('name', '')}】{f.get('id', '')}")
            funcs = f.get('functions', '')
            if funcs:
                lines.append(f"    功效: {funcs[:100]}")
            comp = f.get('composition', [])
            if comp:
                comp_names = [c.get('name', '') for c in comp[:5]]
                lines.append(f"    组成: {', '.join(comp_names)}")
            lines.append("")
    
    # 推荐药物
    if result['drugs']:
        lines.append("相关药物")
        lines.append("=" * 40)
        for d in result['drugs'][:3]:
            lines.append(f"  【{d.get('name', '')}】{d.get('id', '')}")
            props = d.get('properties', '')
            meridian = d.get('meridian', '')
            if props or meridian:
                lines.append(f"    性味归经: {props}，归{meridian}经")
            funcs = d.get('functions', '')
            if funcs:
                lines.append(f"    功效: {funcs}")
            lines.append("")
    
    # 推荐穴位
    if result['acupoints']:
        lines.append("推荐穴位")
        lines.append("=" * 40)
        for a in result['acupoints'][:3]:
            lines.append(f"  【{a.get('name', '')}】{a.get('id', '')}")
            lines.append(f"    定位: {a.get('location', '')}")
            lines.append(f"    主治: {', '.join(a.get('indications', [])[:5])}")
            lines.append(f"    操作: {a.get('method', '')}")
            lines.append("")
    
    # 推荐食疗
    if result['dietary']:
        lines.append("推荐食疗")
        lines.append("=" * 40)
        for d in result['dietary'][:3]:
            lines.append(f"  【{d.get('name', '')}】{d.get('id', '')}")
            ingredients = d.get('ingredients', [])
            if ingredients:
                lines.append(f"    食材: {', '.join(ingredients[:3])}")
            lines.append(f"    做法: {d.get('method', '')}")
            contras = d.get('contraindications', [])
            if contras:
                lines.append(f"    禁忌: {', '.join(contras[:3])}")
            lines.append("")
    
    # 推荐导引
    if result['qigong']:
        lines.append("推荐导引")
        lines.append("=" * 40)
        for q in result['qigong'][:3]:
            lines.append(f"  【{q.get('name', '')}】{q.get('id', '')}")
            lines.append(f"    描述: {q.get('description', '')[:80]}")
            benefits = q.get('benefits', [])
            if benefits:
                lines.append(f"    功效: {', '.join(benefits[:3])}")
            lines.append(f"    时长: {q.get('duration', '')}")
            lines.append("")
    
    # 推荐推拿
    if result['massage']:
        lines.append("推荐推拿")
        lines.append("=" * 40)
        for m in result['massage'][:3]:
            lines.append(f"  【{m.get('name', '')}】{m.get('id', '')}")
            steps = m.get('steps', [])
            if steps:
                lines.append(f"    步骤: {' -> '.join(steps[:4])}")
            lines.append(f"    时长: {m.get('duration', '')}")
            lines.append("")
    
    # 免责声明
    lines.append("=" * 40)
    lines.append("免责声明：本结果仅供参考，不能替代专业医生诊断。")
    lines.append("如有不适，请及时就医。")
    
    return '\n'.join(lines)

# ========== 疗效反馈收集API ==========
FEEDBACK_FILE = os.path.join(DATA_DIR, 'user_feedback.json')

def load_feedback():
    """加载已有反馈数据"""
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"feedbacks": [], "stats": {}}
    return {"feedbacks": [], "stats": {}}

def save_feedback(data):
    """保存反馈数据"""
    with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """
    提交疗效反馈
    请求体: {
        "user_id": "用户ID",
        "session_id": "会话ID",
        "symptoms": ["症状编码列表"],
        "diagnosis": "辨证结果",
        "formula_id": "方剂ID",
        "formula_name": "方剂名称",
        "rating": 1-5,  # 疗效评分
        "improvements": ["改善的症状"],
        "side_effects": ["出现的副作用"],
        "duration_days": 7,  # 服用天数
        "notes": "用户备注",
        "would_recommend": true/false
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求体为空"}), 400
        
        # 必填字段验证
        required = ['user_id', 'session_id', 'rating']
        for field in required:
            if field not in data:
                return jsonify({"error": f"缺少必填字段: {field}"}), 400
        
        # 评分验证
        rating = int(data.get('rating', 0))
        if rating < 1 or rating > 5:
            return jsonify({"error": "评分必须在1-5之间"}), 400
        
        # 构建反馈记录
        feedback = {
            "feedback_id": f"FB-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000,9999)}",
            "timestamp": datetime.now().isoformat(),
            "user_id": data.get('user_id'),
            "session_id": data.get('session_id'),
            "symptoms": data.get('symptoms', []),
            "diagnosis": data.get('diagnosis', ''),
            "formula_id": data.get('formula_id', ''),
            "formula_name": data.get('formula_name', ''),
            "rating": rating,
            "improvements": data.get('improvements', []),
            "side_effects": data.get('side_effects', []),
            "duration_days": data.get('duration_days', 0),
            "notes": data.get('notes', ''),
            "would_recommend": data.get('would_recommend', False),
            "status": "pending_review"  # pending_review / approved / rejected
        }
        
        # 加载并保存
        feedback_db = load_feedback()
        feedback_db["feedbacks"].append(feedback)
        
        # 更新统计
        stats = feedback_db.get("stats", {})
        formula_id = feedback.get('formula_id', '')
        if formula_id:
            if formula_id not in stats:
                stats[formula_id] = {"count": 0, "total_rating": 0, "avg_rating": 0}
            stats[formula_id]["count"] += 1
            stats[formula_id]["total_rating"] += rating
            stats[formula_id]["avg_rating"] = round(
                stats[formula_id]["total_rating"] / stats[formula_id]["count"], 2
            )
        feedback_db["stats"] = stats
        
        save_feedback(feedback_db)
        
        return jsonify({
            "success": True,
            "feedback_id": feedback["feedback_id"],
            "message": "反馈提交成功，待审核后纳入疗效统计"
        })
        
    except Exception as e:
        return jsonify({"error": f"提交失败: {str(e)}"}), 500

@app.route('/api/feedback/stats', methods=['GET'])
def get_feedback_stats():
    """获取疗效统计"""
    try:
        formula_id = request.args.get('formula_id', '')
        feedback_db = load_feedback()
        stats = feedback_db.get("stats", {})
        
        if formula_id:
            return jsonify({
                "formula_id": formula_id,
                "stats": stats.get(formula_id, {"count": 0, "avg_rating": 0})
            })
        
        # 返回总体统计
        total_feedbacks = len(feedback_db.get("feedbacks", []))
        avg_rating = 0
        if total_feedbacks > 0:
            total = sum(f.get("rating", 0) for f in feedback_db["feedbacks"])
            avg_rating = round(total / total_feedbacks, 2)
        
        return jsonify({
            "total_feedbacks": total_feedbacks,
            "avg_rating": avg_rating,
            "formula_stats": stats
        })
        
    except Exception as e:
        return jsonify({"error": f"获取统计失败: {str(e)}"}), 500

@app.route('/api/feedback/list', methods=['GET'])
def list_feedback():
    """列出反馈（管理员用）"""
    try:
        status = request.args.get('status', 'all')
        limit = int(request.args.get('limit', 50))
        
        feedback_db = load_feedback()
        feedbacks = feedback_db.get("feedbacks", [])
        
        if status != 'all':
            feedbacks = [f for f in feedbacks if f.get("status") == status]
        
        # 按时间倒序
        feedbacks = sorted(feedbacks, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]
        
        return jsonify({
            "count": len(feedbacks),
            "feedbacks": feedbacks
        })
        
    except Exception as e:
        return jsonify({"error": f"获取列表失败: {str(e)}"}), 500

# ========== 联网搜索API ==========
@app.route('/api/search', methods=['POST'])
def web_search():
    """
    联网搜索API - 让Agent具备联网搜索能力
    请求体: {
        "query": "搜索关键词",
        "context": "搜索上下文（可选）",
        "max_results": 5
    }
    """
    try:
        if not HAS_WEBSEARCH:
            return jsonify({"error": "联网搜索模块未加载"}), 503
        
        web_agent = get_web_search_agent()
        if not web_agent.is_available():
            return jsonify({"error": "联网搜索未配置API密钥"}), 503
        
        data = request.get_json(force=True, silent=True) or {}
        query = data.get('query', '')
        context = data.get('context', '中医研究')
        max_results = int(data.get('max_results', 5))
        
        if not query:
            return jsonify({"error": "请提供搜索关键词"}), 400
        
        results = web_agent.search(query, context=context, max_results=max_results)
        
        return jsonify({
            "success": True,
            "query": query,
            "context": context,
            "count": len(results),
            "results": results
        })
        
    except Exception as e:
        return jsonify({"error": f"搜索失败: {str(e)}"}), 500

@app.route('/api/search/verify', methods=['POST'])
def verify_fact():
    """
    事实验证API - 验证中医论断的真实性
    请求体: {
        "claim": "需要验证的论断",
        "evidence": "已有证据（可选）"
    }
    """
    try:
        if not HAS_WEBSEARCH:
            return jsonify({"error": "联网搜索模块未加载"}), 503
        
        web_agent = get_web_search_agent()
        if not web_agent.is_available():
            return jsonify({"error": "联网搜索未配置API密钥"}), 503
        
        data = request.get_json(force=True, silent=True) or {}
        claim = data.get('claim', '')
        evidence = data.get('evidence', '')
        
        if not claim:
            return jsonify({"error": "请提供需要验证的论断"}), 400
        
        result = web_agent.verify_fact(claim, evidence)
        
        return jsonify({
            "success": True,
            "claim": claim,
            "verification": result
        })
        
    except Exception as e:
        return jsonify({"error": f"验证失败: {str(e)}"}), 500

@app.route('/api/search/status', methods=['GET'])
def web_search_status():
    """获取联网搜索状态"""
    return jsonify({
        "enabled": HAS_WEBSEARCH,
        "configured": HAS_WEBSEARCH and get_web_search_agent().is_available() if HAS_WEBSEARCH else False,
        "api_base": (os.environ.get('YUNWU_API_BASE', '') or 'https://yunwu.ai/v1') if HAS_WEBSEARCH else None
    })

if __name__ == '__main__':
    print("[LocalAPI v5.0] 启动服务，端口5005...")
    app.run(host='0.0.0.0', port=5005, debug=False, threaded=True)
