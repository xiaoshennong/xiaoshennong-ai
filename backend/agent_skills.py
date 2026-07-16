#!/usr/bin/env python3
"""
小神农中医AI - Agent 技能注册表
为 7 个多 Agent 提供基于 Yunwu API 的结构化生成能力。
"""

import json
import os
import re
import urllib.request
import urllib.error
from typing import Dict, Optional

from llm_client_yunwu import YunwuAIClient, get_llm_client


class AgentLLM:
    """
    面向 Agent 的 Yunwu API 封装。
    支持普通文本生成与结构化 JSON 生成，所有 API 密钥均通过 llm_client_yunwu
    从环境变量读取，不内置任何密钥。
    """

    def __init__(self, client: Optional[YunwuAIClient] = None):
        if client is None:
            # 始终使用 Yunwu（OpenAI 兼容）客户端
            client = get_llm_client("yunwu")
        if not isinstance(client, YunwuAIClient):
            # 如果 get_llm_client 因环境配置返回其他客户端，则强制创建 Yunwu 客户端
            client = YunwuAIClient()
        self.client = client

    def generate(self, system_prompt: str, user_prompt: str,
                 temperature: float = 0.3, max_tokens: int = 2000) -> str:
        """调用 Yunwu API 生成文本。"""
        if not self.client.api_key:
            raise RuntimeError("未配置 YUNWU_API_KEY，无法调用 Yunwu API")

        url = f"{self.client.base_url}/chat/completions"
        payload = {
            "model": self.client.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        # 若服务端支持 JSON 模式则启用
        try:
            payload["response_format"] = {"type": "json_object"}
        except Exception:
            pass

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.client.api_key}",
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if not data.get("choices"):
            raise RuntimeError(f"Yunwu API 返回异常: {data}")
        return data["choices"][0]["message"]["content"]

    def generate_json(self, system_prompt: str, user_prompt: str,
                      output_schema: dict, temperature: float = 0.2,
                      max_tokens: int = 3000) -> dict:
        """
        调用 Yunwu API 并返回解析后的 JSON 字典。
        output_schema 会附加在用户提示中，用于指导模型输出结构。
        """
        schema_text = json.dumps(output_schema, ensure_ascii=False, indent=2)
        full_user_prompt = (
            f"{user_prompt}\n\n"
            f"请严格遵循以下 JSON 结构输出，只返回合法的 JSON 对象，"
            f"不要 Markdown 代码块、不要解释说明。"
            f"对无法确认的内容使用空字符串或空数组，禁止编造。\n\n"
            f"JSON 结构说明：\n{schema_text}"
        )
        text = self.generate(system_prompt, full_user_prompt, temperature, max_tokens)
        text = text.strip()

        # 去除 Markdown 代码块包裹
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)

        return json.loads(text)


# ---------- 1. 药物技能 ----------
_DRUG_SYSTEM_PROMPT = """你是一名资深中药学知识工程师，深耕《神农本草经》《本草纲目》《中华人民共和国药典》《中药学》等权威典籍。
你的任务是为给定中药生成一份结构完整、术语规范、可用于中医 AI 知识库的数字药物档案。

请严格遵守：
1. 只输出合法 JSON，禁止 Markdown 代码块、禁止解释性文字；
2. 性味归经、功效主治、用法用量、炮制、禁忌、注意事项需符合权威教材与药典表述；
3. 毒性字段仅允许填写：无毒、小毒、有毒、大毒、剧毒；
4. 经典来源请尽量标注书名与篇章；
5. 现代研究可填写主要化学成分、药理作用、临床研究、参考文献；
6. 对不确定或缺乏权威依据的内容使用空字符串或空数组，禁止编造。"""

_DRUG_OUTPUT_SCHEMA = {
    "drug_id": "药物编码（可留空）",
    "name": "药物正名",
    "aliases": ["别名、异名"],
    "category": "药物分类，如解表药、清热药、补益药等",
    "properties": {
        "nature": "四气，如温、热、寒、凉、平",
        "taste": "五味，如辛、甘、苦、酸、咸",
        "meridian": ["归经，如肺、膀胱"],
        "toxicity": "无毒/小毒/有毒/大毒/剧毒"
    },
    "effects": ["功效，如发汗解表、宣肺平喘"],
    "indications": ["主治，如风寒感冒、咳嗽气喘"],
    "usage": {
        "dosage": "常规用量",
        "preparation": "炮制方法",
        "administration": "煎服、外用等用法",
        "contraindications": ["禁忌证"],
        "precautions": ["注意事项、特殊人群提醒"]
    },
    "modern_research": {
        "active_compounds": ["主要化学成分"],
        "pharmacology": ["药理作用"],
        "clinical_studies": ["临床研究要点"],
        "references": ["权威参考文献"]
    },
    "source_classics": ["经典来源，如《神农本草经·中品》"],
    "quality_standards": {
        "origin": ["道地产区"],
        "harvest_season": "采收季节",
        "processing": "加工方法",
        "storage": "贮藏条件"
    },
    "relations": {
        "related_formulas": ["相关方剂"],
        "synergistic_drugs": ["相须相使药物"],
        "antagonistic_drugs": ["相反相畏药物"],
        "contraindicated_drugs": ["配伍禁忌药物"]
    }
}


def _drug_user_prompt(drug_name: str, **kwargs) -> str:
    return (
        f"请为中药【{drug_name}】生成完整的数字化药物档案。\n"
        f"要求覆盖性味归经、功效主治、用法用量、炮制、禁忌、现代研究、"
        f"质量标准、经典来源及药物关系。"
    )


# ---------- 2. 症状技能 ----------
_SYMPTOM_SYSTEM_PROMPT = """你是一名中医诊断学专家，擅长症状学、证候学与现代医学对应分析。
你的任务是根据给定的症状名称，生成一个结构化的中医症状节点，用于症状知识图谱与辨证系统。

请严格遵守：
1. 只输出合法 JSON，禁止 Markdown 代码块、禁止解释性文字；
2. 症状定义应简明、专业，符合中医诊断学术语；
3. common_syndromes 列出最常见证型及出现频率（常见/偶见/罕见）；
4. differentiation_points 提供与相似症状的鉴别要点；
5. modern_mapping 给出可能对应的现代医学病名与检查建议；
6. 对不确定的内容使用空字符串或空数组，禁止编造。"""

_SYMPTOM_OUTPUT_SCHEMA = {
    "symptom_id": "症状编码（可留空）",
    "name": "症状名称",
    "aliases": ["别名"],
    "body_part": "部位编码",
    "category": "类别编码",
    "definition": "症状定义",
    "description": {
        "onset": "起病特点",
        "duration": "持续时间",
        "severity_scale": "严重程度分级",
        "characteristics": ["症状特征描述"]
    },
    "common_syndromes": [
        {"syndrome_name": "证型名称", "frequency": "常见/偶见/罕见"}
    ],
    "differentiation": {
        "similar_symptoms": ["相似症状"],
        "key_points": ["鉴别要点"],
        "accompanying_clues": ["伴随线索"]
    },
    "modern_equivalent": {
        "western_terms": ["现代医学术语"],
        "possible_diseases": ["可能疾病"],
        "diagnostic_tests": ["建议检查"]
    },
    "measurement": {
        "has_scale": False,
        "scale_name": "",
        "scale_range": ""
    },
    "source_classics": ["经典来源"],
    "relations": {
        "cooccurrence_symptoms": ["常共现症状"],
        "related_drugs": ["相关药物"],
        "related_formulas": ["相关方剂"]
    }
}


def _symptom_user_prompt(symptom_name: str, body_part: str = "QT",
                         category: str = "Z", **kwargs) -> str:
    return (
        f"请为症状【{symptom_name}】生成结构化症状节点。\n"
        f"部位编码：{body_part}，类别编码：{category}。\n"
        f"请给出症状定义、常见证型、鉴别要点、现代对应病名、相关药物与方剂。"
    )


# ---------- 3. 方剂技能 ----------
_FORMULA_SYSTEM_PROMPT = """你是一名中医方剂学专家，熟悉《伤寒论》《金匮要略》《医方集解》等经典。
你的任务是根据给定方剂名称，生成结构完整的方剂档案，包括来源、组成、功效、主治、方解、加减、禁忌与临床应用。

请严格遵守：
1. 只输出合法 JSON，禁止 Markdown 代码块、禁止解释性文字；
2. 组成药物需注明剂量，君臣佐使分析需符合方义；
3. 功效、主治需与经典原文一致；
4. 加减变化应列举常见证候加减；
5. 对不确定的内容使用空字符串或空数组，禁止编造。"""

_FORMULA_OUTPUT_SCHEMA = {
    "formula_id": "方剂编码（可留空）",
    "name": "方剂名称",
    "aliases": ["别名"],
    "classification": {
        "category": "分类，如解表剂、泻下剂",
        "source": "来源典籍",
        "era": "年代",
        "author": "作者",
        "book": "书名"
    },
    "composition": [
        {"drug_id": "药物编码（可留空）", "name": "药物名", "dose": "剂量"}
    ],
    "effects": ["功效"],
    "indications": {
        "symptoms": ["主治症状"],
        "syndromes": ["主治证型"],
        "diseases": ["主治疾病"]
    },
    "explanation": {
        "monarch": ["君药"],
        "minister": ["臣药"],
        "assistant": ["佐药"],
        "guide": ["使药"],
        "mechanism": "方义总述"
    },
    "modifications": [
        {"scenario": "适用场景", "add": ["加药"], "remove": ["减药"]}
    ],
    "usage": {
        "preparation": "煎服法",
        "dosage_form": "剂型",
        "administration": "服法",
        "course": "疗程"
    },
    "contraindications": ["禁忌"],
    "clinical_application": {
        "modern_diseases": ["现代疾病应用"],
        "case_studies": ["典型医案要点"],
        "efficacy_stats": {}
    },
    "source_classics": ["经典来源"]
}


def _formula_user_prompt(formula_name: str, composition: Optional[list] = None,
                         **kwargs) -> str:
    comp_text = ""
    if composition:
        comp_text = "已知组成如下（可作为参考）：\n" + json.dumps(
            composition, ensure_ascii=False, indent=2
        )
    return (
        f"请为方剂【{formula_name}】生成完整档案。{comp_text}\n"
        f"请覆盖来源、组成（含剂量）、功效、主治、方解、加减变化、禁忌及临床应用。"
    )


# ---------- 4. 副作用技能 ----------
_ADVERSE_SYSTEM_PROMPT = """你是一名临床中药学与安全用药专家，熟悉中药不良反应、毒性成分、配伍禁忌及特殊人群用药。
你的任务是根据给定的药物/方剂及已观察症状，分析可能的副作用、毒性机制、风险因素与处置方案。

请严格遵守：
1. 只输出合法 JSON，禁止 Markdown 代码块、禁止解释性文字；
2. 不良反应按系统分类，标注严重程度和发生频率；
3. 毒性分级仅允许：无毒、小毒、有毒、大毒、剧毒；
4. 特殊人群（孕妇、哺乳期、儿童、老年人、肝肾功能不全）需分别说明；
5. 对不确定的内容使用空字符串或空数组，禁止编造。"""

_ADVERSE_OUTPUT_SCHEMA = {
    "adverse_id": "副作用编码（可留空）",
    "drug_id": "药物编码（可留空）",
    "drug_name": "药物/方剂名称",
    "toxicity_profile": {
        "toxicity_level": "无毒/小毒/有毒/大毒/剧毒",
        "toxic_components": ["毒性成分"],
        "toxic_mechanism": "毒性机制",
        "lethal_dose": "致死量（如有）"
    },
    "adverse_reactions": [
        {
            "type": "系统分类",
            "symptom": "症状",
            "severity": "轻度/中度/重度",
            "incidence": "常见/偶见/罕见",
            "onset_time": "出现时间",
            "reversible": True,
            "management": "处理方法"
        }
    ],
    "contraindications": {
        "absolute": ["绝对禁忌"],
        "relative": ["相对禁忌"],
        "special_populations": {
            "pregnant": "孕妇",
            "lactating": "哺乳期",
            "children": "儿童",
            "elderly": "老年人",
            "hepatic_impairment": "肝功能不全",
            "renal_impairment": "肾功能不全"
        }
    },
    "drug_interactions": [
        {
            "drug_id": "",
            "drug_name": "",
            "interaction_type": "协同/拮抗/毒性增强",
            "mechanism": "",
            "severity": ""
        }
    ],
    "overdose": {
        "symptoms": ["过量症状"],
        "treatment": "急救处理",
        "antidote": "解毒剂"
    },
    "monitoring": {
        "required_tests": ["需监测指标"],
        "monitoring_frequency": "监测频率"
    },
    "reported_cases": ["典型案例简述"]
}


def _adverse_user_prompt(drug_id: str = "", drug_name: str = "",
                         symptoms: Optional[list] = None, **kwargs) -> str:
    symptom_text = ""
    if symptoms:
        symptom_text = f"已观察症状：{', '.join(symptoms)}。"
    return (
        f"请分析药物/方剂【{drug_name}】（drug_id={drug_id}）的潜在不良反应与安全信息。"
        f"{symptom_text}\n"
        f"请给出毒性档案、不良反应、禁忌人群、药物相互作用、过量处置及用药监测建议。"
    )


# ---------- 5. 患者技能 ----------
_PATIENT_SYSTEM_PROMPT = """你是一名中医临床医师，擅长四诊合参、辨证论治与医案书写。
你的任务是根据患者基础画像与就诊时间线，生成一份结构化的中医医案式患者档案。

请严格遵守：
1. 只输出合法 JSON，禁止 Markdown 代码块、禁止解释性文字；
2. 时间线需按就诊顺序列出症状、诊断、处方、疗效与医嘱；
3. 辨证结论需符合中医术语规范；
4. 病历应体现真实临床逻辑，避免前后矛盾；
5. 对不确定的内容使用空字符串或空数组，禁止编造。"""

_PATIENT_OUTPUT_SCHEMA = {
    "patient_id": "患者编码（可留空）",
    "profile": {
        "age": 35,
        "gender": "male/female",
        "constitution": "体质类型",
        "bmi": 22.0,
        "occupation": "职业",
        "lifestyle": {
            "sleep_quality": "睡眠质量",
            "diet_habits": "饮食习惯",
            "exercise_frequency": "运动频率",
            "stress_level": "压力水平"
        },
        "medical_history": ["既往病史"],
        "allergies": ["过敏史"],
        "family_history": ["家族史"]
    },
    "timeline": [
        {
            "date": "日期",
            "event_type": "初诊/复诊",
            "symptoms": ["症状"],
            "diagnosis": "中医诊断/证型",
            "prescription": "处方",
            "dosage": "剂量",
            "efficacy": "疗效",
            "doctor_notes": "医嘱"
        }
    ],
    "symptom_history": [
        {"date": "", "symptoms": [], "severity": "未知"}
    ],
    "treatment_history": [
        {"date": "", "prescription": "", "dosage": "", "efficacy": "未知"}
    ],
    "outcome_summary": {
        "overall": "总体疗效",
        "details": ["随访要点"]
    },
    "notes": "备注"
}


def _patient_user_prompt(profile: Optional[dict] = None,
                         timeline: Optional[list] = None, **kwargs) -> str:
    profile_text = json.dumps(profile, ensure_ascii=False, indent=2) if profile else "未提供，请合理虚构。"
    timeline_text = json.dumps(timeline, ensure_ascii=False, indent=2) if timeline else "未提供，请根据画像合理生成就诊时间线。"
    return (
        f"请根据以下患者信息生成结构化中医医案。\n\n"
        f"【患者画像】\n{profile_text}\n\n"
        f"【就诊时间线】\n{timeline_text}\n\n"
        f"请输出完整的患者档案，包含画像、时间线、症状史、治疗史、疗效总结与备注。"
    )


# ---------- 6. 共现技能 ----------
_COOC_SYSTEM_PROMPT = """你是一名中医数据挖掘与证候学专家，擅长从症状集合中发现共现规律并给出中医证候解释。
你的任务是根据给定的症状列表及统计结果，分析症状共现模式、潜在证型与经典来源。

请严格遵守：
1. 只输出合法 JSON，禁止 Markdown 代码块、禁止解释性文字；
2. 结合中医理论解释高频共现症状的证候意义；
3. classic_sources 请标注相关经典条文；
4. 对不确定的内容使用空字符串或空数组，禁止编造。"""

_COOC_OUTPUT_SCHEMA = {
    "pairs": [
        {
            "symptom_a": "症状A",
            "symptom_b": "症状B",
            "support": 0.0,
            "confidence_ab": 0.0,
            "confidence_ba": 0.0,
            "lift": 0.0,
            "strength": "强/中/弱",
            "possible_syndromes": ["可能证型"],
            "classic_sources": ["经典来源"]
        }
    ],
    "possible_syndromes": ["总体可能证型"],
    "classic_sources": ["总体经典来源"]
}


def _cooccurrence_user_prompt(symptoms: list, top_pairs: Optional[list] = None,
                              **kwargs) -> str:
    pairs_text = ""
    if top_pairs:
        pairs_text = "\n已知高频共现对（按 lift 排序）：\n" + json.dumps(
            top_pairs, ensure_ascii=False, indent=2
        )
    return (
        f"请分析以下症状集合的共现模式与证候意义。\n\n"
        f"症状列表：{', '.join(symptoms)}"
        f"{pairs_text}\n\n"
        f"请返回共现对、支持度、置信度、可能证型及经典来源。"
    )


# ---------- 7. 聚类技能 ----------
_CLUSTER_SYSTEM_PROMPT = """你是一名中医临床流行病学与证候分类专家，擅长根据患者症状特征进行证候聚类与命名。
你的任务是根据给定的患者病例集合及聚类结果，为每个聚类群提炼证型、典型症状与代表病例。

请严格遵守：
1. 只输出合法 JSON，禁止 Markdown 代码块、禁止解释性文字；
2. 每个聚类群应给出中医证型名称、典型症状、性别/年龄分布特征；
3. representative_cases 列出具有代表性的病例 patient_id；
4. 对不确定的内容使用空字符串或空数组，禁止编造。"""

_CLUSTER_OUTPUT_SCHEMA = {
    "clusters": [
        {
            "cluster_index": 0,
            "cluster_name": "聚类名称",
            "patient_count": 0,
            "patients": [{"patient_id": "", "profile": {}}],
            "features": ["特征症状"],
            "characteristics": {
                "typical_symptoms": ["典型症状"],
                "typical_syndrome": "典型证型",
                "age_distribution": {},
                "gender_distribution": {}
            },
            "representative_prescriptions": ["代表方剂"]
        }
    ],
    "features": ["整体特征"],
    "representative_cases": ["代表病例 patient_id"],
    "syndromes": {"0": "证型名称"}
}


def _cluster_user_prompt(cases: list, n_clusters: int = 5, **kwargs) -> str:
    # 避免提示过长，仅向 LLM 提供病例摘要
    summaries = []
    for idx, c in enumerate(cases[:30]):
        pid = c.get("patient_id", f"case-{idx}")
        profile = c.get("profile", {})
        timeline = c.get("timeline", [])
        all_symptoms = []
        for ev in timeline:
            all_symptoms.extend(ev.get("symptoms", []))
        summaries.append({
            "patient_id": pid,
            "age": profile.get("age"),
            "gender": profile.get("gender"),
            "symptoms": list(set(all_symptoms))[:10]
        })
    summary_text = json.dumps(summaries, ensure_ascii=False, indent=2)
    return (
        f"请对以下 {len(cases)} 例患者进行证候聚类分析，目标聚类数 {n_clusters}。\n\n"
        f"病例摘要（前 30 例）：\n{summary_text}\n\n"
        f"请为每个聚类群给出证型名称、典型症状、代表病例与代表方剂。"
    )


# ---------- 可选后处理 ----------
def _identity(result: dict, **kwargs) -> dict:
    return result


def _cooccurrence_parse(result: dict, **kwargs) -> dict:
    """确保共现返回包含必要字段。"""
    return {
        "pairs": result.get("pairs", []),
        "possible_syndromes": result.get("possible_syndromes", []),
        "classic_sources": result.get("classic_sources", []),
    }


def _cluster_parse(result: dict, **kwargs) -> dict:
    """确保聚类返回包含必要字段。"""
    return {
        "clusters": result.get("clusters", []),
        "features": result.get("features", []),
        "representative_cases": result.get("representative_cases", []),
        "syndromes": result.get("syndromes", {}),
    }


# ---------- 技能注册表 ----------
SKILL_REGISTRY: Dict[str, dict] = {
    "drug": {
        "system_prompt": _DRUG_SYSTEM_PROMPT,
        "user_prompt_template": _drug_user_prompt,
        "output_schema": _DRUG_OUTPUT_SCHEMA,
        "parse_response": _identity,
    },
    "symptom": {
        "system_prompt": _SYMPTOM_SYSTEM_PROMPT,
        "user_prompt_template": _symptom_user_prompt,
        "output_schema": _SYMPTOM_OUTPUT_SCHEMA,
        "parse_response": _identity,
    },
    "formula": {
        "system_prompt": _FORMULA_SYSTEM_PROMPT,
        "user_prompt_template": _formula_user_prompt,
        "output_schema": _FORMULA_OUTPUT_SCHEMA,
        "parse_response": _identity,
    },
    "adverse": {
        "system_prompt": _ADVERSE_SYSTEM_PROMPT,
        "user_prompt_template": _adverse_user_prompt,
        "output_schema": _ADVERSE_OUTPUT_SCHEMA,
        "parse_response": _identity,
    },
    "patient": {
        "system_prompt": _PATIENT_SYSTEM_PROMPT,
        "user_prompt_template": _patient_user_prompt,
        "output_schema": _PATIENT_OUTPUT_SCHEMA,
        "parse_response": _identity,
    },
    "cooccurrence": {
        "system_prompt": _COOC_SYSTEM_PROMPT,
        "user_prompt_template": _cooccurrence_user_prompt,
        "output_schema": _COOC_OUTPUT_SCHEMA,
        "parse_response": _cooccurrence_parse,
    },
    "cluster": {
        "system_prompt": _CLUSTER_SYSTEM_PROMPT,
        "user_prompt_template": _cluster_user_prompt,
        "output_schema": _CLUSTER_OUTPUT_SCHEMA,
        "parse_response": _cluster_parse,
    },
}


if __name__ == "__main__":
    print("=== 测试 AgentLLM + drug 技能 ===\n")
    try:
        # 优先从项目根目录 .env 加载环境变量（仅测试用，不泄露密钥）
        try:
            from dotenv import load_dotenv
            _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            _env = os.path.join(_root, ".env")
            if os.path.exists(_env):
                load_dotenv(_env, override=False)
                print(f"已加载环境变量: {_env}")
        except Exception as _e:
            print(f"加载 .env 失败（可忽略）: {_e}")

        llm = AgentLLM()
        skill = SKILL_REGISTRY["drug"]
        user_prompt = skill["user_prompt_template"]("麻黄")
        result = llm.generate_json(
            skill["system_prompt"],
            user_prompt,
            skill["output_schema"],
        )
        if skill.get("parse_response"):
            result = skill["parse_response"](result)

        print("\n=== 生成的药物档案摘要 ===")
        print(json.dumps({
            "name": result.get("name"),
            "category": result.get("category"),
            "properties": result.get("properties"),
            "effects": result.get("effects")[:5] if result.get("effects") else [],
        }, ensure_ascii=False, indent=2))
        print("\n完整结果前 2000 字符：")
        print(json.dumps(result, ensure_ascii=False, indent=2)[:2000])
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
