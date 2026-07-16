#!/usr/bin/env python3
"""
小神农中医AI - 网络搜索模块 v1.0
真正的联网搜索能力，为各Agent提供实时数据

搜索策略：
1. 公开中医网站爬取（中医世家、古诗文网等）
2. LLM API知识检索（Yunwu AI / Kimi）
3. 学术数据库搜索（PubMed/知网 - 预留接口）
"""

import os
import json
import time
import re
import random
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote, urljoin
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup


# ========== 配置 ==========
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

# API Keys（统一使用 Yunwu AI，从环境变量读取，不再硬编码）
YUNWU_API_KEY = os.getenv("YUNWU_API_KEY", "")
YUNWU_BASE_URL = os.getenv("YUNWU_API_BASE") or os.getenv("YUNWU_BASE_URL", "https://yunwu.ai/v1")

# 请求间隔
MIN_DELAY = 1.5
MAX_DELAY = 3.0


def sleep_delay():
    """随机延迟，避免被封"""
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))


@dataclass
class SearchResult:
    """搜索结果"""
    title: str
    content: str
    source: str
    url: str
    relevance_score: float = 0.0
    search_method: str = ""  # web_crawl / llm_api / local_db


class WebSearchEngine:
    """
    网络搜索引擎
    从多个公开中医网站爬取数据
    """
    
    # 中医网站数据源
    SOURCES = {
        "zhongyoo": {
            "name": "中医世家",
            "base_url": "https://www.zhongyoo.com",
            "search_pattern": "https://www.zhongyoo.com/search?q={query}",
            "herb_pattern": "https://www.zhongyoo.com/name/{name}.html",
            "formula_pattern": "https://www.zhongyoo.com/fang/{name}.html",
        },
        "zhongyishiku": {
            "name": "中医智库",
            "base_url": "https://www.zhongyishiku.com",
            "search_pattern": "https://www.zhongyishiku.com/search?keyword={query}",
        },
        "gushiwen": {
            "name": "古诗文网",
            "base_url": "https://so.gushiwen.cn",
            "search_pattern": "https://so.gushiwen.cn/search.aspx?value={query}",
        },
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.request_count = 0
        print("[WebSearchEngine] 网络搜索引擎初始化完成")
    
    def search_herb(self, herb_name: str) -> List[SearchResult]:
        """搜索中药信息"""
        results = []
        
        # 1. 尝试中医世家
        url = self.SOURCES["zhongyoo"]["herb_pattern"].format(name=quote(herb_name))
        result = self._fetch_page(url, herb_name)
        if result:
            results.append(result)
        
        # 2. 通用搜索
        search_results = self._search_general(herb_name + " 中药 性味归经 功效")
        results.extend(search_results)
        
        return results
    
    def search_formula(self, formula_name: str) -> List[SearchResult]:
        """搜索方剂信息"""
        results = []
        
        # 1. 尝试中医世家
        url = self.SOURCES["zhongyoo"]["formula_pattern"].format(name=quote(formula_name))
        result = self._fetch_page(url, formula_name)
        if result:
            results.append(result)
        
        # 2. 通用搜索
        search_results = self._search_general(formula_name + " 方剂 组成 功效")
        results.extend(search_results)
        
        return results
    
    def search_symptom(self, symptom_name: str) -> List[SearchResult]:
        """搜索症状信息"""
        query = f"{symptom_name} 症状 中医 辨证 常见证型"
        return self._search_general(query)
    
    def search_adverse(self, drug_name: str) -> List[SearchResult]:
        """搜索药物副作用"""
        query = f"{drug_name} 副作用 不良反应 禁忌 毒性"
        return self._search_general(query)
    
    def search_clinical(self, condition: str) -> List[SearchResult]:
        """搜索临床研究/医案"""
        query = f"{condition} 中医 医案 临床治疗 疗效"
        return self._search_general(query)
    
    def _fetch_page(self, url: str, keyword: str, retries: int = 2) -> Optional[SearchResult]:
        """获取页面内容"""
        for attempt in range(retries):
            try:
                sleep_delay()
                resp = self.session.get(url, timeout=15)
                resp.encoding = 'utf-8'
                self.request_count += 1
                
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    
                    # 提取标题
                    title = soup.title.string if soup.title else keyword
                    
                    # 提取正文（移除脚本和样式）
                    for script in soup(["script", "style", "nav", "footer"]):
                        script.decompose()
                    
                    text = soup.get_text(separator='\n', strip=True)
                    # 清理空白行
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    content = '\n'.join(lines[:50])  # 取前50行
                    
                    # 计算相关性
                    relevance = self._calculate_relevance(content, keyword)
                    
                    return SearchResult(
                        title=title[:100],
                        content=content[:2000],  # 限制长度
                        source=url,
                        url=url,
                        relevance_score=relevance,
                        search_method="web_crawl"
                    )
                
                elif resp.status_code == 404:
                    print(f"[WebSearch] 页面不存在: {url}")
                    return None
                elif resp.status_code == 429:
                    wait_time = 30 * (attempt + 1)
                    print(f"[WebSearch] 429限流，等待{wait_time}秒...")
                    time.sleep(wait_time)
                
            except Exception as e:
                print(f"[WebSearch] 请求失败({attempt+1}/{retries}): {url} - {e}")
                time.sleep(5 * (attempt + 1))
        
        return None
    
    def _search_general(self, query: str, max_results: int = 3) -> List[SearchResult]:
        """通用搜索（简化版，使用Bing搜索结果或模拟）"""
        results = []
        
        # 由于无法直接调用搜索引擎API，这里使用几种策略：
        # 1. 尝试直接访问已知页面
        # 2. 使用LLM API进行知识检索
        
        # 策略1：尝试中医世家的搜索页面
        # 注意：实际搜索页面通常需要JS渲染，这里简化处理
        
        # 策略2：使用LLM API获取知识
        llm_results = self._search_via_llm(query)
        results.extend(llm_results)
        
        return results[:max_results]
    
    def _search_via_llm(self, query: str) -> List[SearchResult]:
        """通过LLM API获取知识（模拟网络搜索）"""
        try:
            # 使用Yunwu AI API进行知识检索
            headers = {
                "Authorization": f"Bearer {YUNWU_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个中医知识检索助手。请基于你的知识库，提供关于以下查询的详细信息。请确保信息准确，并标注来源。"
                    },
                    {
                        "role": "user",
                        "content": f"请详细检索并提供关于「{query}」的中医相关信息。包括：定义、分类、功效、主治、用法、注意事项等。请用结构化格式输出。"
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 2000
            }
            
            resp = requests.post(
                f"{YUNWU_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                
                return [SearchResult(
                    title=f"LLM检索: {query}",
                    content=content,
                    source="Yunwu AI Knowledge Base",
                    url="",
                    relevance_score=0.8,
                    search_method="llm_api"
                )]
            
        except Exception as e:
            print(f"[WebSearch] LLM搜索失败: {e}")
        
        return []
    
    def _calculate_relevance(self, content: str, keyword: str) -> float:
        """计算内容相关性"""
        keyword_lower = keyword.lower()
        content_lower = content.lower()
        
        # 基础匹配
        if keyword_lower in content_lower:
            score = 0.5
            
            # 关键词出现次数
            count = content_lower.count(keyword_lower)
            score += min(0.3, count * 0.05)
            
            # 内容长度（适中更好）
            length = len(content)
            if 500 < length < 5000:
                score += 0.1
            
            return min(1.0, score)
        
        return 0.1


class LLMKnowledgeSearch:
    """
    LLM知识检索引擎
    利用大模型API进行结构化知识检索
    优势：速度快、结构化、无需爬取
    限制：依赖模型知识截止日期
    """
    
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or YUNWU_API_KEY
        self.base_url = base_url or YUNWU_BASE_URL
        self.request_count = 0
        print("[LLMKnowledgeSearch] LLM知识检索引擎初始化完成")
    
    def search(self, query: str, search_type: str = "general") -> List[SearchResult]:
        """
        LLM知识检索
        
        Args:
            query: 搜索查询
            search_type: 搜索类型 (drug/symptom/formula/adverse/clinical/general)
        """
        # 根据类型构建不同的提示词
        prompts = {
            "drug": f"请详细检索中药「{query}」的信息，包括：性味归经、功效主治、用法用量、现代研究、注意事项。用JSON格式输出。",
            "symptom": f"请详细检索中医症状「{query}」的信息，包括：定义、常见证型、鉴别要点、伴随症状、治疗原则。用JSON格式输出。",
            "formula": f"请详细检索中医方剂「{query}」的信息，包括：组成、功效、主治、方解、加减变化、现代应用。用JSON格式输出。",
            "adverse": f"请检索药物「{query}」的副作用信息，包括：不良反应、毒性、禁忌人群、药物相互作用、过量处理。用JSON格式输出。",
            "clinical": f"请检索「{query}」的中医临床研究信息，包括：常见证型、治疗方案、疗效统计、典型医案。用JSON格式输出。",
            "general": f"请检索中医相关知识：{query}。提供详细、准确的信息。",
        }
        
        prompt = prompts.get(search_type, prompts["general"])
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的中医知识检索助手。请基于中医典籍和现代医学研究，提供准确、详细的结构化信息。所有信息必须可溯源，不确定的内容请标注'待验证'。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.2,
                "max_tokens": 2000
            }
            
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            self.request_count += 1
            
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                
                return [SearchResult(
                    title=f"LLM知识检索: {query}",
                    content=content,
                    source="LLM Knowledge Retrieval",
                    url="",
                    relevance_score=0.85,
                    search_method="llm_api"
                )]
            else:
                print(f"[LLMSearch] API错误: {resp.status_code} - {resp.text[:200]}")
        
        except Exception as e:
            print(f"[LLMSearch] 请求失败: {e}")
        
        return []
    
    def batch_search(self, queries: List[str], search_type: str = "general") -> Dict[str, List[SearchResult]]:
        """批量搜索"""
        results = {}
        for query in queries:
            results[query] = self.search(query, search_type)
            time.sleep(1)  # 避免限流
        return results


class HybridSearchEngine:
    """
    混合搜索引擎
    结合网络爬取 + LLM知识检索 + 本地数据库
    提供最优的搜索结果
    """
    
    def __init__(self):
        self.web_engine = WebSearchEngine()
        self.llm_engine = LLMKnowledgeSearch()
        self.local_db = None  # 可接入本地知识库
        print("[HybridSearchEngine] 混合搜索引擎初始化完成")
    
    def search(self, query: str, search_type: str = "general", 
               use_web: bool = True, use_llm: bool = True, 
               max_results: int = 5) -> List[SearchResult]:
        """
        混合搜索
        
        Args:
            query: 搜索查询
            search_type: 搜索类型
            use_web: 是否使用网络爬取
            use_llm: 是否使用LLM检索
            max_results: 最大结果数
        """
        all_results = []
        
        # 1. LLM知识检索（优先，速度快）
        if use_llm:
            print(f"[HybridSearch] LLM检索: {query}")
            llm_results = self.llm_engine.search(query, search_type)
            all_results.extend(llm_results)
        
        # 2. 网络爬取（补充，真实数据）
        if use_web:
            print(f"[HybridSearch] 网络检索: {query}")
            if search_type == "drug":
                web_results = self.web_engine.search_herb(query)
            elif search_type == "formula":
                web_results = self.web_engine.search_formula(query)
            elif search_type == "symptom":
                web_results = self.web_engine.search_symptom(query)
            elif search_type == "adverse":
                web_results = self.web_engine.search_adverse(query)
            elif search_type == "clinical":
                web_results = self.web_engine.search_clinical(query)
            else:
                web_results = self.web_engine._search_general(query)
            
            all_results.extend(web_results)
        
        # 去重排序
        seen = set()
        unique_results = []
        for r in all_results:
            key = r.content[:100]  # 用内容前100字去重
            if key not in seen:
                seen.add(key)
                unique_results.append(r)
        
        # 按相关性排序
        unique_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return unique_results[:max_results]
    
    def get_stats(self) -> Dict:
        """获取搜索统计"""
        return {
            "web_requests": self.web_engine.request_count,
            "llm_requests": self.llm_engine.request_count,
            "total_requests": self.web_engine.request_count + self.llm_engine.request_count,
        }


# ========== 单例 ==========
_hybrid_search = None

def get_hybrid_search_engine() -> HybridSearchEngine:
    global _hybrid_search
    if _hybrid_search is None:
        _hybrid_search = HybridSearchEngine()
    return _hybrid_search


if __name__ == "__main__":
    # 测试混合搜索引擎
    print("=" * 60)
    print("混合搜索引擎测试")
    print("=" * 60)
    
    engine = HybridSearchEngine()
    
    # 测试1: 搜索中药
    print("\n--- 测试1: 搜索中药 ---")
    results = engine.search("麻黄", search_type="drug", max_results=3)
    print(f"找到 {len(results)} 条结果")
    for i, r in enumerate(results, 1):
        print(f"\n结果{i}: [{r.search_method}] {r.title}")
        print(f"相关性: {r.relevance_score}")
        print(f"内容预览: {r.content[:200]}...")
    
    # 测试2: 搜索方剂
    print("\n--- 测试2: 搜索方剂 ---")
    results = engine.search("麻黄汤", search_type="formula", max_results=2)
    print(f"找到 {len(results)} 条结果")
    for i, r in enumerate(results, 1):
        print(f"\n结果{i}: [{r.search_method}] {r.title}")
        print(f"内容预览: {r.content[:200]}...")
    
    # 测试3: 搜索症状
    print("\n--- 测试3: 搜索症状 ---")
    results = engine.search("头痛", search_type="symptom", max_results=2)
    print(f"找到 {len(results)} 条结果")
    for i, r in enumerate(results, 1):
        print(f"\n结果{i}: [{r.search_method}] {r.title}")
        print(f"内容预览: {r.content[:200]}...")
    
    # 统计
    print("\n" + "=" * 60)
    print("搜索统计:")
    print(json.dumps(engine.get_stats(), ensure_ascii=False, indent=2))
    print("=" * 60)
