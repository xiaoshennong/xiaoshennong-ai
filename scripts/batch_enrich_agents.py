#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小神农中医AI · 多 Agent 批量药物增强

用法：
  python scripts/batch_enrich_agents.py --limit 10
  python scripts/batch_enrich_agents.py --drugs 麻黄,桂枝,酸枣仁,人参,甘草
  python scripts/batch_enrich_agents.py --all

说明：
  - 默认对 C 级证据的药物做增强
  - 联网搜索临床数据 → 批判评估 → 古籍佐证 → 更新 JSON
  - 实际搜索通过 WebSearch 完成，受 API 速率限制，建议分批运行
"""

import argparse
import json
import glob
import time
from pathlib import Path
from collections import Counter

# 复用单药的协调器
from kg_enrich_agent import MultiAgentKGEngine

KG_DIR = Path("data/knowledge_graph")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def select_target_drugs(engine, limit=10, evidence_filter=None, min_formulas=1):
    """选择待增强的药物"""
    candidates = []
    for did, d in engine.drugs.items():
        # 跳过已审核的 A/B 级
        if evidence_filter and d.get("confidence") not in evidence_filter:
            continue
        # 优先选择在多个方剂中出现的药物
        formula_count = len(d.get("relationships", {}).get("in_formulas", []))
        if formula_count < min_formulas:
            continue
        candidates.append((did, formula_count))

    # 按出现频次排序
    candidates.sort(key=lambda x: x[1], reverse=True)
    return [did for did, _ in candidates[:limit]]


def batch_enrich(engine, drug_ids, delay=2):
    """批量增强"""
    print(f"\n批量增强 {len(drug_ids)} 味药物...")
    success = 0
    failed = 0

    for i, did in enumerate(drug_ids, 1):
        drug = engine.drugs.get(did)
        if not drug:
            continue
        name = drug.get("name", did)
        print(f"\n[{i}/{len(drug_ids)}] 增强: {name} ({did})")
        try:
            # 找到该药物最常用的方剂作为关联
            formula_id = None
            formulas = drug.get("relationships", {}).get("in_formulas", [])
            if formulas:
                formula_id = formulas[0]

            # 找到该药物治疗的症状中第一个
            symptom_id = None
            for func in drug.get("functions", []):
                syms = func.get("target_symptoms", [])
                if syms:
                    symptom_id = syms[0]
                    break

            engine.enrich_drug(name, symptom_id, formula_id)
            success += 1
            time.sleep(delay)
        except Exception as e:
            print(f"  [ERROR] {name} 增强失败: {e}")
            failed += 1

    print(f"\n批量增强完成: 成功 {success}, 失败 {failed}")


def enrich_with_extended_data(engine):
    """用扩展数据集批量补充临床统计"""
    print("\n用扩展数据集补充药物临床统计...")
    updated = 0

    for f in glob.glob("data/raw/extended_drugs.json") + glob.glob("data/raw/merged_drugs.json"):
        if not Path(f).exists():
            continue
        data = load_json(f)
        for did, d in data.items():
            if did not in engine.drugs:
                continue
            drug = engine.drugs[did]
            stats = d.get("effectiveness_stats", {})
            if not stats:
                continue

            clinical = drug.setdefault("clinical_stats", {})
            if stats.get("total_cases"):
                clinical["total_cases"] = stats.get("total_cases")
            if stats.get("studies_count"):
                clinical["total_studies"] = stats.get("studies_count")
            if stats.get("effectiveness_rate"):
                clinical["effective_rate"] = stats.get("effectiveness_rate")
            if stats.get("side_effects"):
                side = stats.get("side_effects")
                if side and side not in clinical.get("common_adverse", []):
                    clinical.setdefault("common_adverse", []).append(side)

            # 提升证据等级
            if stats.get("evidence_level") in ["A", "B"]:
                drug["confidence"] = stats.get("evidence_level")

            drug["review_status"] = "batch_enriched"
            drug["last_updated"] = "2025-08-01"

            path = KG_DIR / "drugs" / f"{did}_{drug.get('name', did)}.json"
            save_json(path, drug)
            updated += 1

    print(f"扩展数据补充完成: {updated} 味药物")


def main():
    parser = argparse.ArgumentParser(description="批量药物增强")
    parser.add_argument("--limit", type=int, default=10, help="处理药物数量")
    parser.add_argument("--drugs", help="指定药物名，逗号分隔")
    parser.add_argument("--all", action="store_true", help="处理所有 C 级药物")
    parser.add_argument("--extended-only", action="store_true", help="仅用扩展数据补充，不联网")
    args = parser.parse_args()

    engine = MultiAgentKGEngine()

    # 第一步：用扩展数据批量补充
    enrich_with_extended_data(engine)

    if args.extended_only:
        print("\n仅使用扩展数据，跳过联网搜索")
        return

    # 第二步：联网增强
    if args.drugs:
        names = [n.strip() for n in args.drugs.split(",")]
        drug_ids = []
        for did, d in engine.drugs.items():
            if d.get("name") in names:
                drug_ids.append(did)
    elif args.all:
        drug_ids = select_target_drugs(engine, limit=9999, evidence_filter=["C"])
    else:
        drug_ids = select_target_drugs(engine, limit=args.limit, evidence_filter=["C"])

    if not drug_ids:
        print("没有需要增强的药物")
        return

    print(f"\n选中药物: {len(drug_ids)} 味")
    batch_enrich(engine, drug_ids)


if __name__ == "__main__":
    main()
