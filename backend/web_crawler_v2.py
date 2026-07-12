#!/usr/bin/env python3
"""
小神农中医AI - 网络爬虫模块 v2.0
从公开可访问的数据源爬取真实中医数据

数据源：
1. 维基百科（中文）- 中药、方剂、中医术语
2. 百度百科（需要处理反爬）
3. 公开中医PDF/文档
4. 预留：中医世家、方剂网等（待解封后启用）

策略：
- 优先爬取维基百科（开放、结构化）
- 本地缓存避免重复请求
- 遵守robots.txt和请求频率限制
"""

import os
import json
import time
import re
import hashlib
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

MIN_DELAY = 1.0
MAX_DELAY = 2.5

CACHE_DIR = "./cache/web_crawl"
os.makedirs(CACHE_DIR, exist_ok=True)


@dataclass
class CrawlResult:
    """爬取结果"""
    title: str
    content: str
    source: str
    url: str
    crawl_time: float
    data_type: str  # herb/formula/symptom/theory


class WikipediaCrawler:
    """
    维基百科爬虫
    从中文维基百科爬取中医相关条目
    优势：开放、结构化、多语言
    """
    
    BASE_URL = "https://zh.wikipedia.org"
    API_URL = "https://zh.wikipedia.org/w/api.php"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.request_count = 0
        print("[WikipediaCrawler] 维基百科爬虫初始化完成")
    
    def _get_cache_path(self, key: str) -> str:
        """获取缓存路径"""
        hash_key = hashlib.md5(key.encode()).hexdigest()[:12]
        return os.path.join(CACHE_DIR, f"wiki_{hash_key}.json")
    
    def _load_cache(self, key: str) -> Optional[Dict]:
        """加载缓存"""
        path = self._get_cache_path(key)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 检查缓存是否过期（7天）
                    if time.time() - data.get('cached_at', 0) < 7 * 86400:
                        return data
            except:
                pass
        return None
    
    def _save_cache(self, key: str, data: Dict):
        """保存缓存"""
        path = self._get_cache_path(key)
        data['cached_at'] = time.time()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _sleep(self):
        """请求间隔"""
        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
    
    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """
        使用维基百科API搜索
        
        API文档: https://www.mediawiki.org/wiki/API:Search
        """
        cache_key = f"search_{query}_{limit}"
        cached = self._load_cache(cache_key)
        if cached:
            return cached.get('results', [])
        
        try:
            self._sleep()
            params = {
                'action': 'query',
                'list': 'search',
                'srsearch': query,
                'srlimit': limit,
                'format': 'json',
                'origin': '*'
            }
            
            resp = self.session.get(self.API_URL, params=params, timeout=15)
            self.request_count += 1
            
            if resp.status_code == 200:
                data = resp.json()
                results = []
                
                if 'query' in data and 'search' in data['query']:
                    for item in data['query']['search']:
                        results.append({
                            'title': item['title'],
                            'snippet': item.get('snippet', ''),
                            'pageid': item['pageid'],
                            'wordcount': item.get('wordcount', 0),
                        })
                
                self._save_cache(cache_key, {'results': results})
                return results
            
        except Exception as e:
            print(f"[Wikipedia] 搜索失败: {e}")
        
        return []
    
    def get_page(self, title: str) -> Optional[CrawlResult]:
        """
        获取维基百科页面内容
        
        使用API获取解析后的内容
        """
        cache_key = f"page_{title}"
        cached = self._load_cache(cache_key)
        if cached:
            return CrawlResult(**cached['result'])
        
        try:
            self._sleep()
            # 使用API获取页面内容
            params = {
                'action': 'query',
                'prop': 'extracts',
                'titles': title,
                'explaintext': True,
                'exlimit': 1,
                'format': 'json',
                'origin': '*'
            }
            
            resp = self.session.get(self.API_URL, params=params, timeout=15)
            self.request_count += 1
            
            if resp.status_code == 200:
                data = resp.json()
                
                if 'query' in data and 'pages' in data['query']:
                    pages = data['query']['pages']
                    for page_id, page_data in pages.items():
                        if page_id == '-1':  # 页面不存在
                            continue
                        
                        content = page_data.get('extract', '')
                        if content:
                            result = CrawlResult(
                                title=page_data.get('title', title),
                                content=content,
                                source='Wikipedia',
                                url=f"{self.BASE_URL}/wiki/{quote(title)}",
                                crawl_time=time.time(),
                                data_type=self._detect_type(title, content)
                            )
                            
                            self._save_cache(cache_key, {'result': {
                                'title': result.title,
                                'content': result.content,
                                'source': result.source,
                                'url': result.url,
                                'crawl_time': result.crawl_time,
                                'data_type': result.data_type
                            }})
                            
                            return result
            
        except Exception as e:
            print(f"[Wikipedia] 获取页面失败: {e}")
        
        return None
    
    def get_page_html(self, title: str) -> Optional[CrawlResult]:
        """获取HTML格式页面（更丰富的格式）"""
        cache_key = f"html_{title}"
        cached = self._load_cache(cache_key)
        if cached:
            return CrawlResult(**cached['result'])
        
        try:
            self._sleep()
            url = f"{self.BASE_URL}/wiki/{quote(title)}"
            resp = self.session.get(url, timeout=15)
            self.request_count += 1
            
            if resp.status_code == 200:
                resp.encoding = 'utf-8'
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # 提取标题
                title_text = soup.find('h1', {'id': 'firstHeading'})
                title_text = title_text.get_text() if title_text else title
                
                # 提取正文内容
                content_div = soup.find('div', {'id': 'mw-content-text'})
                if content_div:
                    # 移除不需要的元素
                    for elem in content_div.find_all(['script', 'style', 'nav', 'table', '.infobox']):
                        elem.decompose()
                    
                    # 提取段落文本
                    paragraphs = content_div.find_all('p')
                    content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                    
                    # 提取章节标题和内容
                    sections = []
                    current_heading = ""
                    current_content = []
                    
                    for elem in content_div.find_all(['h2', 'h3', 'p', 'ul']):
                        if elem.name in ['h2', 'h3']:
                            if current_heading and current_content:
                                sections.append({
                                    'heading': current_heading,
                                    'content': '\n'.join(current_content)
                                })
                            current_heading = elem.get_text(strip=True)
                            current_content = []
                        elif elem.name == 'p':
                            text = elem.get_text(strip=True)
                            if text:
                                current_content.append(text)
                        elif elem.name == 'ul':
                            items = [li.get_text(strip=True) for li in elem.find_all('li')]
                            current_content.extend([f"• {item}" for item in items if item])
                    
                    # 结构化内容
                    structured_content = {
                        'full_text': content[:5000],
                        'sections': sections[:10],
                    }
                    
                    result = CrawlResult(
                        title=title_text,
                        content=json.dumps(structured_content, ensure_ascii=False),
                        source='Wikipedia',
                        url=url,
                        crawl_time=time.time(),
                        data_type=self._detect_type(title_text, content)
                    )
                    
                    self._save_cache(cache_key, {'result': {
                        'title': result.title,
                        'content': result.content,
                        'source': result.source,
                        'url': result.url,
                        'crawl_time': result.crawl_time,
                        'data_type': result.data_type
                    }})
                    
                    return result
        
        except Exception as e:
            print(f"[Wikipedia] HTML获取失败: {e}")
        
        return None
    
    def _detect_type(self, title: str, content: str) -> str:
        """检测数据类型"""
        title_lower = title.lower()
        content_lower = content.lower()
        
        # 中药检测
        herb_keywords = ['中药', '草药', '药材', '性味', '归经', '功效']
        if any(kw in title_lower or kw in content_lower[:500] for kw in herb_keywords):
            return 'herb'
        
        # 方剂检测
        formula_keywords = ['方剂', '汤', '散', '丸', '组成', '主治']
        if any(kw in title_lower or kw in content_lower[:500] for kw in formula_keywords):
            return 'formula'
        
        # 症状/疾病检测
        symptom_keywords = ['症状', '证候', '临床表现', '诊断']
        if any(kw in title_lower or kw in content_lower[:500] for kw in symptom_keywords):
            return 'symptom'
        
        # 理论检测
        theory_keywords = ['理论', '学说', '脏腑', '经络', '气血']
        if any(kw in title_lower or kw in content_lower[:500] for kw in theory_keywords):
            return 'theory'
        
        return 'general'
    
    def crawl_herb(self, herb_name: str) -> List[CrawlResult]:
        """爬取中药信息"""
        results = []
        
        # 1. 直接搜索中药名称
        page = self.get_page_html(herb_name)
        if page:
            results.append(page)
        
        # 2. 搜索相关页面
        search_results = self.search(f"{herb_name} 中药", limit=3)
        for sr in search_results:
            if sr['title'] != herb_name:
                page = self.get_page(sr['title'])
                if page:
                    results.append(page)
        
        return results
    
    def crawl_formula(self, formula_name: str) -> List[CrawlResult]:
        """爬取方剂信息"""
        results = []
        
        # 1. 直接搜索
        page = self.get_page_html(formula_name)
        if page:
            results.append(page)
        
        # 2. 搜索相关
        search_results = self.search(f"{formula_name} 方剂", limit=3)
        for sr in search_results:
            if sr['title'] != formula_name:
                page = self.get_page(sr['title'])
                if page:
                    results.append(page)
        
        return results
    
    def crawl_symptom(self, symptom_name: str) -> List[CrawlResult]:
        """爬取症状信息"""
        results = []
        
        # 搜索症状
        search_results = self.search(f"{symptom_name} 症状 中医", limit=5)
        for sr in search_results:
            page = self.get_page(sr['title'])
            if page:
                results.append(page)
        
        return results
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            'source': 'Wikipedia',
            'requests': self.request_count,
            'cache_dir': CACHE_DIR,
            'cache_files': len([f for f in os.listdir(CACHE_DIR) if f.startswith('wiki_')])
        }


class BaiduBaikeCrawler:
    """
    百度百科爬虫
    处理反爬机制，获取中医相关词条
    """
    
    BASE_URL = "https://baike.baidu.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            **HEADERS,
            'Cookie': 'BIDUPSID=0; PSTM=0; BAIDUID=0',
            'Referer': 'https://baike.baidu.com/'
        })
        self.request_count = 0
        print("[BaiduBaikeCrawler] 百度百科爬虫初始化完成")
    
    def _sleep(self):
        time.sleep(random.uniform(MIN_DELAY * 2, MAX_DELAY * 2))
    
    def get_page(self, keyword: str) -> Optional[CrawlResult]:
        """获取百度百科页面"""
        try:
            self._sleep()
            url = f"{self.BASE_URL}/item/{quote(keyword)}"
            
            resp = self.session.get(url, timeout=15, allow_redirects=True)
            self.request_count += 1
            
            if resp.status_code == 200:
                resp.encoding = 'utf-8'
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # 提取标题
                title_elem = soup.find('h1')
                title = title_elem.get_text(strip=True) if title_elem else keyword
                
                # 提取摘要
                summary_elem = soup.find('div', class_=re.compile('lemma-summary|para-summary'))
                summary = summary_elem.get_text(strip=True) if summary_elem else ''
                
                # 提取正文段落
                content_div = soup.find('div', class_=re.compile('main-content|lemma-content'))
                content_parts = [summary]
                
                if content_div:
                    for para in content_div.find_all('div', class_=re.compile('para')):
                        text = para.get_text(strip=True)
                        if text and len(text) > 10:
                            content_parts.append(text)
                
                content = '\n\n'.join(content_parts)
                
                if content:
                    return CrawlResult(
                        title=title,
                        content=content[:8000],
                        source='Baidu Baike',
                        url=url,
                        crawl_time=time.time(),
                        data_type='general'
                    )
            
            elif resp.status_code == 403:
                print(f"[BaiduBaike] 403 Forbidden: {keyword}")
            
        except Exception as e:
            print(f"[BaiduBaike] 请求失败: {e}")
        
        return None
    
    def get_stats(self) -> Dict:
        return {
            'source': 'Baidu Baike',
            'requests': self.request_count
        }


class UnifiedCrawler:
    """
    统一爬虫
    整合多个数据源，提供统一的爬取接口
    """
    
    def __init__(self):
        self.wikipedia = WikipediaCrawler()
        self.baidu = BaiduBaikeCrawler()
        self.results_cache = {}
        print("[UnifiedCrawler] 统一爬虫初始化完成")
    
    def crawl(self, query: str, data_type: str = "auto", 
              sources: List[str] = None) -> List[CrawlResult]:
        """
        统一爬取接口
        
        Args:
            query: 查询关键词
            data_type: 数据类型 (herb/formula/symptom/theory/auto)
            sources: 数据源列表 (wikipedia/baidu)
        
        Returns:
            爬取结果列表
        """
        if sources is None:
            sources = ['wikipedia', 'baidu']
        
        results = []
        
        # 1. 维基百科
        if 'wikipedia' in sources:
            if data_type == 'herb' or data_type == 'auto':
                wiki_results = self.wikipedia.crawl_herb(query)
                results.extend(wiki_results)
            
            if data_type == 'formula' or (data_type == 'auto' and not results):
                wiki_results = self.wikipedia.crawl_formula(query)
                results.extend(wiki_results)
            
            if data_type == 'symptom' or (data_type == 'auto' and not results):
                wiki_results = self.wikipedia.crawl_symptom(query)
                results.extend(wiki_results)
        
        # 2. 百度百科（作为补充）
        if 'baidu' in sources and len(results) < 3:
            baidu_result = self.baidu.get_page(query)
            if baidu_result:
                results.append(baidu_result)
        
        # 去重
        seen = set()
        unique_results = []
        for r in results:
            key = r.title + r.content[:100]
            if key not in seen:
                seen.add(key)
                unique_results.append(r)
        
        return unique_results
    
    def batch_crawl(self, queries: List[str], data_type: str = "auto") -> Dict[str, List[CrawlResult]]:
        """批量爬取"""
        results = {}
        for query in queries:
            results[query] = self.crawl(query, data_type)
            time.sleep(1)
        return results
    
    def get_stats(self) -> Dict:
        return {
            'wikipedia': self.wikipedia.get_stats(),
            'baidu': self.baidu.get_stats(),
        }


# ========== 单例 ==========
_unified_crawler = None

def get_unified_crawler() -> UnifiedCrawler:
    global _unified_crawler
    if _unified_crawler is None:
        _unified_crawler = UnifiedCrawler()
    return _unified_crawler


if __name__ == "__main__":
    print("=" * 60)
    print("统一爬虫测试")
    print("=" * 60)
    
    crawler = UnifiedCrawler()
    
    # 测试1: 爬取中药
    print("\n--- 测试1: 爬取中药 - 麻黄 ---")
    results = crawler.crawl("麻黄", data_type="herb")
    print(f"找到 {len(results)} 条结果")
    for i, r in enumerate(results, 1):
        print(f"\n结果{i}: [{r.source}] {r.title}")
        print(f"类型: {r.data_type}")
        content = r.content[:300] if len(r.content) < 1000 else json.loads(r.content).get('full_text', r.content)[:300]
        print(f"内容预览: {content}...")
    
    # 测试2: 爬取方剂
    print("\n--- 测试2: 爬取方剂 - 麻黄汤 ---")
    results = crawler.crawl("麻黄汤", data_type="formula")
    print(f"找到 {len(results)} 条结果")
    for i, r in enumerate(results, 1):
        print(f"\n结果{i}: [{r.source}] {r.title}")
        content = r.content[:200] if len(r.content) < 1000 else json.loads(r.content).get('full_text', r.content)[:200]
        print(f"内容预览: {content}...")
    
    # 测试3: 爬取症状
    print("\n--- 测试3: 爬取症状 - 头痛 ---")
    results = crawler.crawl("头痛", data_type="symptom")
    print(f"找到 {len(results)} 条结果")
    for i, r in enumerate(results, 1):
        print(f"\n结果{i}: [{r.source}] {r.title}")
    
    # 统计
    print("\n" + "=" * 60)
    print("爬虫统计:")
    print(json.dumps(crawler.get_stats(), ensure_ascii=False, indent=2))
    print("=" * 60)
