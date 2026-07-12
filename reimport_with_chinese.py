#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新生成带中文症状名的导入数据，替换编码症状
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

# 读取症状编码映射
symptom_map = {}
try:
    with open('data/symptom_codes.json', 'r', encoding='utf-8') as f:
        sc = json.load(f)
        for item in sc:
            symptom_map[item['id']] = item['name']
    print(f"加载了 {len(symptom_map)} 个症状编码映射")
except:
    print("未找到症状编码映射文件，使用内置映射")
    # 内置一些常见映射
    symptom_map = {
        'SN-TH-S-001': '头痛', 'SN-TH-S-002': '头晕', 'SN-TH-S-003': '头胀',
        'SN-TH-S-058': '发热', 'SN-TH-S-057': '恶寒', 'SN-TH-S-029': '恶风',
        'SN-HD-S-034': '胸闷', 'SN-HD-S-061': '胸痛', 'SN-PS-C-001': '疲乏无力',
        'SN-RE-S-007': '气短', 'SN-SP-S-030': '食欲不振', 'SN-SP-O-001': '腹胀',
        'SN-SK-O-003': '水肿', 'SN-BK-S-002': '腰痛', 'SN-LM-S-009': '关节痛',
        'SN-OT-S-014': '口苦', 'SN-TM-O-001': '口干', 'SN-RP-S-010': '咳嗽',
        'SN-TH-S-056': '无汗', 'SN-TH-S-055': '汗出', 'SN-HD-O-008': '心烦',
    }

# 读取药物编码映射
drug_map = {}
try:
    with open('data/drug_codes.json', 'r', encoding='utf-8') as f:
        dc = json.load(f)
        for item in dc:
            drug_map[item['id']] = item['name']
except:
    pass

# 重新导入医案数据（使用中文症状名）
print("=== 重新导入医案数据（中文症状名） ===")
case_files = sorted(glob.glob('data/raw/medical_cases_final_batch_*.json'))[:5]
total_cases = 0

for i, fpath in enumerate(case_files):
    with open(fpath, 'rb') as f:
        raw = f.read()
    cases = json.loads(raw.decode('utf-8'))
    
    documents = []
    for case in cases:
        # 使用中文症状名
        symptom_names = case.get('symptom_names', [])
        if not symptom_names:
            # 尝试用编码映射
            symptom_names = [symptom_map.get(sid, sid) for sid in case.get('symptoms', [])]
        
        drug_names = case.get('drug_names', [])
        if not drug_names:
            drug_names = [drug_map.get(did, did) for did in case.get('drugs', [])]
        
        formula_name = case.get('formula_name', case.get('formula', ''))
        
        text = f"医案-{case.get('case_id','')}\n"
        text += f"患者：{case.get('patient_age','')}岁{case.get('patient_gender','')}\n"
        text += f"症状：{', '.join(symptom_names)}\n"
        text += f"辨证：{case.get('syndrome','')} {case.get('diagnosis','')}\n"
        text += f"治法：{case.get('treatment','')}\n"
        text += f"方药：{formula_name} {', '.join(drug_names)}\n"
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
    
    for j in range(0, len(documents), 100):
        batch = documents[j:j+100]
        import_batch(batch, f"医案批次{i+1}-{j//100+1}")
        total_cases += len(batch)

print(f"\n医案导入完成: {total_cases} 条")

# 检查最终统计
print("\n=== 最终统计 ===")
resp = requests.get(f"{API_BASE}/api/knowledge/stats", timeout=30)
stats = resp.json()
print(json.dumps(stats, ensure_ascii=False, indent=2))
