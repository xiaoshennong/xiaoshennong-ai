#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小神农中医AI · 扩展知识图谱数据导入

将 data/raw/ 下的扩展数据导入到 data/knowledge_graph/ 结构化图谱中。
来源：
  - data/raw/extended_drugs.json
  - data/raw/extended_symptoms.json
  - data/raw/extended_formulas.json
  - data/raw/merged_drugs.json
  - data/raw/merged_symptoms.json
  - data/raw/merged_formulas.json
"""

import json
import glob
from pathlib import Path
from collections import defaultdict

KG_DIR = Path("data/knowledge_graph")
RAW_DIR = Path("data/raw")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_drug(drug_id, d):
    """将扩展药物数据转为标准 drug schema"""
    stats = d.get("effectiveness_stats", {})
    return {
        "$schema": "drug",
        "drug_id": drug_id,
        "name": d.get("name", drug_id),
        "aliases": d.get("aliases", []),
        "category": d.get("category", "其他"),
        "category_code": drug_id.split("-")[1] if "-" in drug_id else "QT",
        "properties": {
            "nature": d.get("properties", {}).get("nature", "待补充"),
            "taste": d.get("properties", {}).get("taste", "待补充"),
            "meridian": d.get("properties", {}).get("meridian", "").replace("、", ",").split(",") if isinstance(d.get("properties", {}).get("meridian", ""), str) else d.get("properties", {}).get("meridian", []),
            "toxicity": d.get("properties", {}).get("toxicity", "待确认")
        },
        "functions": [
            {
                "function_id": f"{drug_id}-F1",
                "description": "扩展数据导入",
                "target_symptoms": d.get("indications", []),
                "target_syndromes": [],
                "evidence_level": stats.get("evidence_level", "C"),
                "classic_source": "扩展数据集"
            }
        ],
        "dosage_reference": {
            "classic": d.get("dosage", "待补充"),
            "modern_clinical": d.get("dosage", "待补充"),
            "max_single_dose": "待补充",
            "administration": "煎服，遵医嘱"
        },
        "processing_methods": [],
        "clinical_stats": {
            "total_studies": stats.get("studies_count", 0),
            "total_cases": stats.get("total_cases", 0),
            "effective_rate": stats.get("effectiveness_rate", "待补充"),
            "onset_time": "待补充",
            "common_adverse": [stats.get("side_effects", "")] if stats.get("side_effects") else [],
            "serious_adverse": []
        },
        "relationships": {
            "in_formulas": d.get("classic_formulas", []),
            "synergistic_with": [],
            "antagonistic_with": [],
            "contraindicated_with": [],
            "similar_to": []
        },
        "contraindications": {
            "absolute": d.get("contraindications", []),
            "relative": [],
            "drug_interactions": []
        },
        "sources": d.get("sources", [{"type": "extended", "note": "从扩展数据集导入"}]),
        "last_updated": "2025-08-01",
        "confidence": stats.get("evidence_level", "C"),
        "review_status": "auto_imported"
    }


def normalize_symptom(symptom_id, s):
    """将扩展症状数据转为标准 symptom schema"""
    parts = symptom_id.split("-")
    location_code = parts[1] if len(parts) >= 2 else "QT"
    type_code = parts[2] if len(parts) >= 3 else "Z"
    return {
        "symptom_id": symptom_id,
        "name": s.get("name", symptom_id),
        "aliases": s.get("aliases", []),
        "location": s.get("location", ""),
        "location_code": location_code,
        "type": "自觉症状" if type_code == "Z" else ("体征" if type_code == "T" else "复合症状"),
        "type_code": type_code,
        "description": s.get("description", ""),
        "differentiation": {
            "key_points": s.get("differentiation", []),
            "related_symptoms": s.get("related_symptoms", [])
        },
        "classic_mapping": {ref: ref for ref in s.get("classic_refs", [])},
        "treating_drugs": [],
        "treating_formulas": [],
        "modern_equivalent": s.get("modern_equivalent", ""),
        "severity_scale": s.get("severity_scale", {})
    }


def normalize_formula(formula_id, f):
    """将扩展方剂数据转为标准 formula schema"""
    composition = []
    for did, dname in f.get("composition", {}).items():
        composition.append({
            "drug_id": did,
            "drug_name": dname,
            "dose": "待补充",
            "dose_gram": "待补充",
            "role": "待补充"
        })
    stats = f.get("effectiveness_stats", {})
    return {
        "formula_id": formula_id,
        "name": f.get("name", formula_id),
        "source": f.get("source", "待补充"),
        "chapter": "",
        "article": "",
        "classification": {
            "main": f.get("classification", {}).get("main", "待分类"),
            "sub": f.get("classification", {}).get("sub", "")
        },
        "composition": composition,
        "total_herbs": len(composition),
        "preparation": f.get("preparation", "待补充"),
        "administration": f.get("administration", "待补充"),
        "indications": {
            "syndromes": [f["syndrome"]] if f.get("syndrome") else [],
            "symptoms": f.get("indications", []),
            "description": "、".join(f.get("symptoms", []))
        },
        "effects": {
            "main": f.get("effects", {}).get("main", "待补充"),
            "modern_research": f.get("effects", {}).get("modern_research", [])
        },
        "contraindications": {
            "absolute": f.get("contraindications", []),
            "relative": []
        },
        "clinical_stats": {
            "total_studies": stats.get("studies_count", 0),
            "total_cases": stats.get("total_cases", 0),
            "effective_rate": stats.get("effectiveness_rate", "待补充"),
            "onset_time": "待补充",
            "course": "待补充"
        },
        "variations": f.get("variations", [])
    }


def import_file(src_path, target_dir, normalize_fn, id_field):
    """通用导入函数"""
    if not src_path.exists():
        print(f"[SKIP] 不存在: {src_path}")
        return 0

    data = load_json(src_path)
    if not isinstance(data, dict):
        print(f"[SKIP] 格式不支持: {src_path} ({type(data)})")
        return 0

    count = 0
    for entity_id, entity_data in data.items():
        target_path = target_dir / f"{entity_id}_{entity_data.get('name', entity_id)}.json"
        if target_path.exists():
            # 合并而不是覆盖：保留更高级别的证据
            existing = load_json(target_path)
            if existing.get("confidence") in ["A", "B"]:
                continue

        normalized = normalize_fn(entity_id, entity_data)
        save_json(target_path, normalized)
        count += 1

    print(f"[IMPORT] {src_path} -> {target_dir}: {count} 条")
    return count


def build_reverse_index():
    """建立症状/药物/方剂之间的反向索引"""
    drugs = {}
    symptoms = {}
    formulas = {}

    for f in glob.glob(str(KG_DIR / "drugs" / "*.json")):
        d = load_json(f)
        drugs[d["drug_id"]] = d

    for f in glob.glob(str(KG_DIR / "symptoms" / "*.json")):
        s = load_json(f)
        if "symptom_id" in s:
            symptoms[s["symptom_id"]] = s

    for f in glob.glob(str(KG_DIR / "formulas" / "*.json")):
        fo = load_json(f)
        if "formula_id" in fo:
            formulas[fo["formula_id"]] = fo

    # 药物 -> 治疗症状
    drug_to_symptoms = defaultdict(set)
    drug_to_formulas = defaultdict(set)
    for did, d in drugs.items():
        for func in d.get("functions", []):
            drug_to_symptoms[did].update(func.get("target_symptoms", []))
        drug_to_formulas[did].update(d.get("relationships", {}).get("in_formulas", []))

    # 方剂 -> 组成药物，主治症状
    formula_to_drugs = defaultdict(set)
    formula_to_symptoms = defaultdict(set)
    for fid, fo in formulas.items():
        for comp in fo.get("composition", []):
            formula_to_drugs[fid].add(comp.get("drug_id"))
        formula_to_symptoms[fid].update(fo.get("indications", {}).get("symptoms", []))

    # 更新症状节点的 treating_drugs / treating_formulas
    for did, sym_ids in drug_to_symptoms.items():
        for sid in sym_ids:
            if sid in symptoms:
                symptoms[sid].setdefault("treating_drugs", [])
                if not any(x.get("drug_id") == did for x in symptoms[sid]["treating_drugs"]):
                    symptoms[sid]["treating_drugs"].append({
                        "drug_id": did,
                        "drug_name": drugs[did].get("name", did),
                        "evidence": drugs[did].get("confidence", "C")
                    })

    for fid, sym_ids in formula_to_symptoms.items():
        for sid in sym_ids:
            if sid in symptoms:
                symptoms[sid].setdefault("treating_formulas", [])
                if not any(x.get("formula_id") == fid for x in symptoms[sid]["treating_formulas"]):
                    symptoms[sid]["treating_formulas"].append({
                        "formula_id": fid,
                        "formula_name": formulas[fid].get("name", fid),
                        "evidence": "B"
                    })

    # 更新药物节点的 in_formulas
    for fid, drug_ids in formula_to_drugs.items():
        for did in drug_ids:
            if did in drugs:
                drugs[did].setdefault("relationships", {})
                drugs[did]["relationships"].setdefault("in_formulas", [])
                if fid not in drugs[did]["relationships"]["in_formulas"]:
                    drugs[did]["relationships"]["in_formulas"].append(fid)

    # 保存更新
    for did, d in drugs.items():
        save_json(KG_DIR / "drugs" / f"{did}_{d.get('name', did)}.json", d)
    for sid, s in symptoms.items():
        save_json(KG_DIR / "symptoms" / f"{sid}_{s.get('name', sid)}.json", s)

    print(f"[INDEX] 反向索引完成: {len(drugs)}药, {len(symptoms)}症状, {len(formulas)}方剂")


def main():
    print("=" * 70)
    print("扩展知识图谱数据导入")
    print("=" * 70)

    total = 0
    total += import_file(RAW_DIR / "extended_drugs.json", KG_DIR / "drugs", normalize_drug, "drug_id")
    total += import_file(RAW_DIR / "extended_symptoms.json", KG_DIR / "symptoms", normalize_symptom, "symptom_id")
    total += import_file(RAW_DIR / "extended_formulas.json", KG_DIR / "formulas", normalize_formula, "formula_id")
    total += import_file(RAW_DIR / "merged_drugs.json", KG_DIR / "drugs", normalize_drug, "drug_id")
    total += import_file(RAW_DIR / "merged_symptoms.json", KG_DIR / "symptoms", normalize_symptom, "symptom_id")
    total += import_file(RAW_DIR / "merged_formulas.json", KG_DIR / "formulas", normalize_formula, "formula_id")

    print(f"\n[TOTAL] 新导入/更新: {total} 条")

    # 建立反向索引
    build_reverse_index()

    print("\n[SUCCESS] 扩展数据导入完成")
    print("提示：运行 python scripts/export_kg_for_viz.py 重新生成可视化数据")


if __name__ == "__main__":
    main()
