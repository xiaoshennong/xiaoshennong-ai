import json
import glob
from pathlib import Path
from collections import defaultdict

KG_DIR = Path("data/knowledge_graph")
OUT_PATH = Path("data/kg_graph.json")

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    nodes = []
    links = []
    node_ids = set()

    # 加载所有实体
    drugs = {}
    for f in glob.glob(str(KG_DIR / "drugs" / "*.json")):
        d = load_json(f)
        drugs[d["drug_id"]] = d
        node = {
            "id": d["drug_id"],
            "label": d.get("name", d["drug_id"]),
            "type": "drug",
            "category": d.get("category", "其他"),
            "category_code": d.get("category_code", "QT"),
            "confidence": d.get("confidence", "C"),
            "review_status": d.get("review_status", "manual"),
            "properties": d.get("properties", {}),
            "clinical_stats": d.get("clinical_stats", {})
        }
        nodes.append(node)
        node_ids.add(d["drug_id"])

    symptoms = {}
    for f in glob.glob(str(KG_DIR / "symptoms" / "*.json")):
        d = load_json(f)
        if "symptom_id" not in d:
            continue
        symptoms[d["symptom_id"]] = d
        node = {
            "id": d["symptom_id"],
            "label": d.get("name", d["symptom_id"]),
            "type": "symptom",
            "location": d.get("location", ""),
            "location_code": d.get("location_code", ""),
            "symptom_type": d.get("type", "")
        }
        nodes.append(node)
        node_ids.add(d["symptom_id"])

    syndromes = {}
    for f in glob.glob(str(KG_DIR / "syndromes" / "*.json")):
        d = load_json(f)
        if "syndrome_id" not in d:
            continue
        syndromes[d["syndrome_id"]] = d
        node = {
            "id": d["syndrome_id"],
            "label": d.get("name", d["syndrome_id"]),
            "type": "syndrome",
            "system": d.get("system", ""),
            "treatment_principle": d.get("treatment_principle", "")
        }
        nodes.append(node)
        node_ids.add(d["syndrome_id"])

    formulas = {}
    for f in glob.glob(str(KG_DIR / "formulas" / "*.json")):
        d = load_json(f)
        if "formula_id" not in d:
            continue
        formulas[d["formula_id"]] = d
        node = {
            "id": d["formula_id"],
            "label": d.get("name", d["formula_id"]),
            "type": "formula",
            "source": d.get("source", ""),
            "classification": d.get("classification", {})
        }
        nodes.append(node)
        node_ids.add(d["formula_id"])

    patients = {}
    for f in glob.glob(str(KG_DIR / "patients" / "*.json")):
        d = load_json(f)
        if "patient_id" not in d:
            continue
        patients[d["patient_id"]] = d
        node = {
            "id": d["patient_id"],
            "label": d.get("patient_id", ""),
            "type": "patient",
            "chief_complaint": d.get("medical_history", {}).get("chief_complaint", "")
        }
        nodes.append(node)
        node_ids.add(d["patient_id"])

    # 建立关系
    # 1. 药物 → 组成 → 方剂
    for fid, d in formulas.items():
        for comp in d.get("composition", []):
            did = comp.get("drug_id")
            if did and did in node_ids and fid in node_ids:
                links.append({
                    "source": did,
                    "target": fid,
                    "relation": "组成",
                    "role": comp.get("role", "佐"),
                    "dose": comp.get("dose_gram", "")
                })

    # 2. 方剂 → 主治 → 症状/证型
    for fid, d in formulas.items():
        ind = d.get("indications", {})
        for sid in ind.get("symptoms", []):
            if sid in node_ids and fid in node_ids:
                links.append({"source": fid, "target": sid, "relation": "主治症状"})
        for sid in ind.get("syndromes", []):
            if sid in node_ids and fid in node_ids:
                links.append({"source": fid, "target": sid, "relation": "主治证型"})

    # 3. 药物 → 治疗 → 症状
    for did, d in drugs.items():
        for func in d.get("functions", []):
            for sid in func.get("target_symptoms", []):
                if sid in node_ids and did in node_ids:
                    links.append({
                        "source": did,
                        "target": sid,
                        "relation": "治疗",
                        "function": func.get("description", ""),
                        "evidence": func.get("evidence_level", "C")
                    })

    # 4. 药物 → 治疗 → 证型
    for did, d in drugs.items():
        for func in d.get("functions", []):
            for sid in func.get("target_syndromes", []):
                if sid in node_ids and did in node_ids:
                    links.append({
                        "source": did,
                        "target": sid,
                        "relation": "治疗证型",
                        "function": func.get("description", ""),
                        "evidence": func.get("evidence_level", "C")
                    })

    # 5. 副作用: 药物 → 导致 → 症状
    for f in glob.glob(str(KG_DIR / "adverse" / "*.json")):
        d = load_json(f)
        did = d.get("drug_id")
        sid = d.get("adverse_symptom")
        if did in node_ids and sid in node_ids:
            links.append({
                "source": did,
                "target": sid,
                "relation": "副作用",
                "adverse_name": d.get("adverse_name", ""),
                "incidence": d.get("characteristics", {}).get("incidence", "未知"),
                "severity": d.get("characteristics", {}).get("severity", "未知")
            })

    # 6. 症状共现
    cooccur_path = KG_DIR / "cooccur" / "cooccur.json"
    if cooccur_path.exists():
        cooccur = load_json(cooccur_path)
        for c in cooccur.get("cooccur_network", []):
            a = c.get("symptom_a")
            b = c.get("symptom_b")
            if a in node_ids and b in node_ids:
                links.append({
                    "source": a,
                    "target": b,
                    "relation": "共现",
                    "strength": c.get("strength", 0),
                    "type": c.get("type", "")
                })

    # 7. 患者 → 出现 → 症状
    for pid, d in patients.items():
        for sid in d.get("tcm_assessment", {}).get("symptoms", []):
            if sid in node_ids and pid in node_ids:
                links.append({"source": pid, "target": sid, "relation": "患者症状"})
        # 患者用药
        for event in d.get("treatment_timeline", []):
            for did in event.get("prescription", {}).get("drugs", []):
                if did in node_ids and pid in node_ids:
                    links.append({"source": pid, "target": did, "relation": "患者用药"})
        # 相似患者
        for sid in d.get("similar_patients", []):
            if sid in node_ids and pid in node_ids:
                links.append({"source": pid, "target": sid, "relation": "相似患者"})

    # 8. 十八反/十九畏/七情配伍
    for name, rel_name in [("18fan", "十八反"), ("19wei", "十九畏"), ("7qing", "七情配伍")]:
        path = KG_DIR / "relationships" / f"{name}.json"
        if path.exists():
            data = load_json(path)
            for rule in data.get("rules", []):
                a = rule.get("drug_a")
                bs = rule.get("drug_b_list", [rule.get("drug_b")])
                for b in bs:
                    if a and b and a in node_ids and b in node_ids:
                        links.append({
                            "source": a,
                            "target": b,
                            "relation": rel_name,
                            "rule_id": rule.get("rule_id", ""),
                            "severity": rule.get("severity", ""),
                            "type": rule.get("type", "")
                        })

    graph = {
        "metadata": {
            "version": "2.0",
            "generated_at": "2025-08-01",
            "node_count": len(nodes),
            "link_count": len(links),
            "node_types": defaultdict(int),
            "relation_types": defaultdict(int)
        },
        "nodes": nodes,
        "links": links
    }

    # 统计
    for n in nodes:
        graph["metadata"]["node_types"][n["type"]] += 1
    for l in links:
        graph["metadata"]["relation_types"][l["relation"]] += 1

    graph["metadata"]["node_types"] = dict(graph["metadata"]["node_types"])
    graph["metadata"]["relation_types"] = dict(graph["metadata"]["relation_types"])

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)

    print(f"导出完成: {OUT_PATH}")
    print(f"节点数: {len(nodes)}")
    print(f"关系数: {len(links)}")
    print(f"节点类型: {graph['metadata']['node_types']}")
    print(f"关系类型: {graph['metadata']['relation_types']}")

if __name__ == "__main__":
    main()
