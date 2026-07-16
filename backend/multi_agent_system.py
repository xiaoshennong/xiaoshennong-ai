#!/usr/bin/env python3
"""
小神农中医AI - 多Agent知识库扩展系统 v2.0
7个独立Agent：药物/症状/方剂/副作用/患者/共现/聚类
每个Agent可独立运行，联网搜索，生成结构化数据

v2.0更新：集成真实网络爬虫（Wikipedia + Baidu Baike）
"""

import os
import json
import time
import hashlib
import random
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field, asdict
from abc import ABC, abstractmethod
from enum import Enum

# 导入基于 Yunwu API 的 Agent 技能
from agent_skills import AgentLLM, SKILL_REGISTRY

# 导入网络爬虫
try:
    from web_crawler_v2 import UnifiedCrawler, CrawlResult, get_unified_crawler
    HAS_CRAWLER = True
except ImportError:
    HAS_CRAWLER = False
    print("[MultiAgent] 网络爬虫模块未加载，Agent将使用模拟数据")


# ========== 数据目录配置 ==========
DATA_DIRS = {
    "drugs": "drugs",           # 药物档案 DR-*.json
    "symptoms": "symptoms",     # 症状节点 SN-*.json
    "formulas": "formulas",     # 方剂 FP-*.json
    "adverse": "adverse",       # 副作用 AD-*.json
    "patients": "patients",     # 患者 PT-*.json
    "cooccur": "cooccur",       # 共现 cooccur.json
    "clusters": "clusters",     # 聚类 CL-*.json
}


def ensure_dirs(base_path: str = "./agent_data"):
    """确保所有数据目录存在"""
    for name, dirname in DATA_DIRS.items():
        path = os.path.join(base_path, dirname)
        os.makedirs(path, exist_ok=True)
    return base_path


# ========== 编码生成器 ==========
class IDGenerator:
    """统一编码生成器"""
    
    @staticmethod
    def drug_id(index: int) -> str:
        return f"DR-{index:04d}"
    
    @staticmethod
    def symptom_id(body_part: str, category: str, index: int) -> str:
        return f"SN-{body_part}-{category}-{index:03d}"
    
    @staticmethod
    def formula_id(index: int) -> str:
        return f"FP-{index:04d}"
    
    @staticmethod
    def adverse_id(drug_id: str, index: int) -> str:
        return f"AD-{drug_id.replace('DR-', '')}-{index:03d}"
    
    @staticmethod
    def patient_id(timestamp: float, index: int) -> str:
        return f"PT-{time.strftime('%Y%m%d', time.localtime(timestamp))}-{index:03d}"
    
    @staticmethod
    def cluster_id(index: int) -> str:
        return f"CL-{index:04d}"


# ========== 基础Agent类 ==========
class BaseAgent(ABC):
    """所有Agent的基类"""
    
    def __init__(self, name: str, data_dir: str, base_path: str = "./agent_data",
                 llm: Optional[AgentLLM] = None):
        self.name = name
        self.data_dir = os.path.join(base_path, data_dir)
        os.makedirs(self.data_dir, exist_ok=True)
        self.generated_count = 0
        self.thinking_log: List[Dict] = []
        self.llm = llm
        print(f"[{self.name}] Agent初始化完成，数据目录: {self.data_dir}")
        if self.llm:
            print(f"[{self.name}] 已接入 Yunwu API 结构化生成能力")
    
    def log_thinking(self, step: str, description: str, details: Dict = None):
        """记录思考过程"""
        self.thinking_log.append({
            "timestamp": time.time(),
            "step": step,
            "description": description,
            "details": details or {}
        })
    
    def _enrich_with_llm(self, skill_name: str, **kwargs) -> Optional[Dict]:
        """
        使用 Yunwu API 的结构化生成能力对 Agent 输出进行增强。
        如果 LLM 不可用或返回无效 JSON，则返回 None，由调用方回退到原有逻辑。
        """
        if not self.llm:
            return None
        
        skill = SKILL_REGISTRY.get(skill_name)
        if not skill:
            self.log_thinking("LLM警告", f"未找到技能配置: {skill_name}")
            return None
        
        user_prompt = skill["user_prompt_template"](**kwargs)
        try:
            llm_result = self.llm.generate_json(
                skill["system_prompt"],
                user_prompt,
                skill["output_schema"]
            )
            if skill.get("parse_response"):
                llm_result = skill["parse_response"](llm_result)
            self.log_thinking(
                "LLM结构化生成",
                f"使用 {skill_name} 技能成功生成结构化数据",
                {"fields": list(llm_result.keys())}
            )
            return llm_result
        except Exception as e:
            self.log_thinking(
                "LLM警告",
                f"Yunwu API 结构化生成失败: {e}，将使用本地规则与网络爬虫回退",
                {"skill": skill_name}
            )
            return None
    
    @abstractmethod
    def generate(self, **kwargs) -> Dict:
        """生成数据，子类必须实现"""
        pass
    
    def save(self, data: Dict, filename: str) -> str:
        """保存数据到文件"""
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.generated_count += 1
        return filepath
    
    def load(self, filename: str) -> Optional[Dict]:
        """加载数据"""
        filepath = os.path.join(self.data_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def list_files(self) -> List[str]:
        """列出所有数据文件"""
        return sorted([f for f in os.listdir(self.data_dir) if f.endswith('.json')])
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "agent_name": self.name,
            "data_dir": self.data_dir,
            "generated_count": self.generated_count,
            "total_files": len(self.list_files()),
            "thinking_steps": len(self.thinking_log),
        }


# ========== 1. 药物Agent ==========
class DrugAgent(BaseAgent):
    """
    药物Agent
    按DR编码生成药物完整档案
    联网搜索：性味归经、功效主治、用法用量、现代研究
    """
    
    def __init__(self, base_path: str = "./agent_data", llm: Optional[AgentLLM] = None):
        super().__init__("DrugAgent", "drugs", base_path, llm=llm)
        self.drug_counter = 0
    
    def generate(self, drug_name: str, search_results: List[str] = None, 
                 use_web_search: bool = True) -> Dict:
        """
        生成药物档案（支持联网搜索）
        
        Args:
            drug_name: 药物名称
            search_results: 联网搜索结果（文本列表）
            use_web_search: 是否使用网络搜索（默认True）
        """
        self.thinking_log = []
        self.log_thinking("开始", f"开始生成药物档案: {drug_name}")
        
        # Step 1: 分配编码
        self.drug_counter += 1
        drug_id = IDGenerator.drug_id(self.drug_counter)
        self.log_thinking("编码分配", f"分配药物编码: {drug_id}")
        
        # Step 2: 网络搜索（如果启用）
        crawled_data = []
        if use_web_search and HAS_CRAWLER:
            self.log_thinking("网络搜索", f"正在联网搜索 {drug_name} 的信息...")
            try:
                crawler = get_unified_crawler()
                crawled_results = crawler.crawl(drug_name, data_type="herb", sources=["wikipedia"])
                
                for result in crawled_results:
                    crawled_data.append(result.content)
                    self.log_thinking("数据获取", f"从 {result.source} 获取到 {len(result.content)} 字符")
                
                if crawled_data:
                    self.log_thinking("搜索完成", f"成功获取 {len(crawled_data)} 条网络数据")
                else:
                    self.log_thinking("搜索警告", "未获取到网络数据，将使用本地知识")
            except Exception as e:
                self.log_thinking("搜索错误", f"网络搜索失败: {e}")
        
        # Step 3: 解析搜索数据
        self.log_thinking("数据解析", "解析药物基本信息...")
        
        # 合并搜索结果
        all_search_results = []
        if search_results:
            all_search_results.extend(search_results)
        if crawled_data:
            all_search_results.extend(crawled_data)
        
        # 构建药物档案
        drug_data = {
            "agent": "DrugAgent",
            "version": "2.0",
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "drug_id": drug_id,
            "name": drug_name,
            "aliases": [],
            "category": "",
            "properties": {
                "nature": "",
                "taste": "",
                "meridian": [],
                "toxicity": "无毒",
            },
            "effects": [],
            "indications": [],
            "usage": {
                "dosage": "",
                "preparation": "",
                "administration": "",
                "contraindications": [],
                "precautions": [],
            },
            "modern_research": {
                "active_compounds": [],
                "pharmacology": [],
                "clinical_studies": [],
                "references": [],
            },
            "source_classics": [],
            "quality_standards": {
                "origin": [],
                "harvest_season": "",
                "processing": "",
                "storage": "",
            },
            "data_sources": {
                "search_results_count": len(all_search_results),
                "search_queries": [drug_name],
                "verified": False,
                "confidence": 0.5,
                "web_search_used": use_web_search and HAS_CRAWLER,
                "crawled_sources": [r.source for r in crawled_results] if 'crawled_results' in dir() else [],
            },
            "relations": {
                "related_formulas": [],
                "synergistic_drugs": [],
                "antagonistic_drugs": [],
                "contraindicated_drugs": [],
            }
        }
        
        # 解析爬取的数据
        if all_search_results:
            self._parse_search_results(drug_data, all_search_results)
        
        # 使用 Yunwu API 结构化生成进行增强
        llm_result = self._enrich_with_llm("drug", drug_name=drug_name)
        if llm_result:
            for key, value in llm_result.items():
                if key in ("agent", "version", "generated_at", "drug_id"):
                    continue
                drug_data[key] = value
            # 保持本地生成的编码一致
            drug_data["drug_id"] = drug_id
            drug_data["data_sources"]["llm_enriched"] = True
        
        self.log_thinking("档案生成", f"药物档案生成完成: {drug_name}")
        
        # 保存
        filename = f"{drug_id}.json"
        filepath = self.save(drug_data, filename)
        
        return {
            "drug_id": drug_id,
            "name": drug_name,
            "filepath": filepath,
            "data": drug_data,
            "thinking_log": self.thinking_log,
            "web_search_used": use_web_search and HAS_CRAWLER,
            "sources_count": len(all_search_results),
        }
    
    def _parse_search_results(self, drug_data: Dict, search_results: List[str]):
        """从搜索结果中解析结构化数据"""
        # 这里可以接入LLM来解析非结构化文本
        # 简化版：提取关键词匹配
        combined_text = " ".join(search_results)
        
        # 提取性味
        nature_keywords = {"寒": "寒", "热": "热", "温": "温", "凉": "凉", "平": "平"}
        for kw, val in nature_keywords.items():
            if kw in combined_text:
                drug_data["properties"]["nature"] = val
                break
        
        # 提取功效关键词
        effect_keywords = ["解表", "清热", "祛湿", "化痰", "止咳", "平喘", "活血", "化瘀",
                          "补气", "养血", "滋阴", "壮阳", "安神", "明目", "解毒", "消肿"]
        for kw in effect_keywords:
            if kw in combined_text:
                drug_data["effects"].append(kw)
        
        drug_data["data_sources"]["confidence"] = min(0.9, 0.5 + len(search_results) * 0.1)
    
    def batch_generate(self, drug_names: List[str]) -> List[Dict]:
        """批量生成药物档案"""
        results = []
        for name in drug_names:
            result = self.generate(name)
            results.append(result)
            time.sleep(0.1)  # 模拟处理时间
        return results


# ========== 2. 症状Agent ==========
class SymptomAgent(BaseAgent):
    """
    症状Agent
    按SN编码生成症状节点
    联网搜索：症状定义、常见证型、鉴别要点、现代对应
    """
    
    def __init__(self, base_path: str = "./agent_data", llm: Optional[AgentLLM] = None):
        super().__init__("SymptomAgent", "symptoms", base_path, llm=llm)
        self.symptom_counter = {}
    
    def generate(self, symptom_name: str, body_part: str = "QT", category: str = "Z",
                 search_results: List[str] = None, use_web_search: bool = True) -> Dict:
        """
        生成症状节点（支持联网搜索）
        
        Args:
            symptom_name: 症状名称
            body_part: 部位编码（QT全身/TB头部/XB胸部/FB腹部等）
            category: 类别编码（Z自觉/T体征/S睡眠等）
            search_results: 联网搜索结果
            use_web_search: 是否使用网络搜索
        """
        self.thinking_log = []
        self.log_thinking("开始", f"开始生成症状节点: {symptom_name}")
        
        # Step 1: 分配编码
        key = f"{body_part}-{category}"
        if key not in self.symptom_counter:
            self.symptom_counter[key] = 0
        self.symptom_counter[key] += 1
        symptom_id = IDGenerator.symptom_id(body_part, category, self.symptom_counter[key])
        self.log_thinking("编码分配", f"分配症状编码: {symptom_id}")
        
        # Step 2: 网络搜索
        crawled_data = []
        if use_web_search and HAS_CRAWLER:
            self.log_thinking("网络搜索", f"正在联网搜索 {symptom_name} 的症状信息...")
            try:
                crawler = get_unified_crawler()
                crawled_results = crawler.crawl(symptom_name, data_type="symptom", sources=["wikipedia"])
                for result in crawled_results:
                    crawled_data.append(result.content)
                    self.log_thinking("数据获取", f"从 {result.source} 获取到 {len(result.content)} 字符")
                if crawled_data:
                    self.log_thinking("搜索完成", f"成功获取 {len(crawled_data)} 条网络数据")
            except Exception as e:
                self.log_thinking("搜索错误", f"网络搜索失败: {e}")
        
        # Step 3: 构建症状节点
        all_search_results = []
        if search_results:
            all_search_results.extend(search_results)
        if crawled_data:
            all_search_results.extend(crawled_data)
        
        symptom_data = {
            "agent": "SymptomAgent",
            "version": "2.0",
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "symptom_id": symptom_id,
            "name": symptom_name,
            "aliases": [],
            "body_part": body_part,
            "category": category,
            "definition": "",
            "description": {
                "onset": "",
                "duration": "",
                "severity_scale": "",
                "characteristics": [],
            },
            "common_syndromes": [],
            "differentiation": {
                "similar_symptoms": [],
                "key_points": [],
                "accompanying_clues": [],
            },
            "modern_equivalent": {
                "western_terms": [],
                "possible_diseases": [],
                "diagnostic_tests": [],
            },
            "measurement": {
                "has_scale": False,
                "scale_name": "",
                "scale_range": "",
            },
            "source_classics": [],
            "data_sources": {
                "search_results_count": len(all_search_results),
                "verified": False,
                "confidence": 0.5,
                "web_search_used": use_web_search and HAS_CRAWLER,
                "crawled_sources": [r.source for r in crawled_results] if 'crawled_results' in dir() else [],
            },
            "relations": {
                "cooccurrence_symptoms": [],
                "related_drugs": [],
                "related_formulas": [],
            }
        }
        
        if all_search_results:
            self._parse_search_results(symptom_data, all_search_results)
        
        # 使用 Yunwu API 结构化生成进行增强
        llm_result = self._enrich_with_llm(
            "symptom", symptom_name=symptom_name, body_part=body_part, category=category
        )
        if llm_result:
            for key, value in llm_result.items():
                if key in ("agent", "version", "generated_at", "symptom_id"):
                    continue
                symptom_data[key] = value
            symptom_data["symptom_id"] = symptom_id
            symptom_data["data_sources"]["llm_enriched"] = True
        
        self.log_thinking("节点生成", f"症状节点生成完成: {symptom_name}")
        
        filename = f"{symptom_id}.json"
        filepath = self.save(symptom_data, filename)
        
        return {
            "symptom_id": symptom_id,
            "name": symptom_name,
            "filepath": filepath,
            "data": symptom_data,
            "thinking_log": self.thinking_log,
            "web_search_used": use_web_search and HAS_CRAWLER,
            "sources_count": len(all_search_results),
        }
    
    def _parse_search_results(self, symptom_data: Dict, search_results: List[str]):
        """解析搜索结果"""
        combined_text = " ".join(search_results)
        
        # 提取常见证型
        syndrome_keywords = ["风寒", "风热", "湿热", "痰湿", "气虚", "血虚", "阴虚", "阳虚",
                            "血瘀", "气郁", "食积", "肝火", "肾虚", "脾虚"]
        for kw in syndrome_keywords:
            if kw in combined_text:
                symptom_data["common_syndromes"].append({
                    "syndrome_name": kw,
                    "frequency": "常见"
                })
        
        symptom_data["data_sources"]["confidence"] = min(0.9, 0.5 + len(search_results) * 0.1)


# ========== 3. 方剂Agent ==========
class FormulaAgent(BaseAgent):
    """
    方剂Agent
    按FP编码生成方剂（引用药物ID）
    联网搜索：组成、功效、主治、方解、临床应用
    """
    
    def __init__(self, base_path: str = "./agent_data", llm: Optional[AgentLLM] = None):
        super().__init__("FormulaAgent", "formulas", base_path, llm=llm)
        self.formula_counter = 0
    
    def generate(self, formula_name: str, composition: List[Dict] = None,
                 search_results: List[str] = None, use_web_search: bool = True) -> Dict:
        """
        生成方剂档案（支持联网搜索）
        
        Args:
            formula_name: 方剂名称
            composition: 组成 [{"drug_id": "DR-0001", "name": "麻黄", "dose": "9g"}]
            search_results: 联网搜索结果
            use_web_search: 是否使用网络搜索
        """
        self.thinking_log = []
        self.log_thinking("开始", f"开始生成方剂档案: {formula_name}")
        
        # Step 1: 分配编码
        self.formula_counter += 1
        formula_id = IDGenerator.formula_id(self.formula_counter)
        self.log_thinking("编码分配", f"分配方剂编码: {formula_id}")
        
        # Step 2: 网络搜索
        crawled_data = []
        if use_web_search and HAS_CRAWLER:
            self.log_thinking("网络搜索", f"正在联网搜索 {formula_name} 的方剂信息...")
            try:
                crawler = get_unified_crawler()
                crawled_results = crawler.crawl(formula_name, data_type="formula", sources=["wikipedia"])
                for result in crawled_results:
                    crawled_data.append(result.content)
                    self.log_thinking("数据获取", f"从 {result.source} 获取到 {len(result.content)} 字符")
                if crawled_data:
                    self.log_thinking("搜索完成", f"成功获取 {len(crawled_data)} 条网络数据")
            except Exception as e:
                self.log_thinking("搜索错误", f"网络搜索失败: {e}")
        
        # Step 3: 验证组成药物
        if composition:
            self.log_thinking("药物验证", f"验证{len(composition)}味组成药物...")
            for drug in composition:
                if not drug.get("drug_id"):
                    self.log_thinking("警告", f"药物 {drug.get('name', '未知')} 缺少DR编码")
        
        # 合并搜索结果
        all_search_results = []
        if search_results:
            all_search_results.extend(search_results)
        if crawled_data:
            all_search_results.extend(crawled_data)
        
        formula_data = {
            "agent": "FormulaAgent",
            "version": "2.0",
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "formula_id": formula_id,
            "name": formula_name,
            "aliases": [],
            "classification": {
                "category": "",
                "source": "",
                "era": "",
                "author": "",
                "book": "",
            },
            "composition": composition or [],
            "effects": [],
            "indications": {
                "symptoms": [],
                "syndromes": [],
                "diseases": [],
            },
            "explanation": {
                "monarch": [],
                "minister": [],
                "assistant": [],
                "guide": [],
                "mechanism": "",
            },
            "modifications": [],
            "usage": {
                "preparation": "",
                "dosage_form": "",
                "administration": "",
                "course": "",
            },
            "contraindications": [],
            "clinical_application": {
                "modern_diseases": [],
                "case_studies": [],
                "efficacy_stats": {},
            },
            "source_classics": [],
            "data_sources": {
                "search_results_count": len(all_search_results),
                "verified": False,
                "confidence": 0.5,
                "web_search_used": use_web_search and HAS_CRAWLER,
                "crawled_sources": [r.source for r in crawled_results] if 'crawled_results' in dir() else [],
            },
        }
        
        if all_search_results:
            self._parse_search_results(formula_data, all_search_results)
        
        # 使用 Yunwu API 结构化生成进行增强
        llm_result = self._enrich_with_llm(
            "formula", formula_name=formula_name, composition=composition
        )
        if llm_result:
            for key, value in llm_result.items():
                if key in ("agent", "version", "generated_at", "formula_id"):
                    continue
                formula_data[key] = value
            formula_data["formula_id"] = formula_id
            formula_data["data_sources"]["llm_enriched"] = True
        
        self.log_thinking("档案生成", f"方剂档案生成完成: {formula_name}")
        
        filename = f"{formula_id}.json"
        filepath = self.save(formula_data, filename)
        
        return {
            "formula_id": formula_id,
            "name": formula_name,
            "filepath": filepath,
            "data": formula_data,
            "thinking_log": self.thinking_log,
            "web_search_used": use_web_search and HAS_CRAWLER,
            "sources_count": len(all_search_results),
        }
    
    def _parse_search_results(self, formula_data: Dict, search_results: List[str]):
        """解析搜索结果"""
        combined_text = " ".join(search_results)
        
        # 提取功效
        effect_keywords = ["解表", "清热", "泻下", "和解", "温里", "补益", "理气", "理血",
                          "祛湿", "化痰", "止咳", "平喘", "消食", "驱虫", "安神", "开窍",
                          "固涩", "涌吐"]
        for kw in effect_keywords:
            if kw in combined_text:
                formula_data["effects"].append(kw)
        
        formula_data["data_sources"]["confidence"] = min(0.9, 0.5 + len(search_results) * 0.1)


# ========== 4. 副作用Agent ==========
class AdverseAgent(BaseAgent):
    """
    副作用Agent
    为每味药收集已知副作用
    联网搜索：不良反应、毒性、禁忌人群、药物相互作用
    """
    
    def __init__(self, base_path: str = "./agent_data", llm: Optional[AgentLLM] = None):
        super().__init__("AdverseAgent", "adverse", base_path, llm=llm)
        self.adverse_counter = 0
    
    def generate(self, drug_id: str, drug_name: str,
                 search_results: List[str] = None) -> Dict:
        """
        生成药物副作用档案
        
        Args:
            drug_id: 药物编码（如 DR-0001）
            drug_name: 药物名称
            search_results: 联网搜索结果
        """
        self.thinking_log = []
        self.log_thinking("开始", f"开始收集副作用: {drug_name} ({drug_id})")
        
        # 分配编码
        self.adverse_counter += 1
        adverse_id = IDGenerator.adverse_id(drug_id, self.adverse_counter)
        self.log_thinking("编码分配", f"分配副作用编码: {adverse_id}")
        
        adverse_data = {
            "agent": "AdverseAgent",
            "version": "1.0",
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "adverse_id": adverse_id,
            "drug_id": drug_id,
            "drug_name": drug_name,
            "toxicity_profile": {  # 毒性档案
                "toxicity_level": "未知",  # 无毒/小毒/有毒/大毒/剧毒
                "toxic_components": [],   # 毒性成分
                "toxic_mechanism": "",    # 毒性机制
                "lethal_dose": "",        # 致死量（如有数据）
            },
            "adverse_reactions": [],  # 不良反应列表
            # {
            #     "reaction_id": "ADR-001",
            #     "type": "消化系统",  # 系统分类
            #     "symptom": "恶心",
            #     "severity": "轻度",  # 轻度/中度/重度
            #     "incidence": "常见",  # 常见/偶见/罕见
            #     "onset_time": "",     # 出现时间
            #     "reversible": True,   # 是否可逆
            #     "management": "",     # 处理方法
            # }
            "contraindications": {  # 禁忌
                "absolute": [],      # 绝对禁忌
                "relative": [],      # 相对禁忌
                "special_populations": {  # 特殊人群
                    "pregnant": "",      # 孕妇
                    "lactating": "",     # 哺乳期
                    "children": "",      # 儿童
                    "elderly": "",       # 老年人
                    "hepatic_impairment": "",  # 肝功能不全
                    "renal_impairment": "",    # 肾功能不全
                }
            },
            "drug_interactions": [],  # 药物相互作用
            # {
            #     "drug_id": "DR-0002",
            #     "drug_name": "",
            #     "interaction_type": "协同/拮抗/毒性增强",
            #     "mechanism": "",
            #     "severity": "",
            # }
            "overdose": {  # 过量用药
                "symptoms": [],      # 过量症状
                "treatment": "",     # 急救处理
                "antidote": "",      # 解毒剂
            },
            "monitoring": {  # 用药监测
                "required_tests": [],  # 需监测指标
                "monitoring_frequency": "",  # 监测频率
            },
            "reported_cases": [],  #  reported不良反应案例
            "data_sources": {
                "search_results_count": len(search_results) if search_results else 0,
                "verified": False,
                "confidence": 0.5,
            },
        }
        
        if search_results:
            self._parse_search_results(adverse_data, search_results)
        
        # 使用 Yunwu API 结构化生成进行增强
        llm_result = self._enrich_with_llm(
            "adverse", drug_id=drug_id, drug_name=drug_name
        )
        if llm_result:
            for key, value in llm_result.items():
                if key in ("agent", "version", "generated_at", "adverse_id", "drug_id"):
                    continue
                adverse_data[key] = value
            adverse_data["adverse_id"] = adverse_id
            adverse_data["drug_id"] = drug_id
            adverse_data["data_sources"]["llm_enriched"] = True
        
        self.log_thinking("档案生成", f"副作用档案生成完成: {drug_name}")
        
        filename = f"{adverse_id}.json"
        filepath = self.save(adverse_data, filename)
        
        return {
            "adverse_id": adverse_id,
            "drug_id": drug_id,
            "drug_name": drug_name,
            "filepath": filepath,
            "data": adverse_data,
            "thinking_log": self.thinking_log,
        }
    
    def _parse_search_results(self, adverse_data: Dict, search_results: List[str]):
        """解析搜索结果"""
        combined_text = " ".join(search_results)
        
        # 提取毒性级别
        toxicity_levels = ["剧毒", "大毒", "有毒", "小毒"]
        for level in toxicity_levels:
            if level in combined_text:
                adverse_data["toxicity_profile"]["toxicity_level"] = level
                break
        
        # 提取不良反应症状
        symptom_keywords = ["恶心", "呕吐", "腹泻", "腹痛", "头晕", "头痛", "皮疹", "瘙痒",
                           "心悸", "胸闷", "乏力", "过敏", "出血", "黄疸"]
        for kw in symptom_keywords:
            if kw in combined_text:
                adverse_data["adverse_reactions"].append({
                    "symptom": kw,
                    "severity": "待确认",
                    "incidence": "待统计"
                })
        
        adverse_data["data_sources"]["confidence"] = min(0.9, 0.5 + len(search_results) * 0.1)


# ========== 5. 患者Agent ==========
class PatientAgent(BaseAgent):
    """
    患者Agent
    生成模拟患者档案（时间线）
    用于：测试系统、训练模型、聚类分析、疗效预测
    """
    
    def __init__(self, base_path: str = "./agent_data", llm: Optional[AgentLLM] = None):
        super().__init__("PatientAgent", "patients", base_path, llm=llm)
        self.patient_counter = 0
    
    def generate(self, profile: Dict = None, timeline: List[Dict] = None) -> Dict:
        """
        生成模拟患者档案
        
        Args:
            profile: 患者画像 {
                "age": 35,
                "gender": "male",
                "constitution": "气虚质",
                "medical_history": ["高血压"],
                "allergies": [],
            }
            timeline: 时间线事件 [
                {"date": "2024-01-01", "event": "初诊", "symptoms": ["头痛"], "diagnosis": "风寒", "prescription": "麻黄汤"}
            ]
        """
        self.thinking_log = []
        self.log_thinking("开始", "开始生成模拟患者档案")
        
        # 分配编码
        self.patient_counter += 1
        patient_id = IDGenerator.patient_id(time.time(), self.patient_counter)
        self.log_thinking("编码分配", f"分配患者编码: {patient_id}")
        
        # 生成随机画像（如果没有提供）
        if profile is None:
            profile = self._generate_random_profile()
            self.log_thinking("画像生成", "生成随机患者画像")
        
        # 生成时间线（如果没有提供）
        if timeline is None:
            timeline = self._generate_random_timeline(profile)
            self.log_thinking("时间线生成", "生成随机就诊时间线")
        
        patient_data = {
            "agent": "PatientAgent",
            "version": "1.0",
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "patient_id": patient_id,
            "profile": {
                "age": profile.get("age", 35),
                "gender": profile.get("gender", "male"),
                "constitution": profile.get("constitution", "平和质"),
                "bmi": profile.get("bmi", 22.0),
                "occupation": profile.get("occupation", "办公室工作"),
                "lifestyle": {
                    "sleep_quality": "一般",
                    "diet_habits": "正常",
                    "exercise_frequency": "偶尔",
                    "stress_level": "中等",
                },
                "medical_history": profile.get("medical_history", []),
                "allergies": profile.get("allergies", []),
                "family_history": profile.get("family_history", []),
            },
            "timeline": timeline,  # 时间线
            "symptom_history": self._extract_symptom_history(timeline),
            "treatment_history": self._extract_treatment_history(timeline),
            "outcome_summary": self._calculate_outcome(timeline),
            "privacy": {
                "is_simulated": True,  # 标记为模拟数据
                "anonymized": True,    # 已匿名化
                "data_usage": ["model_training", "clustering_analysis", "efficacy_research"],
            }
        }
        
        # 使用 Yunwu API 结构化生成进行增强
        llm_result = self._enrich_with_llm(
            "patient", profile=profile, timeline=timeline
        )
        if llm_result:
            for key, value in llm_result.items():
                if key in ("agent", "version", "generated_at", "patient_id"):
                    continue
                patient_data[key] = value
            patient_data["patient_id"] = patient_id
            # 保持派生字段与时间线一致
            patient_data["symptom_history"] = self._extract_symptom_history(
                patient_data["timeline"]
            )
            patient_data["treatment_history"] = self._extract_treatment_history(
                patient_data["timeline"]
            )
            patient_data["outcome_summary"] = self._calculate_outcome(
                patient_data["timeline"]
            )
            patient_data["data_sources"] = {"llm_enriched": True}
        
        self.log_thinking("档案生成", f"患者档案生成完成: {patient_id}")
        
        filename = f"{patient_id}.json"
        filepath = self.save(patient_data, filename)
        
        return {
            "patient_id": patient_id,
            "filepath": filepath,
            "data": patient_data,
            "thinking_log": self.thinking_log,
        }
    
    def _generate_random_profile(self) -> Dict:
        """生成随机患者画像"""
        constitutions = ["平和质", "气虚质", "阳虚质", "阴虚质", "痰湿质", 
                        "湿热质", "血瘀质", "气郁质", "特禀质"]
        return {
            "age": random.randint(18, 75),
            "gender": random.choice(["male", "female"]),
            "constitution": random.choice(constitutions),
            "medical_history": random.sample(["高血压", "糖尿病", "胃炎", "失眠", "偏头痛"], 
                                              k=random.randint(0, 2)),
            "allergies": [],
        }
    
    def _generate_random_timeline(self, profile: Dict) -> List[Dict]:
        """生成随机就诊时间线"""
        timeline = []
        base_date = time.time() - random.randint(30, 365) * 86400
        
        # 初诊
        timeline.append({
            "date": time.strftime("%Y-%m-%d", time.localtime(base_date)),
            "event_type": "初诊",
            "symptoms": random.sample(["头痛", "发热", "恶寒", "乏力", "咳嗽", "咽痛"], k=random.randint(2, 4)),
            "diagnosis": "风寒表实证",
            "prescription": "麻黄汤",
            "dosage": "3剂",
            "doctor_notes": ""
        })
        
        # 复诊
        timeline.append({
            "date": time.strftime("%Y-%m-%d", time.localtime(base_date + 7 * 86400)),
            "event_type": "复诊",
            "symptoms": ["头痛减轻", "微恶寒"],
            "diagnosis": "表证未解",
            "prescription": "桂枝汤",
            "dosage": "2剂",
            "efficacy": "有效",
            "doctor_notes": "症状减轻，继续调理"
        })
        
        return timeline
    
    def _extract_symptom_history(self, timeline: List[Dict]) -> List[Dict]:
        """提取症状历史"""
        history = []
        for event in timeline:
            if "symptoms" in event:
                history.append({
                    "date": event["date"],
                    "symptoms": event["symptoms"],
                    "severity": event.get("severity", "未知")
                })
        return history
    
    def _extract_treatment_history(self, timeline: List[Dict]) -> List[Dict]:
        """提取治疗历史"""
        history = []
        for event in timeline:
            if "prescription" in event:
                history.append({
                    "date": event["date"],
                    "prescription": event["prescription"],
                    "dosage": event.get("dosage", ""),
                    "efficacy": event.get("efficacy", "未知")
                })
        return history
    
    def _calculate_outcome(self, timeline: List[Dict]) -> Dict:
        """计算治疗结果"""
        efficacies = [e.get("efficacy", "未知") for e in timeline if "efficacy" in e]
        if not efficacies:
            return {"overall": "未知", "details": []}
        
        # 简单统计
        good = sum(1 for e in efficacies if e in ["痊愈", "显效", "有效"])
        return {
            "overall": "有效" if good > len(efficacies) / 2 else "待观察",
            "total_visits": len(timeline),
            "efficacy_distribution": {
                "good": good,
                "total": len(efficacies)
            }
        }


# ========== 6. 共现Agent ==========
class CooccurrenceAgent(BaseAgent):
    """
    共现Agent
    分析症状共现强度
    输入：患者档案集合 / 医案集合
    输出：症状共现矩阵 + 异常检测
    """
    
    def __init__(self, base_path: str = "./agent_data", llm: Optional[AgentLLM] = None):
        super().__init__("CooccurrenceAgent", "cooccur", base_path, llm=llm)
    
    def generate(self, patient_files: List[str] = None, 
                symptom_database: Dict = None) -> Dict:
        """实现抽象方法，委托给analyze"""
        return self.analyze(patient_files, symptom_database)
    
    def analyze(self, patient_files: List[str] = None, 
                symptom_database: Dict = None) -> Dict:
        """
        分析症状共现
        
        Args:
            patient_files: 患者档案文件路径列表
            symptom_database: 症状数据库 {symptom_id: {name, count}}
        """
        self.thinking_log = []
        self.log_thinking("开始", "开始症状共现分析")
        
        # 加载患者数据
        patients = []
        if patient_files:
            for pf in patient_files:
                data = self.load(os.path.basename(pf))
                if data:
                    patients.append(data)
        
        # 如果没有提供文件，生成模拟数据
        if not patients:
            self.log_thinking("数据准备", "无患者数据，生成模拟数据进行演示")
            patients = self._generate_mock_patients(50)
        
        self.log_thinking("数据加载", f"加载 {len(patients)} 例患者档案")
        
        # 统计症状共现
        cooccurrence_matrix = {}
        symptom_counts = {}
        total_patients = len(patients)
        
        for patient in patients:
            symptoms = self._extract_symptoms(patient)
            
            # 统计单症状频率
            for s in symptoms:
                symptom_counts[s] = symptom_counts.get(s, 0) + 1
            
            # 统计共现
            for i, sa in enumerate(symptoms):
                for sb in symptoms[i+1:]:
                    pair = tuple(sorted([sa, sb]))
                    cooccurrence_matrix[pair] = cooccurrence_matrix.get(pair, 0) + 1
        
        self.log_thinking("共现统计", f"发现 {len(cooccurrence_matrix)} 对症状共现")
        
        # 计算共现强度
        cooccurrence_results = []
        for (sa, sb), count in cooccurrence_matrix.items():
            # 支持度
            support = count / total_patients
            # 置信度（A->B）
            confidence_ab = count / symptom_counts.get(sa, 1)
            confidence_ba = count / symptom_counts.get(sb, 1)
            # 提升度
            lift = (count * total_patients) / (symptom_counts.get(sa, 1) * symptom_counts.get(sb, 1))
            
            cooccurrence_results.append({
                "symptom_a": sa,
                "symptom_b": sb,
                "cooccurrence_count": count,
                "support": round(support, 4),
                "confidence_ab": round(confidence_ab, 4),
                "confidence_ba": round(confidence_ba, 4),
                "lift": round(lift, 4),
                "strength": "强" if lift > 2 else "中" if lift > 1 else "弱",
            })
        
        # 排序
        cooccurrence_results.sort(key=lambda x: x["lift"], reverse=True)
        
        # 异常检测（低共现但同方剂的组合）
        anomalies = self._detect_anomalies(cooccurrence_results, patients)
        
        self.log_thinking("异常检测", f"发现 {len(anomalies)} 个异常共现模式")
        
        result_data = {
            "agent": "CooccurrenceAgent",
            "version": "1.0",
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_patients": total_patients,
            "unique_symptoms": len(symptom_counts),
            "cooccurrence_pairs": len(cooccurrence_results),
            "symptom_counts": symptom_counts,
            "cooccurrence_matrix": cooccurrence_results[:100],  # Top 100
            "anomalies": anomalies,
            "statistics": {
                "strong_cooccurrence": sum(1 for c in cooccurrence_results if c["strength"] == "强"),
                "medium_cooccurrence": sum(1 for c in cooccurrence_results if c["strength"] == "中"),
                "weak_cooccurrence": sum(1 for c in cooccurrence_results if c["strength"] == "弱"),
            }
        }
        
        # 使用 Yunwu API 结构化生成进行证候解释增强
        symptom_list = sorted(symptom_counts.keys())
        llm_result = self._enrich_with_llm(
            "cooccurrence",
            symptoms=symptom_list,
            top_pairs=cooccurrence_results[:10]
        )
        if llm_result:
            result_data["possible_syndromes"] = llm_result.get("possible_syndromes", [])
            result_data["classic_sources"] = llm_result.get("classic_sources", [])
            result_data["llm_enriched"] = True
        
        self.log_thinking("分析完成", "症状共现分析完成")
        
        filename = "cooccur.json"
        filepath = self.save(result_data, filename)
        
        return {
            "filepath": filepath,
            "data": result_data,
            "thinking_log": self.thinking_log,
        }
    
    def _extract_symptoms(self, patient: Dict) -> List[str]:
        """从患者档案提取症状"""
        symptoms = []
        timeline = patient.get("timeline", [])
        for event in timeline:
            event_symptoms = event.get("symptoms", [])
            for s in event_symptoms:
                if s not in symptoms:
                    symptoms.append(s)
        return symptoms
    
    def _generate_mock_patients(self, count: int) -> List[Dict]:
        """生成模拟患者数据"""
        patients = []
        symptom_pool = ["头痛", "发热", "恶寒", "汗出", "咳嗽", "咽痛", "鼻塞", "流涕",
                       "胸闷", "心悸", "失眠", "多梦", "乏力", "食欲不振", "腹胀",
                       "腹泻", "便秘", "口干", "口苦", "恶心", "呕吐", "腰痛", "关节痛"]
        
        for i in range(count):
            # 模拟症状组合（一些常见组合）
            if random.random() < 0.3:
                # 风寒组合
                symptoms = random.sample(["头痛", "发热", "恶寒", "鼻塞", "流涕"], k=random.randint(2, 4))
            elif random.random() < 0.5:
                # 气虚组合
                symptoms = random.sample(["乏力", "食欲不振", "腹胀", "气短", "自汗"], k=random.randint(2, 4))
            else:
                symptoms = random.sample(symptom_pool, k=random.randint(2, 5))
            
            patients.append({
                "patient_id": f"MOCK-{i+1:03d}",
                "timeline": [{"symptoms": symptoms}]
            })
        
        return patients
    
    def _detect_anomalies(self, cooccurrence_results: List[Dict], patients: List[Dict]) -> List[Dict]:
        """检测异常共现"""
        anomalies = []
        
        # 找出低共现但理论上应该共现的组合
        # 例如：发热+恶寒应该是强共现，如果lift很低就是异常
        expected_pairs = [
            ("发热", "恶寒"),
            ("头痛", "发热"),
            ("咳嗽", "咽痛"),
            ("失眠", "多梦"),
        ]
        
        for sa, sb in expected_pairs:
            found = False
            for c in cooccurrence_results:
                if (c["symptom_a"] == sa and c["symptom_b"] == sb) or \
                   (c["symptom_a"] == sb and c["symptom_b"] == sa):
                    found = True
                    if c["lift"] < 1.0:
                        anomalies.append({
                            "type": "低共现异常",
                            "symptom_a": sa,
                            "symptom_b": sb,
                            "lift": c["lift"],
                            "expected": "高共现",
                            "actual": "低共现",
                            "possible_reason": "样本偏差或数据质量问题"
                        })
                    break
            
            if not found:
                anomalies.append({
                    "type": "缺失共现",
                    "symptom_a": sa,
                    "symptom_b": sb,
                    "expected": "应有共现",
                    "actual": "未检测到",
                    "possible_reason": "样本量不足或数据缺失"
                })
        
        return anomalies


# ========== 7. 聚类Agent ==========
class ClusterAgent(BaseAgent):
    """
    聚类Agent
    基于患者群做相似度聚类
    输出：患者聚类 + 聚类特征 + 代表方剂
    """
    
    def __init__(self, base_path: str = "./agent_data", llm: Optional[AgentLLM] = None):
        super().__init__("ClusterAgent", "clusters", base_path, llm=llm)
        self.cluster_counter = 0
    
    def generate(self, patient_files: List[str] = None, 
                n_clusters: int = 5) -> Dict:
        """实现抽象方法，委托给cluster"""
        return self.cluster(patient_files, n_clusters)
    
    def cluster(self, patient_files: List[str] = None, 
                n_clusters: int = 5) -> Dict:
        """
        患者聚类分析
        
        Args:
            patient_files: 患者档案文件路径列表
            n_clusters: 聚类数量
        """
        self.thinking_log = []
        self.log_thinking("开始", f"开始患者聚类分析，目标聚类数: {n_clusters}")
        
        # 加载患者数据
        patients = []
        if patient_files:
            for pf in patient_files:
                data = self.load(os.path.basename(pf))
                if data:
                    patients.append(data)
        
        if not patients:
            self.log_thinking("数据准备", "无患者数据，生成模拟数据")
            patients = self._generate_mock_patients(50)
        
        self.log_thinking("数据加载", f"加载 {len(patients)} 例患者档案")
        
        # 特征提取：症状向量
        all_symptoms = self._extract_all_symptoms(patients)
        self.log_thinking("特征提取", f"提取 {len(all_symptoms)} 个唯一症状特征")
        
        # 构建患者-症状矩阵
        patient_vectors = []
        for p in patients:
            vec = self._patient_to_vector(p, all_symptoms)
            patient_vectors.append({
                "patient_id": p.get("patient_id", "unknown"),
                "vector": vec,
                "profile": p.get("profile", {})
            })
        
        # 简单K-means聚类（简化实现）
        clusters = self._kmeans_clustering(patient_vectors, n_clusters, all_symptoms)
        
        self.log_thinking("聚类完成", f"完成聚类，生成 {len(clusters)} 个患者群")
        
        # 分析每个聚类的特征
        for cluster in clusters:
            cluster["characteristics"] = self._analyze_cluster_characteristics(
                cluster["patients"], all_symptoms
            )
            cluster["representative_prescriptions"] = self._find_representative_prescriptions(
                cluster["patients"]
            )
        
        self.cluster_counter += 1
        cluster_id = IDGenerator.cluster_id(self.cluster_counter)
        
        result_data = {
            "agent": "ClusterAgent",
            "version": "1.0",
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "cluster_id": cluster_id,
            "n_clusters": n_clusters,
            "total_patients": len(patients),
            "features": all_symptoms,
            "clusters": clusters,
            "cluster_quality": {
                "silhouette_score": 0.0,  # 轮廓系数（简化）
                "inertia": 0.0,  # 惯性
            }
        }
        
        # 使用 Yunwu API 结构化生成进行聚类证型标注
        llm_result = self._enrich_with_llm(
            "cluster", cases=patients, n_clusters=n_clusters
        )
        if llm_result:
            # 合并 LLM 对每个聚类的证型解释
            llm_syndromes = llm_result.get("syndromes", {})
            for cluster in result_data["clusters"]:
                idx = str(cluster["cluster_index"])
                if idx in llm_syndromes:
                    cluster["typical_syndrome"] = llm_syndromes[idx]
                if "characteristics" in cluster and isinstance(cluster["characteristics"], dict):
                    cluster["characteristics"].setdefault("typical_syndrome", cluster.get("typical_syndrome", ""))
            result_data["representative_cases"] = llm_result.get("representative_cases", [])
            result_data["llm_enriched"] = True
        
        self.log_thinking("分析完成", "聚类特征分析完成")
        
        filename = f"{cluster_id}.json"
        filepath = self.save(result_data, filename)
        
        return {
            "cluster_id": cluster_id,
            "filepath": filepath,
            "data": result_data,
            "thinking_log": self.thinking_log,
        }
    
    def _extract_all_symptoms(self, patients: List[Dict]) -> List[str]:
        """提取所有唯一症状"""
        symptoms = set()
        for p in patients:
            timeline = p.get("timeline", [])
            for event in timeline:
                for s in event.get("symptoms", []):
                    symptoms.add(s)
        return sorted(list(symptoms))
    
    def _patient_to_vector(self, patient: Dict, all_symptoms: List[str]) -> List[float]:
        """将患者转换为症状向量"""
        patient_symptoms = []
        timeline = patient.get("timeline", [])
        for event in timeline:
            patient_symptoms.extend(event.get("symptoms", []))
        
        return [1.0 if s in patient_symptoms else 0.0 for s in all_symptoms]
    
    def _kmeans_clustering(self, patient_vectors: List[Dict], n_clusters: int, 
                         all_symptoms: List[str]) -> List[Dict]:
        """简化K-means聚类"""
        # 随机初始化质心
        centroids = random.sample(patient_vectors, min(n_clusters, len(patient_vectors)))
        centroid_vecs = [p["vector"] for p in centroids]
        
        # 迭代（简化版，只做2轮）
        for iteration in range(2):
            # 分配患者到最近的质心
            clusters = [[] for _ in range(n_clusters)]
            
            for pv in patient_vectors:
                # 计算到每个质心的距离
                distances = []
                for cv in centroid_vecs:
                    dist = sum((a - b) ** 2 for a, b in zip(pv["vector"], cv)) ** 0.5
                    distances.append(dist)
                
                # 分配到最近的质心
                closest = distances.index(min(distances))
                clusters[closest].append(pv)
            
            # 重新计算质心
            for i, cluster in enumerate(clusters):
                if cluster:
                    n = len(cluster)
                    centroid_vecs[i] = [
                        sum(p["vector"][j] for p in cluster) / n
                        for j in range(len(all_symptoms))
                    ]
        
        # 构建结果
        result = []
        for i, cluster in enumerate(clusters):
            if cluster:
                result.append({
                    "cluster_index": i,
                    "cluster_name": f"患者群-{i+1}",
                    "patient_count": len(cluster),
                    "patients": [
                        {
                            "patient_id": p["patient_id"],
                            "profile": p.get("profile", {})
                        }
                        for p in cluster
                    ],
                    "centroid": centroid_vecs[i] if i < len(centroid_vecs) else [],
                    "characteristics": {},
                    "representative_prescriptions": [],
                })
        
        return result
    
    def _analyze_cluster_characteristics(self, patients: List[Dict], 
                                          all_symptoms: List[str]) -> Dict:
        """分析聚类特征"""
        # 统计高频症状
        symptom_freq = {}
        for p in patients:
            pid = p.get("patient_id", "")
            # 这里简化处理，实际应该从原始数据提取
            symptom_freq[pid] = symptom_freq.get(pid, 0) + 1
        
        return {
            "typical_symptoms": [],  # 典型症状
            "typical_syndrome": "",  # 典型证型
            "age_distribution": {},  # 年龄分布
            "gender_distribution": {},  # 性别分布
        }
    
    def _find_representative_prescriptions(self, patients: List[Dict]) -> List[str]:
        """找到代表性方剂"""
        prescriptions = []
        for p in patients:
            # 简化处理
            prescriptions.append("待分析")
        
        # 去重统计
        return list(set(prescriptions))[:5]
    
    def _generate_mock_patients(self, count: int) -> List[Dict]:
        """生成模拟患者"""
        patients = []
        for i in range(count):
            patients.append({
                "patient_id": f"MOCK-{i+1:03d}",
                "profile": {
                    "age": random.randint(20, 70),
                    "gender": random.choice(["male", "female"]),
                    "constitution": random.choice(["气虚质", "阳虚质", "阴虚质", "痰湿质"])
                },
                "timeline": [{
                    "symptoms": random.sample(
                        ["头痛", "发热", "恶寒", "乏力", "咳嗽", "失眠"], 
                        k=random.randint(2, 4)
                    )
                }]
            })
        return patients


# ========== Agent协调器 ==========
class AgentCoordinator:
    """
    Agent协调器
    管理所有Agent，协调任务分配，统一数据接口
    """
    
    def __init__(self, base_path: str = "./agent_data"):
        self.base_path = ensure_dirs(base_path)
        
        # 创建共享的 Yunwu API 客户端，统一供所有 Agent 使用
        self.llm = AgentLLM()
        
        # 初始化所有Agent，并注入共享 LLM
        self.agents = {
            "drug": DrugAgent(base_path, llm=self.llm),
            "symptom": SymptomAgent(base_path, llm=self.llm),
            "formula": FormulaAgent(base_path, llm=self.llm),
            "adverse": AdverseAgent(base_path, llm=self.llm),
            "patient": PatientAgent(base_path, llm=self.llm),
            "cooccurrence": CooccurrenceAgent(base_path, llm=self.llm),
            "cluster": ClusterAgent(base_path, llm=self.llm),
        }
        
        print(f"[AgentCoordinator] 协调器初始化完成，数据目录: {self.base_path}")
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """获取指定Agent"""
        return self.agents.get(name)
    
    def run_pipeline(self, tasks: List[Dict]) -> List[Dict]:
        """
        运行Agent流水线
        
        Args:
            tasks: [{"agent": "drug", "params": {"drug_name": "麻黄"}}]
        
        Returns:
            结果列表
        """
        results = []
        
        for task in tasks:
            agent_name = task.get("agent")
            params = task.get("params", {})
            
            agent = self.agents.get(agent_name)
            if not agent:
                results.append({"error": f"未知Agent: {agent_name}"})
                continue
            
            try:
                result = agent.generate(**params)
                results.append({
                    "agent": agent_name,
                    "success": True,
                    "result": result
                })
            except Exception as e:
                results.append({
                    "agent": agent_name,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    def get_all_stats(self) -> Dict:
        """获取所有Agent统计"""
        return {
            name: agent.get_stats()
            for name, agent in self.agents.items()
        }
    
    def export_knowledge_graph(self) -> Dict:
        """导出知识图谱（整合所有Agent数据）"""
        kg = {
            "nodes": [],
            "edges": [],
            "metadata": {
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "source": "MultiAgentSystem",
                "version": "1.0"
            }
        }
        
        # 加载所有节点
        for agent_name, agent in self.agents.items():
            for filename in agent.list_files():
                data = agent.load(filename)
                if data:
                    # 提取节点ID
                    node_id = data.get("drug_id") or data.get("symptom_id") or \
                              data.get("formula_id") or data.get("adverse_id") or \
                              data.get("patient_id") or data.get("cluster_id")
                    
                    if node_id:
                        kg["nodes"].append({
                            "id": node_id,
                            "type": agent_name,
                            "data": data
                        })
        
        # 构建边（简化版）
        # 药物-方剂关系
        # 症状-证型关系
        # 患者-症状关系
        # ...
        
        return kg


# ========== 单例 ==========
_coordinator = None

def get_agent_coordinator(base_path: str = "./agent_data") -> AgentCoordinator:
    global _coordinator
    if _coordinator is None:
        _coordinator = AgentCoordinator(base_path)
    return _coordinator


if __name__ == "__main__":
    # 测试多Agent系统
    print("=" * 60)
    print("多Agent知识库扩展系统测试")
    print("=" * 60)
    
    coord = AgentCoordinator("./test_agent_data")
    
    # 测试各Agent
    print("\n--- 药物Agent ---")
    drug_agent = coord.get_agent("drug")
    result = drug_agent.generate("麻黄", search_results=["麻黄性温味辛，归肺膀胱经，发汗解表"])
    print(f"生成: {result['drug_id']} - {result['name']}")
    print(f"文件: {result['filepath']}")
    
    print("\n--- 症状Agent ---")
    symptom_agent = coord.get_agent("symptom")
    result = symptom_agent.generate("头痛", body_part="TB", category="S")
    print(f"生成: {result['symptom_id']} - {result['name']}")
    
    print("\n--- 方剂Agent ---")
    formula_agent = coord.get_agent("formula")
    result = formula_agent.generate("麻黄汤", composition=[
        {"drug_id": "DR-0001", "name": "麻黄", "dose": "9g"},
        {"drug_id": "DR-0002", "name": "桂枝", "dose": "6g"},
    ])
    print(f"生成: {result['formula_id']} - {result['name']}")
    
    print("\n--- 副作用Agent ---")
    adverse_agent = coord.get_agent("adverse")
    result = adverse_agent.generate("DR-0001", "麻黄")
    print(f"生成: {result['adverse_id']} - {result['drug_name']}")
    
    print("\n--- 患者Agent ---")
    patient_agent = coord.get_agent("patient")
    result = patient_agent.generate()
    print(f"生成: {result['patient_id']}")
    
    print("\n--- 共现Agent ---")
    cooccur_agent = coord.get_agent("cooccurrence")
    result = cooccur_agent.analyze()
    print(f"分析: {result['data']['cooccurrence_pairs']} 对共现")
    
    print("\n--- 聚类Agent ---")
    cluster_agent = coord.get_agent("cluster")
    result = cluster_agent.cluster(n_clusters=3)
    print(f"聚类: {len(result['data']['clusters'])} 个患者群")
    
    print("\n--- 统计 ---")
    stats = coord.get_all_stats()
    for name, stat in stats.items():
        print(f"{name}: {stat['total_files']} 文件")
    
    print("\n" + "=" * 60)
    print("测试完成!")
