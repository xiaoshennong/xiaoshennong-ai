import json
import glob
import os
from collections import defaultdict
from pathlib import Path

KG_DIR = Path("data/knowledge_graph")
DRUGS_DIR = KG_DIR / "drugs"
DRUGS_DIR.mkdir(parents=True, exist_ok=True)

CATEGORY_MAP = {
    "JB": "解表药",
    "QR": "清热药",
    "XY": "泻下药",
    "XS": "祛风湿药",
    "HS": "化湿药",
    "LS": "利水渗湿药",
    "WL": "温里药",
    "LQ": "理气药",
    "XY2": "消食药",
    "QC": "驱虫药",
    "ZX": "止血药",
    "HY": "活血化瘀药",
    "HQ": "化痰止咳平喘药",
    "AS": "安神药",
    "PG": "平肝息风药",
    "KQ": "开窍药",
    "BY": "补益药",
    "SS": "收涩药",
    "WY": "外用药",
    "QT": "其他"
}

def parse_drug_id(drug_id):
    """从DR-XX-XXX解析类别码"""
    parts = drug_id.split("-")
    if len(parts) >= 3:
        return parts[1]
    return "QT"

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    # 1. 加载现有药物
    existing = {}
    for f in glob.glob(str(DRUGS_DIR / "*.json")):
        data = load_json(f)
        existing[data["drug_id"]] = data
    print(f"现有药物: {len(existing)}")

    # 2. 从方剂收集药物信息
    drug_info = defaultdict(lambda: {
        "name": "",
        "category_code": "",
        "in_formulas": set(),
        "roles": set(),
        "doses": [],
        "treated_symptoms": set(),
        "treated_syndromes": set()
    })

    for f in glob.glob(str(KG_DIR / "formulas" / "*.json")):
        formula = load_json(f)
        fid = formula.get("formula_id")
        fname = formula.get("name")
        indications = formula.get("indications", {})
        target_symptoms = set(indications.get("symptoms", []))
        target_syndromes = set(indications.get("syndromes", []))

        for comp in formula.get("composition", []):
            did = comp.get("drug_id")
            dname = comp.get("drug_name")
            if not did:
                continue
            info = drug_info[did]
            info["name"] = dname or info["name"]
            info["category_code"] = parse_drug_id(did)
            info["in_formulas"].add(fid)
            info["roles"].add(comp.get("role", "佐"))
            if comp.get("dose_gram"):
                info["doses"].append(comp.get("dose_gram"))
            info["treated_symptoms"].update(target_symptoms)
            info["treated_syndromes"].update(target_syndromes)

    # 3. 从副作用收集信息
    adverse_by_drug = defaultdict(list)
    for f in glob.glob(str(KG_DIR / "adverse" / "*.json")):
        adv = load_json(f)
        did = adv.get("drug_id")
        if did:
            adverse_by_drug[did].append(adv)

    # 4. 生成/补全药物JSON
    created = 0
    updated = 0
    for did, info in drug_info.items():
        if did in existing:
            drug = existing[did]
            # 补全关系
            drug["relationships"] = drug.get("relationships", {})
            current_forms = set(drug["relationships"].get("in_formulas", []))
            current_forms.update(info["in_formulas"])
            drug["relationships"]["in_formulas"] = sorted(current_forms)
            updated += 1
        else:
            cat_code = info["category_code"]
            drug = {
                "$schema": "drug",
                "drug_id": did,
                "name": info["name"] or did,
                "aliases": [],
                "category": CATEGORY_MAP.get(cat_code, "其他"),
                "category_code": cat_code,
                "properties": {
                    "nature": "待补充",
                    "taste": "待补充",
                    "meridian": [],
                    "toxicity": "待确认"
                },
                "functions": [
                    {
                        "function_id": f"{did}-F1",
                        "description": "待补充",
                        "target_symptoms": sorted(info["treated_symptoms"])[:10],
                        "target_syndromes": sorted(info["treated_syndromes"])[:5],
                        "evidence_level": "B",
                        "classic_source": "从方剂组成反推"
                    }
                ],
                "dosage_reference": {
                    "classic": info["doses"][0] if info["doses"] else "待补充",
                    "modern_clinical": "待补充",
                    "max_single_dose": "待补充",
                    "administration": "煎服，遵医嘱"
                },
                "processing_methods": [],
                "clinical_stats": {
                    "total_studies": 0,
                    "total_cases": 0,
                    "effective_rate": "待补充",
                    "onset_time": "待补充",
                    "common_adverse": [
                        f"{a.get('adverse_name')}({a.get('characteristics', {}).get('incidence', '未知')})"
                        for a in adverse_by_drug.get(did, [])[:3]
                    ],
                    "serious_adverse": []
                },
                "relationships": {
                    "in_formulas": sorted(info["in_formulas"]),
                    "synergistic_with": [],
                    "antagonistic_with": [],
                    "contraindicated_with": [],
                    "similar_to": []
                },
                "contraindications": {
                    "absolute": [],
                    "relative": [],
                    "drug_interactions": []
                },
                "sources": [
                    {"type": "derived", "note": "从方剂组成反推生成，待人工审核补充"}
                ],
                "last_updated": "2025-08-01",
                "confidence": "C",
                "review_status": "auto_derived"
            }
            created += 1

        path = DRUGS_DIR / f"{did}_{drug['name']}.json"
        save_json(path, drug)

    print(f"更新现有药物: {updated}")
    print(f"新建药物档案: {created}")
    print(f"药物总数: {len(existing) + created}")

if __name__ == "__main__":
    main()
