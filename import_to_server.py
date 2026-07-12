#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将本地批量数据导入到服务器知识库
"""
import json
import glob
import requests
import sys

sys.stdout.reconfigure(encoding='utf-8')

API_BASE = "http://43.247.135.91:5001"

def import_batch(documents, batch_name):
    """导入一批文档到服务器"""
    url = f"{API_BASE}/api/knowledge/import"
    payload = {"documents": documents}
    
    try:
        resp = requests.post(url, json=payload, timeout=120)
        data = resp.json()
        if data.get("success"):
            print(f"  {batch_name}: 导入 {len(documents)} 条成功，总计 {data['data']['total_count']}")
            return True
        else:
            print(f"  {batch_name}: 失败 - {data.get('error')}")
            return False
    except Exception as e:
        print(f"  {batch_name}: 错误 - {e}")
        return False

# 1. 导入医案数据（前10批 = 10,000条）
print("=== 导入医案数据 ===")
case_files = sorted(glob.glob('data/raw/medical_cases_final_batch_*.json'))[:10]
total_cases = 0

for i, fpath in enumerate(case_files):
    with open(fpath, 'r', encoding='utf-8') as f:
        cases = json.load(f)
    
    documents = []
    for case in cases:
        text = f"医案-{case.get('case_id','')}\n"
        text += f"患者：{case.get('patient_age','')}岁{case.get('patient_gender','')}\n"
        text += f"症状：{', '.join(case.get('symptoms',[]))}\n"
        text += f"辨证：{case.get('syndrome','')} {case.get('diagnosis','')}\n"
        text += f"治法：{case.get('treatment','')}\n"
        text += f"方药：{case.get('formula_name','')} {case.get('formula','')}\n"
        text += f"疗效：{case.get('effectiveness','')}"
        
        documents.append({
            'text': text,
            'metadata': {
                'name': case.get('case_id', ''),
                'source': case.get('source', '中医医案数据库'),
                'category': 'case',
                'authenticity': 'generated'
            }
        })
    
    # 每批100条导入
    for j in range(0, len(documents), 100):
        batch = documents[j:j+100]
        import_batch(batch, f"医案批次{i+1}-{j//100+1}")
        total_cases += len(batch)

print(f"\n医案导入完成: {total_cases} 条")

# 2. 导入古籍数据（前10批 = 10,000条）
print("\n=== 导入古籍数据 ===")
text_files = sorted(glob.glob('data/raw/classical_texts_final_batch_*.json'))[:10]
total_texts = 0

for i, fpath in enumerate(text_files):
    with open(fpath, 'r', encoding='utf-8') as f:
        texts = json.load(f)
    
    documents = []
    for text_item in texts:
        text = f"古籍-{text_item.get('text_id','')}\n"
        text += f"来源：{text_item.get('source_book','')} {text_item.get('source_section','')}\n"
        text += f"朝代：{text_item.get('dynasty','')}\n"
        text += f"内容：{text_item.get('original_text','')}\n"
        if text_item.get('annotation'):
            text += f"注释：{text_item['annotation']}"
        
        documents.append({
            'text': text,
            'metadata': {
                'name': text_item.get('text_id', ''),
                'source': f"{text_item.get('source_book','')} {text_item.get('source_section','')}",
                'category': 'classical_text',
                'authenticity': 'generated'
            }
        })
    
    for j in range(0, len(documents), 100):
        batch = documents[j:j+100]
        import_batch(batch, f"古籍批次{i+1}-{j//100+1}")
        total_texts += len(batch)

print(f"\n古籍导入完成: {total_texts} 条")

# 3. 检查最终统计
print("\n=== 最终统计 ===")
resp = requests.get(f"{API_BASE}/api/knowledge/stats", timeout=30)
stats = resp.json()
print(json.dumps(stats, ensure_ascii=False, indent=2))
