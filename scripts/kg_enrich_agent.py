#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小神农中医AI · 多 Agent 知识图谱扩展协调器

模拟/执行多 Agent 协作工作流：
  搜索 Agent → 批判 Agent → 古籍 Agent → 症状/药物/方剂 Agent → 副作用 Agent → 入库 Agent

用法：
  python kg_enrich_agent.py --drug 酸枣仁 --symptom 失眠
  python kg_enrich_agent.py --formula 酸枣仁汤
"""

import argparse
import json
import glob
from pathlib import Path
from datetime import datetime
from collections import defaultdict

KG_DIR = Path(__file__).parent.parent / "data" / "knowledge_graph"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class MultiAgentKGEngine:
    """多 Agent 知识图谱扩展引擎"""

    def __init__(self, kg_dir=None):
        self.kg_dir = Path(kg_dir) if kg_dir else KG_DIR
        self.drugs = {}
        self.symptoms = {}
        self.formulas = {}
        self.load_kg()

    def load_kg(self):
        for f in glob.glob(str(self.kg_dir / "drugs" / "*.json")):
            d = load_json(f)
            self.drugs[d.get("drug_id")] = d
        for f in glob.glob(str(self.kg_dir / "symptoms" / "*.json")):
            d = load_json(f)
            if "symptom_id" in d:
                self.symptoms[d["symptom_id"]] = d
        for f in glob.glob(str(self.kg_dir / "formulas" / "*.json")):
            d = load_json(f)
            if "formula_id" in d:
                self.formulas[d["formula_id"]] = d
        print(f"[协调器] 已加载: {len(self.drugs)}药, {len(self.symptoms)}症状, {len(self.formulas)}方剂")

    # --------------------------------------------------------
    # Agent 1: 搜索 Agent（模拟输出，可替换为真实 API）
    # --------------------------------------------------------
    def search_agent(self, query, entity_type="drug"):
        """
        搜索 Agent：返回候选临床数据列表
        实际部署时，此处应调用：
          - WebSearch / PubMed API / CNKI API
          - 中医古籍数据库
          - 不良反应数据库
        """
        print(f"\n[搜索 Agent] 正在检索: {query}")
        # 模拟搜索结果（以酸枣仁为例）
        if "酸枣仁" in query:
            return [
                {
                    "source": "233网校执业药师",
                    "url": "https://www.233.com/yaoshi/zhongyao/one/20060810/102923353-4.html",
                    "title": "中药学辅导：酸枣仁",
                    "key_data": "治疗失眠87例，有效率73.5%，生炒同效",
                    "sample_size": 87,
                    "evidence_level": "观察性研究"
                },
                {
                    "source": "TCM杂志综述",
                    "url": "https://tcm-magazine.com/artikel.php?lang=zh&slug=中医药治疗失眠&dr=1",
                    "title": "中医药治疗失眠",
                    "key_data": "2025年荟萃分析纳入32项研究，酸枣仁汤总有效率优于苯二氮卓类",
                    "sample_size": 0,
                    "evidence_level": "Meta分析"
                },
                {
                    "source": "百度健康科普",
                    "url": "https://health.baidu.com/m/detail/ar_6671168240880177038",
                    "title": "酸枣仁治疗失眠的效果",
                    "key_data": "皂苷、黄酮通过GABA受体起镇静作用",
                    "sample_size": 0,
                    "evidence_level": "科普"
                }
            ]
        # 默认返回空，提示需要真实搜索
        return []

    # --------------------------------------------------------
    # Agent 2: 批判 Agent
    # --------------------------------------------------------
    def critical_agent(self, candidates):
        """
        批判 Agent：三阶九维可信度评估
        """
        print("\n[批判 Agent] 开始三阶九维评估...")
        results = []
        for item in candidates:
            # 简化的评分逻辑
            source_score = 3 if "Meta" in item["evidence_level"] else 2
            content_score = 4 if "荟萃" in item["key_data"] or item["sample_size"] >= 100 else 3
            if item["sample_size"] == 0:
                content_score = 2
            applicability_score = 5  # 假设症状匹配

            avg = (source_score + content_score + applicability_score) / 3
            if avg >= 4.5:
                grade = "A"
            elif avg >= 3.5:
                grade = "B"
            elif avg >= 2.5:
                grade = "C"
            else:
                grade = "D"

            result_item = {
                **item,
                "scores": {
                    "source": source_score,
                    "content": content_score,
                    "applicability": applicability_score
                },
                "average": round(avg, 2),
                "grade": grade,
                "adopt": grade in ["A", "B"]
            }
            results.append(result_item)
            print(f"  - {result_item['source']}: {result_item['average']}分 → {result_item['grade']}级")
        return results

    # --------------------------------------------------------
    # Agent 3: 古籍 Agent
    # --------------------------------------------------------
    def classic_agent(self, drug_name, symptom_name):
        """
        古籍 Agent：在知识库和经典条文里寻找佐证
        """
        print("\n[古籍 Agent] 检索古籍佐证...")
        evidence = []

        # 简单内置映射（实际应从 classics/ 目录加载）
        classic_db = {
            "酸枣仁": [
                {"book": "金匮要略", "text": "虚劳虚烦不得眠，酸枣仁汤主之", "strength": "强佐证"},
                {"book": "神农本草经", "text": "主心腹寒热，邪结气聚，四肢酸疼，湿痹", "strength": "弱佐证"}
            ]
        }

        for drug, records in classic_db.items():
            if drug in drug_name:
                evidence.extend(records)

        # 从现有方剂数据中寻找佐证
        for fid, formula in self.formulas.items():
            comp_names = [c.get("drug_name", "") for c in formula.get("composition", [])]
            if drug_name in comp_names:
                evidence.append({
                    "book": formula.get("source", "未知"),
                    "text": f"{formula.get('name')} 含 {drug_name}",
                    "strength": "强佐证"
                })

        print(f"  找到 {len(evidence)} 条古籍/方剂佐证")
        return evidence

    # --------------------------------------------------------
    # Agent 4-6: 实体 Agent
    # --------------------------------------------------------
    def drug_agent(self, drug_name, clinical_items, classic_evidence):
        """药物 Agent：生成/更新药物 JSON"""
        print(f"\n[药物 Agent] 更新药物档案: {drug_name}")
        drug_id = None
        for did, d in self.drugs.items():
            if d.get("name") == drug_name:
                drug_id = did
                break

        if not drug_id:
            print(f"  未找到药物 {drug_name}，请先分配编码")
            return None

        drug = self.drugs[drug_id]
        # 确保 clinical_stats 存在
        if "clinical_stats" not in drug:
            drug["clinical_stats"] = {
                "total_studies": 0,
                "total_cases": 0,
                "effective_rate": "待补充",
                "onset_time": "待补充",
                "common_adverse": [],
                "serious_adverse": []
            }
        # 统计有效率和样本量
        effective_rates = []
        total_cases = 0
        for item in clinical_items:
            if item.get("adopt"):
                # 从 key_data 中粗略提取数字
                import re
                nums = re.findall(r'(\d+(?:\.\d+)?)%', item["key_data"])
                if nums:
                    effective_rates.append(float(nums[0]))
                if item.get("sample_size", 0) > 0:
                    total_cases += item["sample_size"]

        if effective_rates:
            drug["clinical_stats"]["effective_rate"] = f"{sum(effective_rates)/len(effective_rates):.1f}%"
        if total_cases > 0:
            drug["clinical_stats"]["total_cases"] = total_cases

        # 添加来源
        for item in clinical_items:
            if item.get("adopt"):
                drug.setdefault("sources", []).append({
                    "type": "clinical",
                    "source": item["source"],
                    "url": item["url"],
                    "key_data": item["key_data"],
                    "grade": item["grade"]
                })

        drug["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        drug["review_status"] = "agent_enriched"
        return drug

    def symptom_agent(self, symptom_name):
        """症状 Agent：查找/分配症状编号"""
        print(f"\n[症状 Agent] 查找症状: {symptom_name}")
        for sid, s in self.symptoms.items():
            if s.get("name") == symptom_name:
                print(f"  找到编号: {sid}")
                return s
        print(f"  未找到症状 {symptom_name}，需要新建 SN 编码")
        return None

    def formula_agent(self, formula_name):
        """方剂 Agent：查找方剂"""
        print(f"\n[方剂 Agent] 查找方剂: {formula_name}")
        for fid, f in self.formulas.items():
            if f.get("name") == formula_name:
                print(f"  找到编号: {fid}")
                return f
        return None

    # --------------------------------------------------------
    # Agent 7: 副作用 Agent
    # --------------------------------------------------------
    def adverse_agent(self, drug_id, drug_name):
        """副作用 Agent：收集已知副作用"""
        print(f"\n[副作用 Agent] 检索 {drug_name} 副作用...")
        adverse_dir = self.kg_dir / "adverse"
        adverse_list = []
        for f in glob.glob(str(adverse_dir / f"AD-{drug_id}-*.json")):
            adv = load_json(f)
            adverse_list.append(adv)
        print(f"  找到 {len(adverse_list)} 条副作用记录")
        return adverse_list

    # --------------------------------------------------------
    # Agent 8: 入库 Agent
    # --------------------------------------------------------
    def ingest_agent(self, drug):
        """入库 Agent：保存更新后的药物档案"""
        print("\n[入库 Agent] 审核并归档...")
        if drug.get("confidence") == "C" and drug.get("review_status") == "auto_derived":
            print("  [警告] 该药物为自动推导的 C 级数据，建议人工审核后再提升等级")
        else:
            print("  [通过] 数据通过初筛，准备归档")

        path = self.kg_dir / "drugs" / f"{drug['drug_id']}_{drug['name']}.json"
        save_json(path, drug)
        print(f"  已保存: {path}")

    # --------------------------------------------------------
    # 主流程
    # --------------------------------------------------------
    def enrich_drug(self, drug_name, symptom_name=None, formula_name=None):
        """完整的药物增强工作流"""
        print("=" * 70)
        print(f"多 Agent 知识图谱扩展 · 目标: {drug_name}")
        print("=" * 70)

        # Step 1-2: 搜索
        candidates = self.search_agent(drug_name)
        if not candidates:
            print("未找到在线数据，工作流终止。请配置真实搜索 API。")
            return

        # Step 3: 批判评估
        evaluated = self.critical_agent(candidates)

        # Step 4: 古籍佐证
        classic_evidence = self.classic_agent(drug_name, symptom_name or "")

        # Step 5: 实体更新
        drug = self.drug_agent(drug_name, evaluated, classic_evidence)
        if symptom_name:
            self.symptom_agent(symptom_name)
        if formula_name:
            self.formula_agent(formula_name)

        # Step 6: 副作用
        if drug:
            self.adverse_agent(drug["drug_id"], drug_name)
            self.ingest_agent(drug)

        # 输出报告
        print("\n" + "=" * 70)
        print("扩展报告")
        print("=" * 70)
        adopted = [e for e in evaluated if e.get("adopt")]
        print(f"采用文献: {len(adopted)}/{len(evaluated)}")
        print(f"古籍佐证: {len(classic_evidence)}条")
        if drug:
            print(f"更新药物: {drug['drug_id']} {drug['name']}")
            print(f"有效率: {drug['clinical_stats'].get('effective_rate', '-')}")
            print(f"样本量: {drug['clinical_stats'].get('total_cases', 0)}例")
        print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="多 Agent 知识图谱扩展")
    parser.add_argument("--drug", help="目标药物名称")
    parser.add_argument("--symptom", help="关联症状名称")
    parser.add_argument("--formula", help="关联方剂名称")
    args = parser.parse_args()

    engine = MultiAgentKGEngine()

    if args.drug:
        engine.enrich_drug(args.drug, args.symptom, args.formula)
    else:
        # 默认演示：酸枣仁
        engine.enrich_drug("酸枣仁", "失眠", "酸枣仁汤")


if __name__ == "__main__":
    main()
