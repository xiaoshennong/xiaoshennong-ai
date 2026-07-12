#!/usr/bin/env python3
"""
小神农中医AI - 知识库数据导入工具 v3.0
将生成的结构化数据导入ChromaDB向量数据库
"""

import os
import json
import sys
sys.dont_write_bytecode = True

import chromadb
from chromadb.config import Settings

# 项目路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")

# 使用sentence-transformers嵌入
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    USE_LOCAL = True
    print("[导入] 使用本地嵌入模型 all-MiniLM-L6-v2")
except ImportError:
    USE_LOCAL = False
    print("[导入] 警告：未安装sentence-transformers，将使用默认嵌入")


def get_embedding(text):
    """获取文本嵌入向量"""
    if USE_LOCAL:
        return model.encode(text, convert_to_numpy=True).tolist()
    return None


def import_symptoms(collection, filepath):
    """导入症状数据"""
    print(f"[导入症状] {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        symptoms = json.load(f)
    
    count = 0
    for sid, info in symptoms.items():
        text = f"症状编号：{sid}\n症状名称：{info['name']}\n别名：{', '.join(info['aliases'])}\n经典引用：{', '.join(info['classic_refs'])}"
        
        collection.add(
            documents=[text],
            metadatas=[{
                'type': 'symptom',
                'id': sid,
                'name': info['name'],
                'source': 'extended_symptoms',
                'classic_refs': ', '.join(info['classic_refs'])
            }],
            ids=[f"symptom_{sid}"]
        )
        count += 1
    
    print(f"  导入 {count} 个症状")
    return count


def import_drugs(collection, filepath):
    """导入药物数据"""
    print(f"[导入药物] {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        drugs = json.load(f)
    
    count = 0
    for did, info in drugs.items():
        text = f"药物编号：{did}\n药物名称：{info['name']}\n性味归经：{info['properties']['nature']}，归{info['properties']['meridian']}\n主治症状：{', '.join(info['indications'])}\n禁忌：{', '.join(info['contraindications'])}\n有效率：{info['effectiveness_stats']['effectiveness_rate']}"
        
        collection.add(
            documents=[text],
            metadatas=[{
                'type': 'drug',
                'id': did,
                'name': info['name'],
                'source': 'extended_drugs',
                'effectiveness_rate': info['effectiveness_stats']['effectiveness_rate'],
                'evidence_level': info['effectiveness_stats']['evidence_level']
            }],
            ids=[f"drug_{did}"]
        )
        count += 1
    
    print(f"  OK 导入 {count} 个药物")
    return count


def import_formulas(collection, filepath):
    """导入方剂数据"""
    print(f"[导入方剂] {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        formulas = json.load(f)
    
    count = 0
    for fid, info in formulas.items():
        composition_str = ', '.join([f"{k}({v})" for k, v in info['composition'].items()])
        text = f"方剂编号：{fid}\n方剂名称：{info['name']}\n来源：{info['source']}\n组成：{composition_str}\n主治症状：{', '.join(info['indications'])}\n证型：{info['syndrome']}\n禁忌：{', '.join(info['contraindications'])}"
        
        collection.add(
            documents=[text],
            metadatas=[{
                'type': 'formula',
                'id': fid,
                'name': info['name'],
                'source': info['source'],
                'syndrome': info['syndrome'],
                'effectiveness_rate': info['effectiveness_stats']['effectiveness_rate']
            }],
            ids=[f"formula_{fid}"]
        )
        count += 1
    
    print(f"  OK 导入 {count} 个方剂")
    return count


def import_medical_cases(collection, filepath):
    """导入医案数据"""
    print(f"[导入医案] {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        cases = json.load(f)
    
    count = 0
    for case in cases:
        text = f"医案编号：{case['case_id']}\n患者：{case['patient_gender']}，{case['patient_age']}岁\n症状：{', '.join(case['symptom_names'])}\n辨证：{case['syndrome']}\n诊断：{case['diagnosis']}\n治疗：{case['treatment']}\n方剂：{case['formula_name']}\n药物：{', '.join(case['drug_names'])}\n医师：{case['doctor']}\n来源：{case['source']}\n疗效：{case['effectiveness']}\n疗程：{case['treatment_duration']}\n备注：{case['notes']}"
        
        collection.add(
            documents=[text],
            metadatas=[{
                'type': 'medical_case',
                'id': case['case_id'],
                'syndrome': case['syndrome'],
                'formula': case['formula_name'],
                'doctor': case['doctor'],
                'source': case['source'],
                'effectiveness': case['effectiveness']
            }],
            ids=[f"case_{case['case_id']}"]
        )
        count += 1
    
    print(f"  OK 导入 {count} 个医案")
    return count


def import_classical_texts(collection, filepath):
    """导入古籍条文"""
    print(f"[导入古籍] {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        texts = json.load(f)
    
    count = 0
    for text_item in texts:
        text = f"古籍条文编号：{text_item['text_id']}\n出处：{text_item['book']}·{text_item['section']}\n原文：{text_item['text']}\n关键词：{', '.join(text_item['keywords'])}"
        
        collection.add(
            documents=[text],
            metadatas=[{
                'type': 'classical_text',
                'id': text_item['text_id'],
                'book': text_item['book'],
                'section': text_item['section'],
                'symptom': text_item['symptom'],
                'source': text_item['book']
            }],
            ids=[f"text_{text_item['text_id']}"]
        )
        count += 1
    
    print(f"  OK 导入 {count} 条古籍")
    return count


def main():
    print("=" * 60)
    print("小神农中医AI - 知识库数据导入工具 v3.0")
    print("=" * 60)
    
    # 初始化ChromaDB
    chroma_dir = os.path.join(DATA_DIR, "chroma_db_v3")
    os.makedirs(chroma_dir, exist_ok=True)
    
    client = chromadb.PersistentClient(
        path=chroma_dir,
        settings=Settings(anonymized_telemetry=False)
    )
    
    # 创建或获取集合
    collection = client.get_or_create_collection(
        name="xiaoshennong_knowledge_v3",
        metadata={"description": "小神农中医AI知识库v3.0"}
    )
    
    print(f"[数据库] 路径: {chroma_dir}")
    print(f"[集合] 名称: xiaoshennong_knowledge_v3")
    print()
    
    total_count = 0
    
    # 1. 导入症状
    symptoms_file = os.path.join(RAW_DIR, 'extended_symptoms.json')
    if os.path.exists(symptoms_file):
        total_count += import_symptoms(collection, symptoms_file)
    
    # 2. 导入药物
    drugs_file = os.path.join(RAW_DIR, 'extended_drugs.json')
    if os.path.exists(drugs_file):
        total_count += import_drugs(collection, drugs_file)
    
    # 3. 导入方剂
    formulas_file = os.path.join(RAW_DIR, 'extended_formulas.json')
    if os.path.exists(formulas_file):
        total_count += import_formulas(collection, formulas_file)
    
    # 4. 导入医案（5个批次）
    for i in range(1, 6):
        cases_file = os.path.join(RAW_DIR, f'medical_cases_batch_{i}.json')
        if os.path.exists(cases_file):
            total_count += import_medical_cases(collection, cases_file)
    
    # 5. 导入古籍（5个批次）
    for i in range(1, 6):
        texts_file = os.path.join(RAW_DIR, f'classical_texts_batch_{i}.json')
        if os.path.exists(texts_file):
            total_count += import_classical_texts(collection, texts_file)
    
    # 持久化
    client.persist()
    
    # 验证
    print("\n" + "=" * 60)
    print("导入完成!")
    print(f"  总记录数: {total_count}")
    print(f"  数据库路径: {chroma_dir}")
    
    # 统计各类数据
    results = collection.get()
    type_counts = {}
    for meta in results['metadatas']:
        t = meta.get('type', 'unknown')
        type_counts[t] = type_counts.get(t, 0) + 1
    
    print("\n[数据分布]")
    for t, count in sorted(type_counts.items()):
        print(f"  {t}: {count}")
    print("=" * 60)


if __name__ == '__main__':
    main()
