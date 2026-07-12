#!/usr/bin/env python3
"""
小神农中医AI - 快速知识库导入工具
分批导入，避免超时
"""

import os
import json
import sys
sys.dont_write_bytecode = True

import chromadb
from chromadb.config import Settings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")


def import_batch(collection, file_path, import_func, batch_size=100):
    """分批导入数据"""
    if not os.path.exists(file_path):
        print(f"[跳过] 文件不存在: {file_path}")
        return 0
    
    print(f"[导入] {os.path.basename(file_path)}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 根据数据类型处理
    if isinstance(data, dict):
        items = list(data.items())
    elif isinstance(data, list):
        items = data
    else:
        return 0
    
    total = len(items)
    imported = 0
    
    for i in range(0, total, batch_size):
        batch = items[i:i+batch_size]
        try:
            count = import_func(collection, batch)
            imported += count
            print(f"  进度: {min(i+batch_size, total)}/{total}")
        except Exception as e:
            print(f"  错误: {e}")
    
    print(f"  完成: {imported}/{total}")
    return imported


def import_symptoms_batch(collection, batch):
    """导入症状批次"""
    docs, metas, ids = [], [], []
    for sid, info in batch:
        text = f"症状: {info['name']}\n别名: {', '.join(info['aliases'])}\n出处: {', '.join(info['classic_refs'])}"
        docs.append(text)
        metas.append({'type': 'symptom', 'id': sid, 'name': info['name']})
        ids.append(f"sym_{sid}")
    collection.add(documents=docs, metadatas=metas, ids=ids)
    return len(batch)


def import_drugs_batch(collection, batch):
    """导入药物批次"""
    docs, metas, ids = [], [], []
    for did, info in batch:
        text = f"药物: {info['name']}\n性味: {info['properties']['nature']}\n归经: {info['properties']['meridian']}\n主治: {', '.join(info['indications'])}\n禁忌: {', '.join(info['contraindications'])}"
        docs.append(text)
        metas.append({'type': 'drug', 'id': did, 'name': info['name']})
        ids.append(f"drug_{did}")
    collection.add(documents=docs, metadatas=metas, ids=ids)
    return len(batch)


def import_formulas_batch(collection, batch):
    """导入方剂批次"""
    docs, metas, ids = [], [], []
    for fid, info in batch:
        comp = ', '.join([f"{k}({v})" for k, v in info['composition'].items()])
        text = f"方剂: {info['name']}\n来源: {info['source']}\n组成: {comp}\n主治: {', '.join(info['indications'])}\n证型: {info['syndrome']}"
        docs.append(text)
        metas.append({'type': 'formula', 'id': fid, 'name': info['name'], 'source': info['source']})
        ids.append(f"form_{fid}")
    collection.add(documents=docs, metadatas=metas, ids=ids)
    return len(batch)


def import_cases_batch(collection, batch):
    """导入医案批次"""
    docs, metas, ids = [], [], []
    for case in batch:
        text = f"医案: {case['case_id']}\n患者: {case['patient_gender']}{case['patient_age']}岁\n症状: {', '.join(case['symptom_names'])}\n辨证: {case['syndrome']}\n方剂: {case['formula_name']}\n疗效: {case['effectiveness']}"
        docs.append(text)
        metas.append({'type': 'case', 'id': case['case_id'], 'syndrome': case['syndrome']})
        ids.append(f"case_{case['case_id']}")
    collection.add(documents=docs, metadatas=metas, ids=ids)
    return len(batch)


def import_texts_batch(collection, batch):
    """导入古籍批次"""
    docs, metas, ids = [], [], []
    for text_item in batch:
        text = f"古籍: {text_item['book']} {text_item['section']}\n原文: {text_item['text'][:200]}"
        docs.append(text)
        metas.append({'type': 'text', 'id': text_item['text_id'], 'book': text_item['book']})
        ids.append(f"text_{text_item['text_id']}")
    collection.add(documents=docs, metadatas=metas, ids=ids)
    return len(batch)


def main():
    print("=" * 50)
    print("小神农 - 快速知识库导入")
    print("=" * 50)
    
    chroma_dir = os.path.join(DATA_DIR, "chroma_db_v3")
    os.makedirs(chroma_dir, exist_ok=True)
    
    client = chromadb.PersistentClient(
        path=chroma_dir,
        settings=Settings(anonymized_telemetry=False)
    )
    
    collection = client.get_or_create_collection(
        name="xiaoshennong_v3",
        metadata={"version": "3.0"}
    )
    
    total = 0
    
    # 导入各类数据
    files_to_import = [
        (os.path.join(RAW_DIR, 'extended_symptoms.json'), import_symptoms_batch),
        (os.path.join(RAW_DIR, 'extended_drugs.json'), import_drugs_batch),
        (os.path.join(RAW_DIR, 'extended_formulas.json'), import_formulas_batch),
    ]
    
    for filepath, func in files_to_import:
        total += import_batch(collection, filepath, func, batch_size=50)
    
    # 导入医案
    for i in range(1, 6):
        filepath = os.path.join(RAW_DIR, f'medical_cases_batch_{i}.json')
        total += import_batch(collection, filepath, import_cases_batch, batch_size=50)
    
    # 导入古籍
    for i in range(1, 6):
        filepath = os.path.join(RAW_DIR, f'classical_texts_batch_{i}.json')
        total += import_batch(collection, filepath, import_texts_batch, batch_size=50)
    
    print(f"\n[完成] 总导入: {total} 条")
    
    # 统计
    results = collection.get()
    types = {}
    for meta in results.get('metadatas', []):
        t = meta.get('type', 'unknown')
        types[t] = types.get(t, 0) + 1
    
    print("[分布]")
    for t, c in sorted(types.items()):
        print(f"  {t}: {c}")


if __name__ == '__main__':
    main()
