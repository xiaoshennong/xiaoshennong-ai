#!/usr/bin/env python3
"""
小神农中医AI - 症状数据合并工具
合并原始症状(symptom_codes.py)和扩展症状(extended_symptoms.json)
"""

import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# 导入原始症状
from symptom_codes import SYMPTOM_MAP as ORIGINAL_SYMPTOMS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")

def merge_symptoms():
    """合并症状数据"""
    print("[合并] 开始合并症状数据...")
    
    # 加载扩展症状
    extended_file = os.path.join(RAW_DIR, 'extended_symptoms.json')
    with open(extended_file, 'r', encoding='utf-8') as f:
        extended = json.load(f)
    
    print(f"[原始] {len(ORIGINAL_SYMPTOMS)} 个症状")
    print(f"[扩展] {len(extended)} 个症状")
    
    # 合并（扩展覆盖原始）
    merged = dict(ORIGINAL_SYMPTOMS)
    merged.update(extended)
    
    # 保存合并后的数据
    output_file = os.path.join(RAW_DIR, 'merged_symptoms.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    
    print(f"[合并] 完成: {len(merged)} 个症状 -> {output_file}")
    return merged


def merge_drugs():
    """合并药物数据"""
    print("[合并] 开始合并药物数据...")
    
    from drug_formula_db import DRUG_DATABASE as ORIGINAL_DRUGS
    
    extended_file = os.path.join(RAW_DIR, 'extended_drugs.json')
    with open(extended_file, 'r', encoding='utf-8') as f:
        extended = json.load(f)
    
    print(f"[原始] {len(ORIGINAL_DRUGS)} 个药物")
    print(f"[扩展] {len(extended)} 个药物")
    
    merged = dict(ORIGINAL_DRUGS)
    merged.update(extended)
    
    output_file = os.path.join(RAW_DIR, 'merged_drugs.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    
    print(f"[合并] 完成: {len(merged)} 个药物 -> {output_file}")
    return merged


def merge_formulas():
    """合并方剂数据"""
    print("[合并] 开始合并方剂数据...")
    
    from drug_formula_db import FORMULA_DATABASE as ORIGINAL_FORMULAS
    
    extended_file = os.path.join(RAW_DIR, 'extended_formulas.json')
    with open(extended_file, 'r', encoding='utf-8') as f:
        extended = json.load(f)
    
    print(f"[原始] {len(ORIGINAL_FORMULAS)} 个方剂")
    print(f"[扩展] {len(extended)} 个方剂")
    
    merged = dict(ORIGINAL_FORMULAS)
    merged.update(extended)
    
    output_file = os.path.join(RAW_DIR, 'merged_formulas.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    
    print(f"[合并] 完成: {len(merged)} 个方剂 -> {output_file}")
    return merged


if __name__ == '__main__':
    merge_symptoms()
    merge_drugs()
    merge_formulas()
    print("\n[完成] 所有数据合并完成!")
