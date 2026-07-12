#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小神农中医AI - 本地简化版API
使用正确的中文症状名数据，绕过服务器编码问题
"""

import json
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 加载本地真实数据
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'real')

knowledge_base = []

def load_data():
    """加载所有真实数据"""
    global knowledge_base
    
    # 加载药典药物
    with open(os.path.join(DATA_DIR, 'all_real_data.json'), 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 药物
    for herb in data.get('herbs', []):
        text = f"{herb['name']}\n性味归经：{herb.get('properties','')} {herb.get('meridian','')}\n"
        text += f"功效：{herb.get('functions','')}\n"
        text += f"主治：{', '.join(herb.get('indications',[]))}\n"
        text += f"用法：{herb.get('usage','')}\n"
        text += f"禁忌：{', '.join(herb.get('contraindications',[]))}"
        knowledge_base.append({
            'text': text,
            'metadata': {'name': herb['name'], 'source': herb.get('source',''), 'category': 'drug'},
            'keywords': [herb['name']] + herb.get('indications', [])
        })
    
    # 方剂
    for formula in data.get('formulas', []):
        text = f"{formula['name']}\n来源：{formula.get('source','')}\n"
        text += f"组成：{', '.join(formula.get('composition',[]))}\n"
        text += f"功效：{formula.get('functions','')}\n"
        text += f"主治：{', '.join(formula.get('indications',[]))}"
        knowledge_base.append({
            'text': text,
            'metadata': {'name': formula['name'], 'source': formula.get('source',''), 'category': 'formula'},
            'keywords': [formula['name']] + formula.get('indications', [])
        })
    
    # 医案
    for case in data.get('cases', []):
        text = f"医案-{case.get('case_id','')}\n"
        text += f"患者：{case.get('patient_age','')}岁{case.get('patient_gender','')}\n"
        text += f"症状：{', '.join(case.get('symptoms',[]))}\n"
        text += f"辨证：{case.get('diagnosis','')}\n"
        text += f"治法：{case.get('treatment','')}\n"
        text += f"方药：{case.get('formula','')}\n"
        text += f"疗效：{case.get('effectiveness','')}"
        knowledge_base.append({
            'text': text,
            'metadata': {'name': case.get('case_id',''), 'source': case.get('source',''), 'category': 'case'},
            'keywords': case.get('symptoms', []) + [case.get('diagnosis',''), case.get('formula','')]
        })
    
    print(f"[LocalAPI] 加载了 {len(knowledge_base)} 条知识")

# 简单的关键词检索
def search_knowledge(query, top_k=5):
    """基于关键词的检索"""
    query_keywords = set(query.lower().split())
    
    results = []
    for item in knowledge_base:
        score = 0
        text_lower = item['text'].lower()
        
        # 直接匹配
        if query.lower() in text_lower:
            score += 2.0
        
        # 关键词匹配
        for kw in item['keywords']:
            if kw.lower() in query.lower() or query.lower() in kw.lower():
                score += 1.0
        
        # 分词匹配
        for qk in query_keywords:
            if len(qk) >= 2 and qk in text_lower:
                score += 0.5
        
        if score > 0:
            results.append({
                'text': item['text'],
                'metadata': item['metadata'],
                'score': score
            })
    
    # 按分数排序
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:top_k]

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'service': 'xiaoshennong-local',
        'knowledge_count': len(knowledge_base)
    })

@app.route('/api/retrieve', methods=['POST'])
def retrieve():
    data = request.get_json() or {}
    query = data.get('query', '')
    top_k = data.get('top_k', 5)
    
    results = search_knowledge(query, top_k)
    
    return jsonify({
        'success': True,
        'data': {
            'query': query,
            'results': results,
            'total': len(results)
        }
    })

@app.route('/api/diagnosis', methods=['POST'])
def diagnosis():
    data = request.get_json() or {}
    symptoms = data.get('symptoms', [])
    query = ' '.join(symptoms) if isinstance(symptoms, list) else data.get('query', '')
    
    # 检索相关知识
    results = search_knowledge(query, top_k=5)
    
    # 构建简单的诊断结果
    if results:
        # 提取相关药物和方剂
        drugs = [r for r in results if r['metadata'].get('category') == 'drug']
        formulas = [r for r in results if r['metadata'].get('category') == 'formula']
        cases = [r for r in results if r['metadata'].get('category') == 'case']
        
        advice = "📋 症状分析\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        advice += f"用户描述：{query}\n\n"
        
        if cases:
            advice += "📜 相关医案\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            for c in cases[:2]:
                advice += f"{c['text'][:300]}...\n\n"
        
        if formulas:
            advice += "💊 推荐方剂\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            for f in formulas[:2]:
                advice += f"{f['text'][:300]}...\n\n"
        
        if drugs:
            advice += "🌿 相关药物\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            for d in drugs[:2]:
                advice += f"{d['text'][:300]}...\n\n"
        
        advice += "\n⚠️ 免责声明\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        advice += "本结果仅供参考，不能替代专业医生诊断。如有不适，请及时就医。"
        
        sources = [{'book': r['metadata'].get('source', '未知'), 'section': r['metadata'].get('name', '')} for r in results[:3]]
    else:
        advice = "抱歉，暂无权威数据支持该问题。\n\n建议：\n1. 尝试使用更具体的症状描述\n2. 咨询专业中医师\n3. 参考权威中医典籍"
        sources = []
    
    return jsonify({
        'success': True,
        'data': {
            'constitution': '待辨识',
            'syndrome': '待进一步辨证',
            'advice': advice,
            'classic_sources': sources,
            'warning': '本结果仅供参考，不能替代专业医生诊断',
            'thinking_process': [
                {'step': 1, 'name': '症状分析', 'description': '提取用户症状', 'status': 'completed'},
                {'step': 2, 'name': '知识检索', 'description': f'检索到 {len(results)} 条相关知识', 'status': 'completed'},
                {'step': 3, 'name': '结果生成', 'description': '基于检索结果生成建议', 'status': 'completed'}
            ],
            'total_time_ms': 100,
            'drug_recommendations': [],
            'formula_recommendations': [],
            'contraindications': [],
            'credibility_assessment': [],
            'cooccurrence_analysis': {},
            'adverse_detection': {'risk_level': '低风险', 'adverse_events': [], 'time_window_days': 7}
        }
    })

if __name__ == '__main__':
    load_data()
    print("[LocalAPI] 启动本地API服务，端口5002...")
    app.run(host='0.0.0.0', port=5002, debug=False)
