#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小神农中医AI - 本地API v3.0
整合GitHub PTM数据集: 2672症状, 1104药物, 98334方剂
支持编码查询和中文查询的完整RAG系统
"""

import json
import os
import re
import glob
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ========== 加载编码数据库 ==========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
KB_DIR = os.path.join(BASE_DIR, '..', '..', 'knowledge_base')  # 外部知识库

# 优先使用外部知识库，回退到内部数据
if os.path.exists(KB_DIR):
    SYMPTOMS_DIR = os.path.join(KB_DIR, 'symptoms')
    DRUGS_DIR = os.path.join(KB_DIR, 'drugs')
    FORMULAS_DIR = os.path.join(KB_DIR, 'formulas')
    USE_EXTERNAL_KB = True
    print(f"[LocalAPI v3.0] 使用外部知识库: {KB_DIR}")
else:
    USE_EXTERNAL_KB = False
    print(f"[LocalAPI v3.0] 使用内部数据: {DATA_DIR}")

# 加载症状数据
SYMPTOM_MAP = {}
SYMPTOM_NAME_MAP = {}

if USE_EXTERNAL_KB and os.path.exists(SYMPTOMS_DIR):
    symptom_files = glob.glob(os.path.join(SYMPTOMS_DIR, 'SN-*.json'))
    for fpath in symptom_files:
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            sid = data.get('id', '')
            name = data.get('name', '')
            if sid and name:
                SYMPTOM_MAP[sid] = data
                SYMPTOM_NAME_MAP[name] = data
else:
    # 回退到内部数据
    try:
        with open(os.path.join(DATA_DIR, 'symptom_codes_v2.json'), 'r', encoding='utf-8') as f:
            symptom_data = json.load(f)
            for s in symptom_data.get('symptoms', []):
                SYMPTOM_MAP[s['id']] = s
                SYMPTOM_NAME_MAP[s['name']] = s
                for alias in s.get('aliases', []):
                    SYMPTOM_NAME_MAP[alias] = s
    except:
        pass

# 加载药物数据
DRUG_MAP = {}
DRUG_NAME_MAP = {}

if USE_EXTERNAL_KB and os.path.exists(DRUGS_DIR):
    drug_files = glob.glob(os.path.join(DRUGS_DIR, 'DR-*.json'))
    for fpath in drug_files:
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            did = data.get('id', '')
            name = data.get('name', '')
            if did and name:
                DRUG_MAP[did] = data
                DRUG_NAME_MAP[name] = data
else:
    try:
        with open(os.path.join(DATA_DIR, 'drug_codes_v2.json'), 'r', encoding='utf-8') as f:
            drug_data = json.load(f)
            for d in drug_data.get('drugs', []):
                DRUG_MAP[d['id']] = d
                DRUG_NAME_MAP[d['name']] = d
    except:
        pass

# 加载方剂数据 (限制内存使用，只加载索引)
FORMULA_MAP = {}
FORMULA_NAME_MAP = {}

if USE_EXTERNAL_KB and os.path.exists(FORMULAS_DIR):
    # 对于大量方剂，只加载前5000个到内存，其余按需加载
    formula_files = sorted(glob.glob(os.path.join(FORMULAS_DIR, 'FP-*.json')))[:5000]
    for fpath in formula_files:
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            fid = data.get('id', '')
            name = data.get('name', '')
            if fid:
                FORMULA_MAP[fid] = data
                if name:
                    FORMULA_NAME_MAP[name] = data
    print(f"  方剂(内存加载前5000): {len(FORMULA_MAP)}")
else:
    try:
        with open(os.path.join(DATA_DIR, 'formula_codes_v2.json'), 'r', encoding='utf-8') as f:
            formula_data = json.load(f)
            for fm in formula_data.get('formulas', []):
                FORMULA_MAP[fm['id']] = fm
                FORMULA_NAME_MAP[fm['name']] = fm
    except:
        pass

print(f"[LocalAPI v3.0] 加载完成:")
print(f"  症状: {len(SYMPTOM_MAP)} 条")
print(f"  药物: {len(DRUG_MAP)} 条")
print(f"  方剂: {len(FORMULA_MAP)} 条(内存) + 磁盘缓存")

# ========== 核心检索引擎 ==========

class XiaoShennongEngineV3:
    """小神农中医AI检索引擎 v3.0"""
    
    def __init__(self):
        self.symptoms = SYMPTOM_MAP
        self.drugs = DRUG_MAP
        self.formulas = FORMULA_MAP
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
        
        # 1. 提取症状编码 (SN-XXX 或 SN-XX-XX-XXX)
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
        
        # 4. 中文症状名匹配 (优化性能：先分词再匹配)
        query_words = set(query)
        # 只匹配长度>=2的词，避免单字误匹配
        for name, symptom in self.symptom_name_map.items():
            if len(name) >= 2 and name in query:
                sid = symptom.get('id', '')
                if sid and sid not in result['symptom_ids']:
                    result['symptom_ids'].append(sid)
                    result['symptom_names'].append(name)
        
        # 5. 中文药物名匹配
        for name, drug in self.drug_name_map.items():
            if len(name) >= 2 and name in query:
                did = drug.get('id', '')
                if did and did not in result['drug_ids']:
                    result['drug_ids'].append(did)
                    result['drug_names'].append(name)
        
        # 6. 中文方剂名匹配
        for name, formula in self.formula_name_map.items():
            if len(name) >= 2 and name in query:
                fid = formula.get('id', '')
                if fid and fid not in result['formula_ids']:
                    result['formula_ids'].append(fid)
                    result['formula_names'].append(name)
        
        return result
    
    def search_by_symptoms(self, symptom_ids: list, top_k: int = 5):
        """根据症状编码检索相关方剂和药物"""
        results = []
        query_symptoms = set(symptom_ids)
        
        # 1. 查找包含这些症状的药物
        matched_drugs = []
        for did, drug in self.drugs.items():
            assoc_symptoms = set(drug.get('associated_symptoms', []))
            match_count = len(assoc_symptoms & query_symptoms)
            if match_count > 0:
                matched_drugs.append({
                    'type': 'drug',
                    'id': did,
                    'name': drug.get('name', ''),
                    'score': match_count / max(len(assoc_symptoms), len(query_symptoms)),
                    'data': drug,
                    'matched_symptoms': list(assoc_symptoms & query_symptoms)
                })
        
        # 2. 查找包含这些症状的方剂
        matched_formulas = []
        for fid, formula in self.formulas.items():
            target_symptoms = set(formula.get('target_symptoms', []))
            match_count = len(target_symptoms & query_symptoms)
            if match_count > 0:
                matched_formulas.append({
                    'type': 'formula',
                    'id': fid,
                    'name': formula.get('name', ''),
                    'score': match_count / max(len(target_symptoms), len(query_symptoms)),
                    'data': formula,
                    'matched_symptoms': list(target_symptoms & query_symptoms)
                })
        
        # 3. 合并排序
        all_results = matched_drugs + matched_formulas
        all_results.sort(key=lambda x: x['score'], reverse=True)
        
        return all_results[:top_k]
    
    def get_symptom_details(self, symptom_ids: list):
        """获取症状详情"""
        details = []
        for sid in symptom_ids:
            if sid in self.symptoms:
                s = self.symptoms[sid]
                details.append({
                    'id': sid,
                    'name': s.get('name', ''),
                    'source': s.get('source', ''),
                    'associated_herbs': s.get('associated_herbs', []),
                    'subtypes': s.get('subtypes', [])
                })
        return details
    
    def get_formula_details(self, formula_id: str):
        """获取方剂详情"""
        if formula_id in self.formulas:
            return self.formulas[formula_id]
        
        # 按需从磁盘加载
        if USE_EXTERNAL_KB:
            fpath = os.path.join(FORMULAS_DIR, f'{formula_id}.json')
            if os.path.exists(fpath):
                with open(fpath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        return None
    
    def get_drug_details(self, drug_id: str):
        """获取药物详情"""
        if drug_id in self.drugs:
            return self.drugs[drug_id]
        return None
    
    def diagnose(self, query: str):
        """中医辨证主函数"""
        # 1. 解析查询
        parsed = self.parse_query(query)
        
        # 2. 获取症状详情
        symptom_details = self.get_symptom_details(parsed['symptom_ids'])
        
        # 3. 检索相关方剂和药物
        matched = self.search_by_symptoms(parsed['symptom_ids'], top_k=10)
        
        # 4. 构建结果
        formulas = []
        drugs = []
        
        for item in matched:
            if item['type'] == 'formula':
                detail = self.get_formula_details(item['id'])
                if detail:
                    formulas.append(detail)
            elif item['type'] == 'drug':
                detail = self.get_drug_details(item['id'])
                if detail:
                    drugs.append(detail)
        
        return {
            'parsed': parsed,
            'symptoms': symptom_details,
            'formulas': formulas[:5],
            'drugs': drugs[:5],
            'total_matches': len(matched)
        }

# 初始化引擎
engine = XiaoShennongEngineV3()

# ========== API端点 ==========

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'service': 'xiaoshennong-v3',
        'version': '3.0',
        'knowledge': {
            'symptoms': len(SYMPTOM_MAP),
            'drugs': len(DRUG_MAP),
            'formulas_memory': len(FORMULA_MAP),
            'formulas_disk': len(glob.glob(os.path.join(FORMULAS_DIR, 'FP-*.json'))) if USE_EXTERNAL_KB else 0,
            'source': 'PTM_github_dataset'
        }
    })

@app.route('/api/symptoms', methods=['GET'])
def list_symptoms():
    """列出所有症状编码"""
    items = []
    for sid, s in SYMPTOM_MAP.items():
        items.append({
            'id': sid,
            'name': s.get('name', ''),
            'source': s.get('source', '')
        })
    
    return jsonify({
        'success': True,
        'data': {
            'total': len(items),
            'symptoms': items[:100]  # 分页，只返回前100
        }
    })

@app.route('/api/symptoms/search', methods=['POST'])
def search_symptoms():
    """搜索症状"""
    data = request.get_json() or {}
    query = data.get('query', '')
    
    results = []
    for name, s in SYMPTOM_NAME_MAP.items():
        if query in name:
            results.append({
                'id': s.get('id', ''),
                'name': s.get('name', ''),
                'source': s.get('source', '')
            })
    
    # 去重
    seen = set()
    unique_results = []
    for r in results:
        if r['id'] not in seen:
            seen.add(r['id'])
            unique_results.append(r)
    
    return jsonify({
        'success': True,
        'data': {
            'query': query,
            'results': unique_results[:20],
            'total': len(unique_results)
        }
    })

@app.route('/api/drugs', methods=['GET'])
def list_drugs():
    """列出所有药物编码"""
    items = []
    for did, d in DRUG_MAP.items():
        items.append({
            'id': did,
            'name': d.get('name', ''),
            'source': d.get('source', '')
        })
    
    return jsonify({
        'success': True,
        'data': {
            'total': len(items),
            'drugs': items[:100]
        }
    })

@app.route('/api/drugs/<drug_id>', methods=['GET'])
def get_drug(drug_id):
    """获取药物详情"""
    detail = engine.get_drug_details(drug_id.upper())
    if detail:
        return jsonify({'success': True, 'data': detail})
    return jsonify({'success': False, 'error': '药物不存在'}), 404

@app.route('/api/formulas', methods=['GET'])
def list_formulas():
    """列出所有方剂编码"""
    items = []
    for fid, f in FORMULA_MAP.items():
        items.append({
            'id': fid,
            'name': f.get('name', ''),
            'description': f.get('description', '')[:50]
        })
    
    return jsonify({
        'success': True,
        'data': {
            'total': len(items),
            'formulas': items[:100]
        }
    })

@app.route('/api/formulas/<formula_id>', methods=['GET'])
def get_formula(formula_id):
    """获取方剂详情"""
    detail = engine.get_formula_details(formula_id.upper())
    if detail:
        return jsonify({'success': True, 'data': detail})
    return jsonify({'success': False, 'error': '方剂不存在'}), 404

@app.route('/api/retrieve', methods=['POST'])
def retrieve():
    """检索知识库"""
    data = request.get_json() or {}
    query = data.get('query', '')
    top_k = data.get('top_k', 5)
    
    parsed = engine.parse_query(query)
    matched = engine.search_by_symptoms(parsed['symptom_ids'], top_k)
    
    results = []
    for item in matched:
        if item['type'] == 'formula':
            detail = engine.get_formula_details(item['id'])
        else:
            detail = engine.get_drug_details(item['id'])
        
        if detail:
            results.append({
                'type': item['type'],
                'id': item['id'],
                'name': item['name'],
                'score': round(item['score'], 4),
                'matched_symptoms': [
                    {'id': sid, 'name': SYMPTOM_MAP.get(sid, {}).get('name', sid)}
                    for sid in item['matched_symptoms']
                ],
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
    """中医辨证诊断"""
    data = request.get_json() or {}
    
    symptoms = data.get('symptoms', [])
    query = data.get('query', '')
    
    if isinstance(symptoms, list):
        query = ' '.join(str(s) for s in symptoms) + ' ' + query
    else:
        query = str(symptoms) + ' ' + query
    
    result = engine.diagnose(query)
    
    # 构建诊断报告
    report = _build_diagnosis_report(result)
    
    return jsonify({
        'success': True,
        'data': {
            'diagnosis': result,
            'report': report
        }
    })

def _build_diagnosis_report(result):
    """构建诊断报告文本"""
    lines = []
    
    # 症状分析
    lines.append("📋 症状分析")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    for s in result['symptoms']:
        lines.append(f"  • {s['name']} [{s['id']}]")
        herbs = s.get('associated_herbs', [])
        if herbs:
            lines.append(f"    关联药物: {', '.join(herbs[:5])}")
    lines.append("")
    
    # 推荐方剂
    if result['formulas']:
        lines.append("💊 推荐方剂")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for f in result['formulas'][:3]:
            lines.append(f"  【{f.get('name', '')}】{f.get('id', '')}")
            desc = f.get('description', '')
            if desc:
                lines.append(f"    描述: {desc[:100]}")
            comp = f.get('composition_text', '')
            if comp:
                lines.append(f"    组成: {comp[:100]}")
            lines.append("")
    
    # 推荐药物
    if result['drugs']:
        lines.append("🌿 相关药物")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for d in result['drugs'][:3]:
            lines.append(f"  【{d.get('name', '')}】{d.get('id', '')}")
            assoc = d.get('associated_symptoms', [])
            if assoc:
                symptom_names = [SYMPTOM_MAP.get(sid, {}).get('name', sid) for sid in assoc[:5]]
                lines.append(f"    主治症状: {', '.join(symptom_names)}")
            lines.append("")
    
    # 免责声明
    lines.append("⚠️ 免责声明")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("本结果仅供参考，不能替代专业医生诊断。")
    lines.append("如有不适，请及时就医。")
    
    return '\n'.join(lines)

if __name__ == '__main__':
    print("[LocalAPI v3.0] 启动服务，端口5003...")
    app.run(host='0.0.0.0', port=5003, debug=False)
