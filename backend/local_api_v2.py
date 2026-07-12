#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小神农中医AI - 本地API v2.0
支持编码查询和中文查询的完整RAG系统
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

# 加载症状编码
with open(os.path.join(DATA_DIR, 'symptom_codes_v2.json'), 'r', encoding='utf-8') as f:
    symptom_data = json.load(f)
    SYMPTOM_MAP = {s['id']: s for s in symptom_data['symptoms']}
    SYMPTOM_NAME_MAP = {s['name']: s for s in symptom_data['symptoms']}
    # 别名映射
    for s in symptom_data['symptoms']:
        for alias in s.get('aliases', []):
            SYMPTOM_NAME_MAP[alias] = s

# 加载药物编码
with open(os.path.join(DATA_DIR, 'drug_codes_v2.json'), 'r', encoding='utf-8') as f:
    drug_data = json.load(f)
    DRUG_MAP = {d['id']: d for d in drug_data['drugs']}
    DRUG_NAME_MAP = {d['name']: d for d in drug_data['drugs']}

# 加载方剂编码
with open(os.path.join(DATA_DIR, 'formula_codes_v2.json'), 'r', encoding='utf-8') as f:
    formula_data = json.load(f)
    FORMULA_MAP = {f['id']: f for f in formula_data['formulas']}
    FORMULA_NAME_MAP = {f['name']: f for f in formula_data['formulas']}

print(f"[LocalAPI v2.0] 加载完成:")
print(f"  症状: {len(SYMPTOM_MAP)} 条")
print(f"  药物: {len(DRUG_MAP)} 条")
print(f"  方剂: {len(FORMULA_MAP)} 条")

# ========== 核心检索引擎 ==========

class XiaoShennongEngine:
    """小神农中医AI检索引擎"""
    
    def __init__(self):
        self.symptoms = SYMPTOM_MAP
        self.drugs = DRUG_MAP
        self.formulas = FORMULA_MAP
        
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
        
        # 1. 提取症状编码 (SN-XX-XX-XXX)
        symptom_id_pattern = r'SN-[A-Z]{2}-[SO]-\d{3}'
        found_ids = re.findall(symptom_id_pattern, query.upper())
        result['symptom_ids'].extend(found_ids)
        
        # 2. 提取药物编码 (DR-XX-XXX)
        drug_id_pattern = r'DR-[A-Z0-9]{2,3}-\d{3}'
        found_drug_ids = re.findall(drug_id_pattern, query.upper())
        result['drug_ids'].extend(found_drug_ids)
        
        # 3. 提取方剂编码 (FP-XX-XXX)
        formula_id_pattern = r'FP-[A-Z]{2}-\d{3}'
        found_formula_ids = re.findall(formula_id_pattern, query.upper())
        result['formula_ids'].extend(found_formula_ids)
        
        # 4. 中文症状名匹配
        for name, symptom in SYMPTOM_NAME_MAP.items():
            if name in query:
                if symptom['id'] not in result['symptom_ids']:
                    result['symptom_ids'].append(symptom['id'])
                    result['symptom_names'].append(name)
        
        # 5. 中文药物名匹配
        for name, drug in DRUG_NAME_MAP.items():
            if name in query:
                if drug['id'] not in result['drug_ids']:
                    result['drug_ids'].append(drug['id'])
                    result['drug_names'].append(name)
        
        # 6. 中文方剂名匹配
        for name, formula in FORMULA_NAME_MAP.items():
            if name in query:
                if formula['id'] not in result['formula_ids']:
                    result['formula_ids'].append(formula['id'])
                    result['formula_names'].append(name)
        
        return result
    
    def search_by_symptoms(self, symptom_ids: list, top_k: int = 5):
        """根据症状编码检索相关方剂和药物"""
        results = []
        
        # 1. 查找包含这些症状的方剂
        matched_formulas = []
        for fid, formula in self.formulas.items():
            formula_symptoms = set(formula.get('indications', []))
            query_symptoms = set(symptom_ids)
            match_count = len(formula_symptoms & query_symptoms)
            if match_count > 0:
                matched_formulas.append({
                    'type': 'formula',
                    'id': fid,
                    'name': formula['name'],
                    'score': match_count / max(len(formula_symptoms), len(query_symptoms)),
                    'data': formula,
                    'matched_symptoms': list(formula_symptoms & query_symptoms)
                })
        
        # 2. 查找包含这些症状的药物
        matched_drugs = []
        for did, drug in self.drugs.items():
            drug_symptoms = set(drug.get('indications', []))
            query_symptoms = set(symptom_ids)
            match_count = len(drug_symptoms & query_symptoms)
            if match_count > 0:
                matched_drugs.append({
                    'type': 'drug',
                    'id': did,
                    'name': drug['name'],
                    'score': match_count / max(len(drug_symptoms), len(query_symptoms)),
                    'data': drug,
                    'matched_symptoms': list(drug_symptoms & query_symptoms)
                })
        
        # 3. 合并排序
        all_results = matched_formulas + matched_drugs
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
                    'name': s['name'],
                    'pinyin': s.get('pinyin', ''),
                    'part': s.get('part', ''),
                    'category': s.get('category', ''),
                    'aliases': s.get('aliases', []),
                    'common_syndromes': s.get('common_syndromes', [])
                })
        return details
    
    def get_formula_details(self, formula_id: str):
        """获取方剂详情，包含药物信息"""
        if formula_id not in self.formulas:
            return None
        
        formula = self.formulas[formula_id]
        composition = []
        for comp in formula.get('composition', []):
            drug_id = comp.get('drug_id', '')
            drug_info = self.drugs.get(drug_id, {})
            composition.append({
                'drug_id': drug_id,
                'name': comp.get('name', drug_info.get('name', '')),
                'dosage': comp.get('dosage', ''),
                'role': comp.get('role', ''),
                'properties': drug_info.get('properties', ''),
                'functions': drug_info.get('functions', '')
            })
        
        # 解析症状名
        symptom_names = []
        for sid in formula.get('indications', []):
            if sid in self.symptoms:
                symptom_names.append(self.symptoms[sid]['name'])
        
        return {
            'id': formula_id,
            'name': formula['name'],
            'source': formula.get('source', ''),
            'author': formula.get('author', ''),
            'dynasty': formula.get('dynasty', ''),
            'category': formula.get('category', ''),
            'type': formula.get('type', ''),
            'functions': formula.get('functions', ''),
            'syndrome': formula.get('syndrome', ''),
            'key_symptoms': formula.get('key_symptoms', []),
            'contraindications': formula.get('contraindications', []),
            'composition': composition,
            'indications': formula.get('indications', []),
            'symptom_names': symptom_names,
            'usage': formula.get('usage', ''),
            'source_text': formula.get('source_text', ''),
            'source_location': formula.get('source_location', ''),
            'clinical_notes': formula.get('clinical_notes', ''),
            'modern_applications': formula.get('modern_applications', []),
            'authenticity': formula.get('authenticity', '')
        }
    
    def get_drug_details(self, drug_id: str):
        """获取药物详情"""
        if drug_id not in self.drugs:
            return None
        
        drug = self.drugs[drug_id]
        
        # 解析症状名
        symptom_names = []
        for sid in drug.get('indications', []):
            if sid in self.symptoms:
                symptom_names.append(self.symptoms[sid]['name'])
        
        return {
            'id': drug_id,
            'name': drug['name'],
            'latin': drug.get('latin', ''),
            'properties': drug.get('properties', ''),
            'meridian': drug.get('meridian', ''),
            'functions': drug.get('functions', ''),
            'indications': drug.get('indications', []),
            'symptom_names': symptom_names,
            'contraindications': drug.get('contraindications', []),
            'dosage': drug.get('dosage', ''),
            'source': drug.get('source', ''),
            'authenticity': drug.get('authenticity', '')
        }
    
    def check_drug_interactions(self, drug_ids: list):
        """检查药物相互作用"""
        interactions = {
            'mutual_enhancement': [],  # 相须/相使
            'mutual_inhibition': [],    # 相恶
            'mutual_aversion': [],       # 相反（十八反）
            'mutual_neutrality': []      # 相畏/相杀
        }
        
        drug_id_set = set(drug_ids)
        
        # 检查相须/相使
        for rel in drug_data.get('drug_relationships', {}).get('mutual_enhancement', []):
            if rel['drug_a'] in drug_id_set and rel['drug_b'] in drug_id_set:
                interactions['mutual_enhancement'].append(rel)
        
        # 检查相恶
        for rel in drug_data.get('drug_relationships', {}).get('mutual_inhibition', []):
            if rel['drug_a'] in drug_id_set and rel['drug_b'] in drug_id_set:
                interactions['mutual_inhibition'].append(rel)
        
        # 检查相反（十八反）
        for rel in drug_data.get('drug_relationships', {}).get('mutual_aversion', []):
            if rel['drug_a'] in drug_id_set and rel['drug_b'] in drug_id_set:
                interactions['mutual_aversion'].append(rel)
        
        # 检查相畏/相杀
        for rel in drug_data.get('drug_relationships', {}).get('mutual_neutrality', []):
            if rel['drug_a'] in drug_id_set and rel['drug_b'] in drug_id_set:
                interactions['mutual_neutrality'].append(rel)
        
        return interactions
    
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
        all_drug_ids = []
        
        for item in matched:
            if item['type'] == 'formula':
                detail = self.get_formula_details(item['id'])
                if detail:
                    formulas.append(detail)
                    # 收集方剂中的药物ID
                    for comp in detail.get('composition', []):
                        all_drug_ids.append(comp['drug_id'])
            elif item['type'] == 'drug':
                detail = self.get_drug_details(item['id'])
                if detail:
                    drugs.append(detail)
                    all_drug_ids.append(item['id'])
        
        # 5. 检查药物相互作用
        interactions = self.check_drug_interactions(all_drug_ids)
        
        # 6. 分析证型
        syndromes = {}
        for s in symptom_details:
            for syndrome in s.get('common_syndromes', []):
                syndromes[syndrome] = syndromes.get(syndrome, 0) + 1
        
        # 按出现频率排序
        sorted_syndromes = sorted(syndromes.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'parsed': parsed,
            'symptoms': symptom_details,
            'syndrome_analysis': sorted_syndromes[:5],
            'formulas': formulas[:5],
            'drugs': drugs[:5],
            'interactions': interactions,
            'total_matches': len(matched)
        }

# 初始化引擎
engine = XiaoShennongEngine()

# ========== API端点 ==========

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'service': 'xiaoshennong-v2',
        'version': '2.0',
        'knowledge': {
            'symptoms': len(SYMPTOM_MAP),
            'drugs': len(DRUG_MAP),
            'formulas': len(FORMULA_MAP)
        }
    })

@app.route('/api/symptoms', methods=['GET'])
def list_symptoms():
    """列出所有症状编码"""
    return jsonify({
        'success': True,
        'data': {
            'total': len(SYMPTOM_MAP),
            'symptoms': [
                {'id': s['id'], 'name': s['name'], 'pinyin': s.get('pinyin', ''), 
                 'part': s['part'], 'category': s['category']}
                for s in symptom_data['symptoms']
            ]
        }
    })

@app.route('/api/symptoms/search', methods=['POST'])
def search_symptoms():
    """搜索症状"""
    data = request.get_json() or {}
    query = data.get('query', '')
    
    results = []
    for s in symptom_data['symptoms']:
        if query in s['name'] or query in s.get('pinyin', '') or any(query in a for a in s.get('aliases', [])):
            results.append({
                'id': s['id'],
                'name': s['name'],
                'pinyin': s.get('pinyin', ''),
                'aliases': s.get('aliases', []),
                'common_syndromes': s.get('common_syndromes', [])
            })
    
    return jsonify({
        'success': True,
        'data': {
            'query': query,
            'results': results,
            'total': len(results)
        }
    })

@app.route('/api/drugs', methods=['GET'])
def list_drugs():
    """列出所有药物编码"""
    return jsonify({
        'success': True,
        'data': {
            'total': len(DRUG_MAP),
            'drugs': [
                {'id': d['id'], 'name': d['name'], 'category': d.get('category', ''),
                 'properties': d.get('properties', ''), 'functions': d.get('functions', '')}
                for d in drug_data['drugs']
            ]
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
    return jsonify({
        'success': True,
        'data': {
            'total': len(FORMULA_MAP),
            'formulas': [
                {'id': f['id'], 'name': f['name'], 'source': f.get('source', ''),
                 'category': f.get('category', ''), 'type': f.get('type', '')}
                for f in formula_data['formulas']
            ]
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
    
    # 支持多种输入格式
    symptoms = data.get('symptoms', [])
    query = data.get('query', '')
    
    # 构建查询字符串
    if isinstance(symptoms, list):
        query = ' '.join(str(s) for s in symptoms) + ' ' + query
    else:
        query = str(symptoms) + ' ' + query
    
    # 执行辨证
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
        lines.append(f"    常见证型: {', '.join(s.get('common_syndromes', [])[:3])}")
    lines.append("")
    
    # 证型分析
    if result['syndrome_analysis']:
        lines.append("🔬 证型分析")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for syndrome, count in result['syndrome_analysis'][:3]:
            lines.append(f"  • {syndrome} (匹配度: {count})")
        lines.append("")
    
    # 推荐方剂
    if result['formulas']:
        lines.append("💊 推荐方剂")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for f in result['formulas'][:3]:
            lines.append(f"  【{f['name']}】{f['id']}")
            lines.append(f"    来源: {f['source']}")
            lines.append(f"    功效: {f['functions']}")
            lines.append(f"    主治证型: {f['syndrome']}")
            lines.append(f"    组成: {', '.join([c['name'] + c['dosage'] for c in f['composition'][:5]])}")
            lines.append("")
    
    # 推荐药物
    if result['drugs']:
        lines.append("🌿 相关药物")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for d in result['drugs'][:3]:
            lines.append(f"  【{d['name']}】{d['id']}")
            lines.append(f"    性味归经: {d['properties']}，归{d['meridian']}经")
            lines.append(f"    功效: {d['functions']}")
            lines.append("")
    
    # 药物相互作用警告
    interactions = result['interactions']
    if interactions['mutual_aversion']:
        lines.append("⚠️ 药物禁忌警告")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for rel in interactions['mutual_aversion']:
            lines.append(f"  🔴 {rel['drug_a']} + {rel['drug_b']}: {rel['description']}")
        lines.append("")
    
    if interactions['mutual_inhibition']:
        lines.append("⚠️ 药物配伍警告")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for rel in interactions['mutual_inhibition']:
            lines.append(f"  🟠 {rel['drug_a']} + {rel['drug_b']}: {rel['description']}")
        lines.append("")
    
    # 免责声明
    lines.append("⚠️ 免责声明")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("本结果仅供参考，不能替代专业医生诊断。")
    lines.append("如有不适，请及时就医。")
    
    return '\n'.join(lines)

@app.route('/api/interactions/check', methods=['POST'])
def check_interactions():
    """检查药物相互作用"""
    data = request.get_json() or {}
    drug_ids = data.get('drug_ids', [])
    
    interactions = engine.check_drug_interactions([d.upper() for d in drug_ids])
    
    return jsonify({
        'success': True,
        'data': {
            'drug_ids': drug_ids,
            'interactions': interactions,
            'has_danger': len(interactions['mutual_aversion']) > 0
        }
    })

if __name__ == '__main__':
    print("[LocalAPI v2.0] 启动服务，端口5002...")
    app.run(host='0.0.0.0', port=5002, debug=False)
