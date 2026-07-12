#!/usr/bin/env python3
"""
小神农中医AI - 古籍爬虫模块
自动抓取网上已有的数字化古籍资源，减少人工扫描工作量

目标网站：
- 中国哲学书电子化计划 (ctext.org) - 大量古籍，结构化好
- 殆知阁 (oushidai.com) - 古籍检索
- 汉典 (zdic.net) - 汉字+古籍
- 书格 (shuge.org) - 高清扫描件

策略：
1. 优先抓取已有文本化（非扫描件）的古籍
2. 只抓取公版/无版权古籍
3. 结构化存储，直接入知识库
4. 人工只处理网上找不到的稀缺古籍
"""

import os
import json
import time
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urljoin, quote
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup


@dataclass
class ScrapedBook:
    """爬取的古籍信息"""
    title: str
    dynasty: str
    author: str
    source_url: str
    sections: List[Dict]  # [{"section_name": "...", "text": "..."}]
    is_complete: bool  # 是否完整抓取


class CTextScraper:
    """
    中国哲学书电子化计划 (ctext.org) 爬虫
    优势：
    - 大量古籍已文本化
    - API友好，结构清晰
    - 公版古籍为主
    """
    
    BASE_URL = "https://ctext.org"
    API_URL = "https://api.ctext.org"
    
    def __init__(self, delay: float = 1.0):
        self.delay = delay  # 请求间隔，避免被封
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_books(self, query: str) -> List[Dict]:
        """搜索古籍"""
        url = f"{self.API_URL}/search?q={quote(query)}"
        
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            books = []
            for item in data.get("results", []):
                books.append({
                    "title": item.get("title", ""),
                    "id": item.get("id", ""),
                    "url": f"{self.BASE_URL}{item.get('link', '')}"
                })
            
            return books
        except Exception as e:
            print(f"[CText] 搜索失败: {e}")
            return []
    
    def get_book_text(self, book_id: str) -> Optional[ScrapedBook]:
        """
        获取古籍全文
        ctext.org的API格式：/api/gettext?urn=ctp:book_id
        """
        url = f"{self.API_URL}/gettext?urn=ctp:{book_id}"
        
        try:
            print(f"[CText] 获取古籍: {book_id}")
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            if "error" in data:
                print(f"[CText] API错误: {data['error']}")
                return None
            
            # 解析返回数据
            title = data.get("title", book_id)
            
            sections = []
            for chapter in data.get("chapters", []):
                section = {
                    "section_name": chapter.get("title", "未知篇章"),
                    "original_text": chapter.get("text", ""),
                    "text": chapter.get("text", "")  # 原文
                }
                sections.append(section)
            
            return ScrapedBook(
                title=title,
                dynasty=self._infer_dynasty(title),
                author="佚名",  # ctext.org通常不直接提供作者
                source_url=f"{self.BASE_URL}/{book_id}",
                sections=sections,
                is_complete=True
            )
            
        except Exception as e:
            print(f"[CText] 获取失败: {e}")
            return None
    
    def _infer_dynasty(self, title: str) -> str:
        """根据书名推断朝代（简化版）"""
        dynasty_map = {
            "黄帝内经": "先秦",
            "伤寒论": "东汉",
            "金匮要略": "东汉",
            "神农本草经": "东汉",
            "本草纲目": "明",
            "千金要方": "唐",
            "医宗金鉴": "清",
            "温病条辨": "清",
            "脾胃论": "金",
            "丹溪心法": "元",
        }
        
        for book, dynasty in dynasty_map.items():
            if book in title:
                return dynasty
        
        return "未知"
    
    def fetch_core_books(self) -> List[ScrapedBook]:
        """
        抓取核心古籍列表
        优先抓取MVP阶段需要的100部核心古籍
        """
        core_books = [
            "huangdi-neijing",      # 黄帝内经
            "shang-han-lun",        # 伤寒论
            "jin-gui-yao-lue",      # 金匮要略
            "shen-nong-ben-cao-jing", # 神农本草经
            "ben-cao-gang-mu",      # 本草纲目
            "qian-jin-yao-fang",    # 千金要方
            "yi-zong-jin-jian",     # 医宗金鉴
            "wen-bing-tiao-bian",   # 温病条辨
        ]
        
        results = []
        for book_id in core_books:
            book = self.get_book_text(book_id)
            if book:
                results.append(book)
                print(f"[CText] ✓ 成功抓取: {book.title} ({len(book.sections)}章)")
            else:
                print(f"[CText] ✗ 抓取失败: {book_id}")
            
            time.sleep(self.delay)
        
        return results


class SimpleWebScraper:
    """
    通用网页爬虫
    用于抓取其他来源的古籍文本
    """
    
    def __init__(self, delay: float = 1.0):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_page(self, url: str) -> Optional[str]:
        """获取网页内容"""
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            resp.encoding = 'utf-8'
            return resp.text
        except Exception as e:
            print(f"[Web] 获取失败: {url}, 错误: {e}")
            return None
    
    def parse_text_content(self, html: str, selector: str = "body") -> str:
        """从HTML中提取文本内容"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # 移除脚本和样式
        for script in soup(["script", "style"]):
            script.decompose()
        
        # 提取指定区域的文本
        content = soup.select_one(selector)
        if content:
            return content.get_text(separator='\n', strip=True)
        
        return soup.get_text(separator='\n', strip=True)


class BookImporter:
    """
    古籍导入器
    将爬取的古籍转换为知识库格式并导入
    """
    
    def __init__(self, output_dir: str = "./data/raw"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def save_book(self, book: ScrapedBook) -> str:
        """将爬取的古籍保存为JSON格式"""
        
        data = {
            "book_name": book.title,
            "dynasty": book.dynasty,
            "author": book.author,
            "source_url": book.source_url,
            "is_scraped": True,
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "sections": book.sections
        }
        
        # 生成文件名
        filename = self._slugify(book.title) + ".json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"[Importer] 保存古籍: {book.title} -> {filepath}")
        return str(filepath)
    
    def batch_import_to_rag(self, rag_engine, books: List[ScrapedBook]) -> int:
        """批量导入到RAG知识库"""
        from data_pipeline import DataPipeline
        
        pipeline = DataPipeline()
        total = 0
        
        for book in books:
            # 先保存为JSON文件
            filepath = self.save_book(book)
            
            # 然后导入到知识库
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                documents = pipeline.process_json_file(filepath)
                
                if documents:
                    rag_engine.add_documents(documents)
                    total += len(documents)
                    print(f"[Importer] 导入知识库: {book.title} ({len(documents)}条)")
            
            except Exception as e:
                print(f"[Importer] 导入失败: {book.title}, {e}")
        
        return total
    
    def _slugify(self, text: str) -> str:
        """生成文件名"""
        text = re.sub(r'[^\u4e00-\u9fff\w]', '_', text)
        return text[:50]


def run_crawler():
    """运行爬虫，抓取核心古籍"""
    
    print("=" * 50)
    print("小神农中医AI - 古籍爬虫")
    print("=" * 50)
    
    # 初始化组件
    ctext = CTextScraper(delay=1.0)
    importer = BookImporter(output_dir="./data/raw")
    
    # 抓取核心古籍
    print("\n[1/3] 从ctext.org抓取核心古籍...")
    books = ctext.fetch_core_books()
    
    if not books:
        print("\n[警告] 未抓取到任何古籍，尝试备用方案...")
        print("备用方案：使用本地示例数据")
        return 0
    
    print(f"\n[2/3] 成功抓取 {len(books)} 部古籍")
    
    # 保存到本地
    print("\n[3/3] 保存古籍数据...")
    for book in books:
        importer.save_book(book)
    
    print(f"\n完成！共抓取 {len(books)} 部古籍")
    print(f"数据保存位置: {importer.output_dir}")
    
    # 显示摘要
    print("\n抓取结果摘要:")
    for book in books:
        total_chars = sum(len(s["text"]) for s in book.sections)
        print(f"  - {book.title} ({book.dynasty}): {len(book.sections)}章, {total_chars}字")
    
    return len(books)


def import_to_knowledge_base():
    """将爬取的数据导入知识库"""
    
    print("\n" + "=" * 50)
    print("导入知识库")
    print("=" * 50)
    
    from rag_engine import XiaoShennongRAG
    from data_pipeline import DataPipeline
    
    rag = XiaoShennongRAG(db_path="./data/chroma_db")
    pipeline = DataPipeline()
    importer = BookImporter()
    
    # 导入所有JSON文件
    raw_dir = Path("./data/raw")
    total = 0
    
    for json_file in sorted(raw_dir.glob("*.json")):
        try:
            documents = pipeline.process_json_file(str(json_file))
            if documents:
                rag.add_documents(documents)
                total += len(documents)
                print(f"  ✓ {json_file.name}: {len(documents)}条")
        except Exception as e:
            print(f"  ✗ {json_file.name}: {e}")
    
    print(f"\n共导入 {total} 条文档到知识库")
    print(f"知识库统计: {rag.get_stats()}")
    
    return total


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="小神农古籍爬虫")
    parser.add_argument("--crawl", action="store_true", help="运行爬虫抓取古籍")
    parser.add_argument("--import", action="store_true", dest="import_kb", help="导入知识库")
    parser.add_argument("--all", action="store_true", help="抓取并导入")
    
    args = parser.parse_args()
    
    if args.crawl or args.all:
        run_crawler()
    
    if args.import_kb or args.all:
        import_to_knowledge_base()
    
    if not any([args.crawl, args.import_kb, args.all]):
        parser.print_help()
