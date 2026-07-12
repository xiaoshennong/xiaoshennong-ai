#!/usr/bin/env python3
"""
小神农中医AI - 古籍批量下载器
从公开渠道批量下载已数字化的古籍文本

核心策略：
1. 优先使用已有文本化资源（txt/json/html）
2. 自动转换为统一JSON格式
3. 人工只处理网上找不到的稀缺古籍

数据来源：
- 中国哲学书电子化计划 (ctext.org) - 有API
- 维基文库 (zh.wikisource.org) - 大量古籍
- 古诗文网 (gushiwen.cn) - 中医古籍
- 本地已有的PDF/扫描件（需OCR）
"""

import os
import json
import time
import re
from pathlib import Path
from typing import List, Dict, Optional
import urllib.request
import urllib.error


# MVP阶段核心100部古籍清单（按优先级排序）
CORE_BOOKS_100 = [
    # P0: 最核心10部（MVP必须）
    {"name": "黄帝内经", "dynasty": "先秦", "author": "佚名", "priority": "P0"},
    {"name": "伤寒论", "dynasty": "东汉", "author": "张仲景", "priority": "P0"},
    {"name": "金匮要略", "dynasty": "东汉", "author": "张仲景", "priority": "P0"},
    {"name": "神农本草经", "dynasty": "东汉", "author": "佚名", "priority": "P0"},
    {"name": "本草纲目", "dynasty": "明", "author": "李时珍", "priority": "P0"},
    {"name": "温病条辨", "dynasty": "清", "author": "吴鞠通", "priority": "P0"},
    {"name": "医宗金鉴", "dynasty": "清", "author": "吴谦", "priority": "P0"},
    {"name": "千金要方", "dynasty": "唐", "author": "孙思邈", "priority": "P0"},
    {"name": "脾胃论", "dynasty": "金", "author": "李东垣", "priority": "P0"},
    {"name": "丹溪心法", "dynasty": "元", "author": "朱丹溪", "priority": "P0"},
    
    # P1: 重要经典20部
    {"name": "素问", "dynasty": "先秦", "author": "佚名", "priority": "P1"},
    {"name": "灵枢", "dynasty": "先秦", "author": "佚名", "priority": "P1"},
    {"name": "难经", "dynasty": "战国", "author": "扁鹊", "priority": "P1"},
    {"name": "脉经", "dynasty": "晋", "author": "王叔和", "priority": "P1"},
    {"name": "针灸甲乙经", "dynasty": "晋", "author": "皇甫谧", "priority": "P1"},
    {"name": "诸病源候论", "dynasty": "隋", "author": "巢元方", "priority": "P1"},
    {"name": "备急千金要方", "dynasty": "唐", "author": "孙思邈", "priority": "P1"},
    {"name": "外台秘要", "dynasty": "唐", "author": "王焘", "priority": "P1"},
    {"name": "太平圣惠方", "dynasty": "宋", "author": "王怀隐", "priority": "P1"},
    {"name": "圣济总录", "dynasty": "宋", "author": "赵佶", "priority": "P1"},
    {"name": "妇人良方", "dynasty": "宋", "author": "陈自明", "priority": "P1"},
    {"name": "小儿药证直诀", "dynasty": "宋", "author": "钱乙", "priority": "P1"},
    {"name": "局方发挥", "dynasty": "元", "author": "朱丹溪", "priority": "P1"},
    {"name": "格致余论", "dynasty": "元", "author": "朱丹溪", "priority": "P1"},
    {"name": "儒门事亲", "dynasty": "金", "author": "张从正", "priority": "P1"},
    {"name": "卫生宝鉴", "dynasty": "元", "author": "罗天益", "priority": "P1"},
    {"name": "世医得效方", "dynasty": "元", "author": "危亦林", "priority": "P1"},
    {"name": "饮膳正要", "dynasty": "元", "author": "忽思慧", "priority": "P1"},
    {"name": "本草备要", "dynasty": "清", "author": "汪昂", "priority": "P1"},
    {"name": "医林改错", "dynasty": "清", "author": "王清任", "priority": "P1"},
    
    # P2: 扩展70部（略，实际需要时补充）
]


class BookDownloader:
    """古籍下载器"""
    
    def __init__(self, output_dir: str = "./data/raw"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 下载统计
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0
        }
    
    def download_from_ctext(self, book_name: str, book_id: str) -> bool:
        """
        从ctext.org下载古籍
        ctext API格式: https://api.ctext.org/gettext?urn=ctp:book_id
        """
        url = f"https://api.ctext.org/gettext?urn=ctp:{book_id}"
        
        try:
            print(f"  尝试从ctext.org下载: {book_name}")
            
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            
            if "error" in data:
                print(f"    ✗ ctext.org无此古籍: {data['error']}")
                return False
            
            # 转换为统一格式
            book_data = {
                "book_name": book_name,
                "dynasty": self._infer_dynasty(book_name),
                "author": "佚名",
                "source": "ctext.org",
                "source_url": f"https://ctext.org/{book_id}",
                "sections": []
            }
            
            # 解析章节
            for chapter in data.get("chapters", []):
                book_data["sections"].append({
                    "section_name": chapter.get("title", "未知篇章"),
                    "original_text": chapter.get("text", "")
                })
            
            # 保存
            self._save_book(book_data)
            print(f"    ✓ 成功下载: {book_name} ({len(book_data['sections'])}章)")
            self.stats["success"] += 1
            return True
            
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"    ✗ ctext.org未找到: {book_name}")
            else:
                print(f"    ✗ HTTP错误 {e.code}: {book_name}")
            return False
        except Exception as e:
            print(f"    ✗ 下载失败: {book_name}, {e}")
            return False
    
    def download_from_wikisource(self, book_name: str) -> bool:
        """
        从维基文库下载
        优势：大量古籍已文本化，质量高
        """
        # 维基文库API
        encoded_name = urllib.parse.quote(book_name)
        url = f"https://zh.wikisource.org/w/api.php?action=parse&page={encoded_name}&prop=text&format=json"
        
        try:
            print(f"  尝试从维基文库下载: {book_name}")
            
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (Xiaoshennong TCM AI Project)'}
            )
            
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            
            if "error" in data:
                print(f"    ✗ 维基文库无此古籍")
                return False
            
            # 解析HTML内容
            html = data["parse"]["text"]["*"]
            
            # 简单提取文本（去掉HTML标签）
            text = re.sub(r'<[^>]+>', '', html)
            text = re.sub(r'\[编辑\]', '', text)
            
            # 分段
            paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
            
            book_data = {
                "book_name": book_name,
                "dynasty": self._infer_dynasty(book_name),
                "author": "佚名",
                "source": "zh.wikisource.org",
                "source_url": f"https://zh.wikisource.org/wiki/{encoded_name}",
                "sections": [
                    {
                        "section_name": f"第{i+1}段",
                        "original_text": p
                    }
                    for i, p in enumerate(paragraphs[:100])  # 最多100段
                ]
            }
            
            self._save_book(book_data)
            print(f"    ✓ 成功下载: {book_name} ({len(book_data['sections'])}段)")
            self.stats["success"] += 1
            return True
            
        except Exception as e:
            print(f"    ✗ 下载失败: {e}")
            return False
    
    def create_from_local_text(self, book_name: str, text_file: str) -> bool:
        """
        从本地文本文件创建古籍数据
        用于处理网上下载的txt文件
        """
        try:
            filepath = Path(text_file)
            if not filepath.exists():
                print(f"  ✗ 本地文件不存在: {text_file}")
                return False
            
            print(f"  从本地文件导入: {book_name}")
            
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # 智能分段（按章节标题或空行）
            sections = self._split_into_sections(text)
            
            book_data = {
                "book_name": book_name,
                "dynasty": self._infer_dynasty(book_name),
                "author": "佚名",
                "source": "local_file",
                "source_file": text_file,
                "sections": sections
            }
            
            self._save_book(book_data)
            print(f"    ✓ 成功导入: {book_name} ({len(sections)}章)")
            self.stats["success"] += 1
            return True
            
        except Exception as e:
            print(f"    ✗ 导入失败: {e}")
            return False
    
    def _split_into_sections(self, text: str) -> List[Dict]:
        """智能分段"""
        # 尝试按常见章节标题分割
        chapter_patterns = [
            r'第[一二三四五六七八九十百千]+[章卷篇]',  # 第一章
            r'卷[一二三四五六七八九十]+',  # 卷一
            r'[\d]+、',  # 1、
            r'[\d]+\.',  # 1.
        ]
        
        for pattern in chapter_patterns:
            matches = list(re.finditer(pattern, text))
            if len(matches) > 3:  # 至少找到3个章节
                sections = []
                for i, match in enumerate(matches):
                    start = match.start()
                    end = matches[i+1].start() if i+1 < len(matches) else len(text)
                    
                    sections.append({
                        "section_name": match.group(0),
                        "original_text": text[start:end].strip()
                    })
                
                return sections
        
        #  fallback: 按空行分段
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        return [
            {
                "section_name": f"第{i+1}段",
                "original_text": p
            }
            for i, p in enumerate(paragraphs)
        ]
    
    def _save_book(self, book_data: Dict) -> str:
        """保存古籍数据为JSON"""
        filename = self._slugify(book_data["book_name"]) + ".json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(book_data, f, ensure_ascii=False, indent=2)
        
        return str(filepath)
    
    def _infer_dynasty(self, title: str) -> str:
        """推断朝代"""
        dynasty_map = {
            "黄帝内经": "先秦", "素问": "先秦", "灵枢": "先秦",
            "伤寒论": "东汉", "金匮要略": "东汉", "神农本草经": "东汉",
            "难经": "战国", "脉经": "晋", "针灸甲乙经": "晋",
            "诸病源候论": "隋", "千金要方": "唐", "备急千金要方": "唐",
            "外台秘要": "唐", "太平圣惠方": "宋", "圣济总录": "宋",
            "妇人良方": "宋", "小儿药证直诀": "宋",
            "儒门事亲": "金", "脾胃论": "金",
            "丹溪心法": "元", "格致余论": "元", "局方发挥": "元",
            "卫生宝鉴": "元", "世医得效方": "元", "饮膳正要": "元",
            "本草纲目": "明",
            "医宗金鉴": "清", "温病条辨": "清", "本草备要": "清", "医林改错": "清",
        }
        
        for book, dynasty in dynasty_map.items():
            if book in title:
                return dynasty
        
        return "未知"
    
    def _slugify(self, text: str) -> str:
        """生成文件名"""
        text = re.sub(r'[^\u4e00-\u9fff\w]', '_', text)
        return text[:50]
    
    def batch_download(self, books: List[Dict]) -> Dict:
        """批量下载古籍"""
        print(f"\n开始批量下载 {len(books)} 部古籍...")
        print("=" * 50)
        
        for book in books:
            self.stats["total"] += 1
            book_name = book["name"]
            
            # 检查是否已存在
            filename = self._slugify(book_name) + ".json"
            if (self.output_dir / filename).exists():
                print(f"[{self.stats['total']}/{len(books)}] {book_name} - 已存在，跳过")
                self.stats["skipped"] += 1
                continue
            
            print(f"\n[{self.stats['total']}/{len(books)}] 下载: {book_name}")
            
            # 尝试多个来源
            success = False
            
            # 1. 尝试ctext.org
            book_id = self._name_to_ctext_id(book_name)
            if book_id and self.download_from_ctext(book_name, book_id):
                success = True
            
            # 2. 尝试维基文库
            if not success:
                time.sleep(1)  # 礼貌间隔
                if self.download_from_wikisource(book_name):
                    success = True
            
            if not success:
                self.stats["failed"] += 1
                print(f"  → 标记为需人工处理: {book_name}")
            
            time.sleep(1)  # 请求间隔
        
        return self.stats
    
    def _name_to_ctext_id(self, book_name: str) -> Optional[str]:
        """书名转换为ctext ID"""
        mapping = {
            "黄帝内经": "huangdi-neijing",
            "伤寒论": "shang-han-lun",
            "金匮要略": "jin-gui-yao-lue",
            "神农本草经": "shen-nong-ben-cao-jing",
            "本草纲目": "ben-cao-gang-mu",
            "温病条辨": "wen-bing-tiao-bian",
            "医宗金鉴": "yi-zong-jin-jian",
            "千金要方": "qian-jin-yao-fang",
            "脾胃论": "pi-wei-lun",
            "丹溪心法": "dan-xi-xin-fa",
            "素问": "su-wen",
            "灵枢": "ling-shu",
            "难经": "nan-jing",
            "脉经": "mai-jing",
            "针灸甲乙经": "zhen-jiu-jia-yi-jing",
        }
        return mapping.get(book_name)
    
    def generate_report(self) -> str:
        """生成下载报告"""
        report = []
        report.append("\n" + "=" * 50)
        report.append("下载报告")
        report.append("=" * 50)
        report.append(f"总计: {self.stats['total']} 部")
        report.append(f"成功: {self.stats['success']} 部")
        report.append(f"失败: {self.stats['failed']} 部")
        report.append(f"跳过: {self.stats['skipped']} 部")
        report.append(f"")
        report.append(f"成功率: {self.stats['success']/max(self.stats['total'],1)*100:.1f}%")
        report.append(f"")
        report.append(f"数据保存位置: {self.output_dir}")
        report.append(f"需人工处理: {self.stats['failed']} 部")
        
        return "\n".join(report)


def main():
    """主函数"""
    print("=" * 50)
    print("小神农中医AI - 古籍批量下载器")
    print("=" * 50)
    print("\n策略：")
    print("  1. 自动从公开渠道下载已有数字化古籍")
    print("  2. 人工只处理网上找不到的稀缺古籍")
    print("  3. 最大化利用人力成本\n")
    
    downloader = BookDownloader()
    
    # 下载P0优先级古籍（最核心10部）
    p0_books = [b for b in CORE_BOOKS_100 if b["priority"] == "P0"]
    print(f"\n>>> 下载P0核心古籍 ({len(p0_books)}部)")
    downloader.batch_download(p0_books)
    
    # 下载P1优先级古籍
    p1_books = [b for b in CORE_BOOKS_100 if b["priority"] == "P1"]
    print(f"\n>>> 下载P1重要古籍 ({len(p1_books)}部)")
    downloader.batch_download(p1_books)
    
    # 生成报告
    print(downloader.generate_report())
    
    # 生成待人工处理清单
    if downloader.stats["failed"] > 0:
        print("\n" + "=" * 50)
        print("待人工处理清单（网上找不到，需扫描/OCR）")
        print("=" * 50)
        
        for book in CORE_BOOKS_100:
            filename = downloader._slugify(book["name"]) + ".json"
            if not (downloader.output_dir / filename).exists():
                print(f"  - {book['name']} ({book['dynasty']}, {book['author']})")
        
        print(f"\n建议：")
        print(f"  1. 优先处理P0级古籍（MVP必需）")
        print(f"  2. 联系中医科学院图书馆或国家图书馆获取扫描件")
        print(f"  3. 使用PaddleOCR进行批量OCR识别")
        print(f"  4. 安排学生团队进行人工校验")


if __name__ == "__main__":
    main()
