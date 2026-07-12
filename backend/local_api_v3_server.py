#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小神农中医AI - 本地API v3.0 (Server Edition)
使用内部数据格式，兼容服务器部署
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
    with open(os.path.join(DATA_DIR, 'symptom_codes_v3_mini.json'), 'r', encoding='utf-8') as f:
        symptom_data = json.load(f)
        for s in symptom_data.get('symptoms', []):
            SYMPTOM_MAP[s['id']] = s
            SYMPTOM_NAME_MAP[s['name']] = s
            for alias in s.get('aliases', []):
                SYMPTOM_NAME_MAP[alias] = s
    print(f"[LocalAPI v3.0] 症状: {len(SYMPTOM_MAP)} 条")
except Exception as e:
    print(f"[LocalAPI v3.0] 症状加载失败: {e}")

# 加载药物数据
DRUG_MAP = {}
DRUG_NAME_MAP = {}

try:
    with open(os.path.join(DATA_DIR, 'drug_codes_v3_mini.json'), 'r', encoding='utf-8') as f:
        drug_data = json.load(f)
        for d in drug_data.get('drugs', []):
            DRUG_MAP[d['id']] = d
            DRUG_NAME_MAP[d['name']] = d
    print(f"[LocalAPI v3.0] 药物: {len(DRUG_MAP)} 条")
except Exception as e:
    print(f"[LocalAPI v3.0] 药物加载失败: {e}")

# 加载方剂数据
try:
    with open(os.path.join(DATA_DIR, 'formula_codes_v2.json'), 'r', encoding='utf-8') as f:
        formula_data = json.load(f)
        FORMULA_MAP = {f['id']: f for f in formula_data.get('formulas', [])}
        FORMULA_NAME_MAP = {f['name']: f for f in formula_data.get('formulas', [])}
    print(f"[LocalAPI v3.0] 方剂: {len(FORMULA_MAP)} 条")
except Exception as e:
    print(f"[LocalAPI v3.0] 方剂加载失败: {e}")
    FORMULA_MAP = {}
    FORMULA_NAME_MAP = {}

print(f"[LocalAPI v3.0] 加载完成:")
print(f"  症状: {len(SYMPTOM_MAP)} 条")
print(f"  药物: {len(DRUG_MAP)} 条")
print(f"  方剂: {len(FORMULA_MAP)} 条")

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
        
        # 4. 中文症状名匹配
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
            drug_symptoms = set(drug.get('indications', []))
            match_count = len(drug_symptoms & query_symptoms)
            if match_count > 0:
                matched_drugs.append({
                    'type': 'drug',
                    'id': did,
                    'name': drug.get('name', ''),
                    'score': match_count / max(len(drug_symptoms), len(query_symptoms)),
                    'data': drug,
                    'matched_symptoms': list(drug_symptoms & query_symptoms)
                })
        
        # 2. 查找包含这些症状的方剂
        matched_formulas = []
        for fid, formula in self.formulas.items():
            formula_symptoms = set(formula.get('indications', []))
            match_count = len(formula_symptoms & query_symptoms)
            if match_count > 0:
                matched_formulas.append({
                    'type': 'formula',
                    'id': fid,
                    'name': formula.get('name', ''),
                    'score': match_count / max(len(formula_symptoms), len(query_symptoms)),
                    'data': formula,
                    'matched_symptoms': list(formula_symptoms & query_symptoms)
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
                    'pinyin': s.get('pinyin', ''),
                    'part': s.get('part', ''),
                    'category': s.get('category', ''),
                    'aliases': s.get('aliases', []),
                    'common_syndromes': s.get('common_syndromes', [])
                })
        return details
    
    def get_formula_details(self, formula_id: str):
        """获取方剂详情"""
        if formula_id in self.formulas:
            return self.formulas[formula_id]
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
            'formulas': len(FORMULA_MAP),
            'source': 'PTM_github_dataset_server'
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
            'pinyin': s.get('pinyin', ''),
            'part': s.get('part', ''),
            'category': s.get('category', '')
        })
    
    return jsonify({
        'success': True,
        'data': {
            'total': len(items),
            'symptoms': items[:100]
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
                'pinyin': s.get('pinyin', ''),
                'aliases': s.get('aliases', []),
                'common_syndromes': s.get('common_syndromes', [])
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
            'properties': d.get('properties', ''),
            'functions': d.get('functions', '')
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
            'source': f.get('source', ''),
            'category': f.get('category', '')
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
                comp_names = [c.get('name', '') + c.get('dosage', '') for c in comp[:5]]
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
    
    # 免责声明
    lines.append("=" * 40)
    lines.append("免责声明：本结果仅供参考，不能替代专业医生诊断。")
    lines.append("如有不适，请及时就医。")
    
    return '\n'.join(lines)

# ========== 对话式问诊引擎 ==========

class DialogueEngine:
    """对话式中医问诊引擎"""
    
    # 症状追问模板
    FOLLOW_UP_QUESTIONS = {
        '失眠': ['入睡困难还是易醒？', '伴有心烦吗？', '口干吗？'],
        '不寐': ['入睡困难还是易醒？', '伴有心烦吗？', '口干吗？'],
        '多梦': ['梦境清晰吗？', '晨起疲劳吗？'],
        '心烦': ['心烦加重的时间？', '伴有失眠吗？'],
        '头痛': ['头痛部位？', '胀痛还是刺痛？', '伴有恶心吗？'],
        '头晕': ['旋转感还是昏沉感？', '伴有耳鸣吗？'],
        '胃痛': ['空腹痛还是饭后痛？', '喜温喜按吗？'],
        '便秘': ['大便干结吗？', '几天一次？'],
        '腹泻': ['大便稀溏吗？', '伴有腹痛吗？'],
        '咳嗽': ['有痰吗？', '痰色白还是黄？'],
        '气喘': ['活动后加重吗？', '伴有胸闷吗？'],
        '乏力': ['乏力程度？', '伴有气短吗？'],
        '口干': ['口渴想喝水吗？', '夜间加重吗？'],
        '口苦': ['晨起明显吗？', '伴有胁痛吗？'],
        '畏寒': ['怕冷还是怕风？', '四肢冰冷吗？'],
        '发热': ['发热时间？', '伴有汗出吗？'],
        '汗出': ['自汗还是盗汗？', '汗出部位？'],
        '心悸': ['心悸频率？', '伴有胸闷吗？'],
        '胸闷': ['胸闷程度？', '伴有气短吗？'],
        '胁痛': ['胀痛还是刺痛？', '与情绪有关吗？'],
        '腰痛': ['酸软还是刺痛？', '劳累后加重吗？'],
        '关节痛': ['游走性还是固定？', '遇寒加重吗？'],
        '皮肤瘙痒': ['干燥还是潮湿？', '夜间加重吗？'],
        '月经不调': ['提前还是延后？', '经色如何？'],
        '痛经': ['经前痛还是经中痛？', '喜温还是喜冷？'],
    }
    
    def __init__(self):
        self.sessions = {}  # 简单内存会话存储
    
    def start_session(self, session_id: str, initial_symptoms: list = None):
        """开始新的问诊会话"""
        self.sessions[session_id] = {
            'symptoms': initial_symptoms or [],
            'asked_questions': [],
            'answers': {},
            'stage': 'collecting',  # collecting -> analyzing -> complete
            'turn': 0
        }
        return self._generate_next_question(session_id)
    
    def process_answer(self, session_id: str, answer: str):
        """处理用户回答，生成下一个问题"""
        if session_id not in self.sessions:
            return self.start_session(session_id, [answer])
        
        session = self.sessions[session_id]
        session['turn'] += 1
        session['answers'][session['turn']] = answer
        
        # 从回答中提取症状
        new_symptoms = self._extract_symptoms(answer)
        session['symptoms'].extend(new_symptoms)
        session['symptoms'] = list(set(session['symptoms']))
        
        # 如果收集了足够信息或达到最大轮数，进入分析阶段
        if session['turn'] >= 5 or len(session['symptoms']) >= 4:
            session['stage'] = 'analyzing'
            return self._generate_diagnosis(session_id)
        
        return self._generate_next_question(session_id)
    
    def _extract_symptoms(self, text: str):
        """从文本中提取症状"""
        found = []
        for name in SYMPTOM_NAME_MAP.keys():
            if len(name) >= 2 and name in text:
                found.append(name)
        return found
    
    def _generate_next_question(self, session_id: str):
        """生成下一个追问问题"""
        session = self.sessions[session_id]
        symptoms = session['symptoms']
        asked = session['asked_questions']
        
        # 根据已有症状找相关追问
        for sym in symptoms:
            questions = self.FOLLOW_UP_QUESTIONS.get(sym, [])
            for q in questions:
                if q not in asked:
                    asked.append(q)
                    return {
                        'type': 'question',
                        'session_id': session_id,
                        'turn': session['turn'] + 1,
                        'question': q,
                        'context': f"基于您提到的{sym}症状",
                        'collected_symptoms': symptoms,
                        'stage': 'collecting',
                        'progress': min(100, int((session['turn'] / 5) * 100))
                    }
        
        # 如果没有特定追问，使用通用问题
        general_questions = [
            '您的食欲如何？',
            '您的大便情况正常吗？',
            '您的睡眠除了提到的问题，还有其他不适吗？',
            '您平时容易疲劳吗？',
            '您的情绪状态如何？',
            '您有口干或口苦的感觉吗？',
        ]
        
        for q in general_questions:
            if q not in asked:
                asked.append(q)
                return {
                    'type': 'question',
                    'session_id': session_id,
                    'turn': session['turn'] + 1,
                    'question': q,
                    'context': '进一步了解您的身体状况',
                    'collected_symptoms': symptoms,
                    'stage': 'collecting',
                    'progress': min(100, int((session['turn'] / 5) * 100))
                }
        
        # 没有更多问题了，进入分析
        session['stage'] = 'analyzing'
        return self._generate_diagnosis(session_id)
    
    def _generate_diagnosis(self, session_id: str):
        """生成诊断结果"""
        session = self.sessions[session_id]
        symptoms = session['symptoms']
        
        # 使用引擎进行诊断
        query = ' '.join(symptoms)
        result = engine.diagnose(query)
        
        report = _build_diagnosis_report(result)
        
        return {
            'type': 'diagnosis',
            'session_id': session_id,
            'turn': session['turn'],
            'collected_symptoms': symptoms,
            'stage': 'complete',
            'progress': 100,
            'diagnosis': result,
            'report': report
        }

# 初始化对话引擎
dialogue_engine = DialogueEngine()

@app.route('/api/dialogue/start', methods=['POST'])
def dialogue_start():
    """开始对话式问诊"""
    data = request.get_json() or {}
    session_id = data.get('session_id', f"session_{os.urandom(8).hex()}")
    initial_symptoms = data.get('symptoms', [])
    initial_query = data.get('query', '')
    
    # 提取初始症状
    if initial_query:
        initial_symptoms.extend(dialogue_engine._extract_symptoms(initial_query))
    
    result = dialogue_engine.start_session(session_id, initial_symptoms)
    return jsonify({'success': True, 'data': result})

@app.route('/api/dialogue/turn', methods=['POST'])
def dialogue_turn():
    """对话回合"""
    data = request.get_json() or {}
    session_id = data.get('session_id', '')
    answer = data.get('answer', '')
    
    if not session_id:
        return jsonify({'success': False, 'error': '缺少session_id'}), 400
    
    result = dialogue_engine.process_answer(session_id, answer)
    return jsonify({'success': True, 'data': result})

@app.route('/api/interactions/check', methods=['POST'])
def check_interactions():
    """检查药物相互作用"""
    data = request.get_json() or {}
    drug_ids = data.get('drug_ids', [])
    
    return jsonify({
        'success': True,
        'data': {
            'drug_ids': drug_ids,
            'interactions': {
                'mutual_enhancement': [],
                'mutual_inhibition': [],
                'mutual_aversion': [],
                'mutual_neutrality': []
            },
            'has_danger': False
        }
    })

if __name__ == '__main__':
    print("[LocalAPI v3.0] 启动服务，端口5003...")
    app.run(host='0.0.0.0', port=5003, debug=False)
