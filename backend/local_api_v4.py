#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小神农中医AI - 本地API v4.0 (综合版)
支持：中药方剂、针灸、推拿、食疗、导引、体质辨识
"""

import json
import os
import re
from flask import Flask, request, jsonify
from flask_cors import CORS

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
    print(f"[LocalAPI v4.0] 症状: {len(SYMPTOM_MAP)} 条")
except Exception as e:
    print(f"[LocalAPI v4.0] 症状加载失败: {e}")

# 加载药物数据
DRUG_MAP = {}
DRUG_NAME_MAP = {}

try:
    with open(os.path.join(DATA_DIR, 'drug_codes_v3_full.json'), 'r', encoding='utf-8') as f:
        drug_data = json.load(f)
        for d in drug_data.get('drugs', []):
            DRUG_MAP[d['id']] = d
            DRUG_NAME_MAP[d['name']] = d
    print(f"[LocalAPI v4.0] 药物: {len(DRUG_MAP)} 条")
except Exception as e:
    print(f"[LocalAPI v4.0] 药物加载失败: {e}")

# 加载方剂数据
FORMULA_MAP = {}
FORMULA_NAME_MAP = {}

try:
    with open(os.path.join(DATA_DIR, 'formula_codes_v3_5k.json'), 'r', encoding='utf-8') as f:
        formula_data = json.load(f)
        FORMULA_MAP = {f['id']: f for f in formula_data.get('formulas', [])}
        FORMULA_NAME_MAP = {f['name']: f for f in formula_data.get('formulas', [])}
    print(f"[LocalAPI v4.0] 方剂: {len(FORMULA_MAP)} 条")
except Exception as e:
    print(f"[LocalAPI v4.0] 方剂加载失败: {e}")

# 加载针灸数据
ACUPOINT_MAP = {}
ACUPOINT_NAME_MAP = {}

try:
    with open(os.path.join(DATA_DIR, 'acupuncture_db.json'), 'r', encoding='utf-8') as f:
        acu_data = json.load(f)
        for a in acu_data.get('acupoints', []):
            ACUPOINT_MAP[a['id']] = a
            ACUPOINT_NAME_MAP[a['name']] = a
    print(f"[LocalAPI v4.0] 穴位: {len(ACUPOINT_MAP)} 条")
except Exception as e:
    print(f"[LocalAPI v4.0] 穴位加载失败: {e}")

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
    print(f"[LocalAPI v4.0] 推拿: {len(MASSAGE_MAP)} 手法, {len(MASSAGE_ROUTINE_MAP)} 套路")
except Exception as e:
    print(f"[LocalAPI v4.0] 推拿加载失败: {e}")

# 加载食疗数据
DIETARY_MAP = {}

try:
    with open(os.path.join(DATA_DIR, 'dietary_db.json'), 'r', encoding='utf-8') as f:
        diet_data = json.load(f)
        for d in diet_data.get('dietary_therapies', []):
            DIETARY_MAP[d['id']] = d
    print(f"[LocalAPI v4.0] 食疗: {len(DIETARY_MAP)} 条")
except Exception as e:
    print(f"[LocalAPI v4.0] 食疗加载失败: {e}")

# 加载导引数据
QIGONG_MAP = {}

try:
    with open(os.path.join(DATA_DIR, 'qigong_db.json'), 'r', encoding='utf-8') as f:
        qg_data = json.load(f)
        for q in qg_data.get('qigong_routines', []):
            QIGONG_MAP[q['id']] = q
    print(f"[LocalAPI v4.0] 导引: {len(QIGONG_MAP)} 条")
except Exception as e:
    print(f"[LocalAPI v4.0] 导引加载失败: {e}")

# 加载体质数据
CONSTITUTION_MAP = {}
CONSTITUTION_NAME_MAP = {}

try:
    with open(os.path.join(DATA_DIR, 'constitution_db.json'), 'r', encoding='utf-8') as f:
        const_data = json.load(f)
        for c in const_data.get('constitutions', []):
            CONSTITUTION_MAP[c['id']] = c
            CONSTITUTION_NAME_MAP[c['name']] = c
    print(f"[LocalAPI v4.0] 体质: {len(CONSTITUTION_MAP)} 种")
except Exception as e:
    print(f"[LocalAPI v4.0] 体质加载失败: {e}")

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
}

print(f"[LocalAPI v4.0] 加载完成:")
print(f"  症状: {len(SYMPTOM_MAP)} 条")
print(f"  药物: {len(DRUG_MAP)} 条")
print(f"  方剂: {len(FORMULA_MAP)} 条")
print(f"  穴位: {len(ACUPOINT_MAP)} 个")
print(f"  推拿: {len(MASSAGE_MAP)} 手法, {len(MASSAGE_ROUTINE_MAP)} 套路")
print(f"  食疗: {len(DIETARY_MAP)} 条")
print(f"  导引: {len(QIGONG_MAP)} 条")
print(f"  体质: {len(CONSTITUTION_MAP)} 种")

# ========== 核心检索引擎 ==========

class XiaoShennongEngineV4:
    """小神农中医AI检索引擎 v4.0 - 综合版"""
    
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
            acu_symptoms = set(acu.get('indications', []))
            match_count = 0
            for sid in symptom_ids:
                symptom_name = SYMPTOM_MAP.get(sid, {}).get('name', '')
                if symptom_name and any(symptom_name in ind for ind in acu_symptoms):
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
            diet_symptoms = set(diet.get('indications', []))
            match_count = 0
            for sid in symptom_ids:
                symptom_name = SYMPTOM_MAP.get(sid, {}).get('name', '')
                if symptom_name and any(symptom_name in ind for ind in diet_symptoms):
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
            qg_symptoms = set(qg.get('indications', []))
            match_count = 0
            for sid in symptom_ids:
                symptom_name = SYMPTOM_MAP.get(sid, {}).get('name', '')
                if symptom_name and any(symptom_name in ind for ind in qg_symptoms):
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
            mass_symptoms = set(mass.get('indications', []))
            match_count = 0
            for sid in symptom_ids:
                symptom_name = SYMPTOM_MAP.get(sid, {}).get('name', '')
                if symptom_name and any(symptom_name in ind for ind in mass_symptoms):
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
engine = XiaoShennongEngineV4()

# ========== API端点 ==========

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'service': 'xiaoshennong-v4',
        'version': '4.0',
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
            'source': 'PTM_github_dataset + TCM_comprehensive'
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
    results = []
    for name, s in SYMPTOM_NAME_MAP.items():
        if query in name:
            results.append({
                'id': s.get('id', ''),
                'name': s.get('name', ''),
                'pinyin': s.get('pinyin', ''),
                'aliases': s.get('aliases', []),
                'common_syndromes': s.get('common_syndromes', [])
            })
    seen = set()
    unique_results = []
    for r in results:
        if r['id'] not in seen:
            seen.add(r['id'])
            unique_results.append(r)
    return jsonify({'success': True, 'data': {'query': query, 'results': unique_results[:20], 'total': len(unique_results)}})

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
        items.append({'id': aid, 'name': a.get('name', ''), 'location': a.get('location', '')})
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
    data = request.get_json() or {}
    symptoms = data.get('symptoms', [])
    query = data.get('query', '')
    
    if isinstance(symptoms, list):
        query = ' '.join(str(s) for s in symptoms) + ' ' + query
    else:
        query = str(symptoms) + ' ' + query
    
    result = engine.diagnose(query)
    report = _build_diagnosis_report(result)
    
    return jsonify({
        'success': True,
        'data': {
            'diagnosis': result,
            'report': report
        }
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

if __name__ == '__main__':
    print("[LocalAPI v4.0] 启动服务，端口5004...")
    app.run(host='0.0.0.0', port=5004, debug=False)
