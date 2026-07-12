#!/usr/bin/env python3
"""
小神农中医AI - 真实网络爬虫
从公开中医网站爬取真实数据，目标10万条
数据源：
  - 中医世家 www.zhongyoo.com（中药、方剂）
  - 古诗文网 gushiwen.cn（中医古籍）
  - 公开API接口
"""

import os
import json
import time
import re
import hashlib
import random
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urljoin, quote
import argparse

import requests
from bs4 import BeautifulSoup

# ============ 配置 ============
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}

# 请求间隔（秒），遵守robots.txt精神
MIN_DELAY = 2.0
MAX_DELAY = 5.0

# API配置
YUNWU_API_KEY = "sk-kGZ5PiMxdpT91QzvvcGPMNk8Sp6Uzkmdmmaq20aE2kEEpzvl"
YUNWU_BASE_URL = "https://yunwu.ai/v1"

KIMI_API_KEY = "sk-kimi-dv9yPey41r9gtlv4nyIIZtaeqRCpGjbRR5cz78zF07kveFmx6kDlg4PCE4Dhj6xs"


def sleep_delay():
    """随机延迟，避免被封"""
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))


def fetch_url(url: str, retries: int = 3, timeout: int = 15) -> Optional[str]:
    """获取网页内容，带重试"""
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=timeout)
            resp.encoding = 'utf-8'
            if resp.status_code == 200:
                return resp.text
            elif resp.status_code == 429:
                wait_time = 60 * (attempt + 1)
                print(f"[Crawler] 429限流，等待{wait_time}秒...")
                time.sleep(wait_time)
            else:
                print(f"[Crawler] HTTP {resp.status_code}: {url}")
        except Exception as e:
            print(f"[Crawler] 请求失败({attempt+1}/{retries}): {url} - {e}")
            time.sleep(5 * (attempt + 1))
    return None


def save_data(data: List[Dict], filename: str, output_dir: str = "./data/raw") -> str:
    """保存数据到JSON文件"""
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[Crawler] 保存 {len(data)} 条数据到 {filepath}")
    return filepath


def load_existing_data(output_dir: str = "./data/raw") -> List[Dict]:
    """加载已爬取的数据，避免重复"""
    all_data = []
    data_path = Path(output_dir)
    if not data_path.exists():
        return all_data
    
    for json_file in sorted(data_path.glob("*.json")):
        if json_file.name in ['all_data.json', 'bulk_stats.json']:
            continue
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_data.extend(data)
                    print(f"[Crawler] 加载已有数据: {json_file.name} ({len(data)}条)")
        except Exception as e:
            print(f"[Crawler] 加载失败 {json_file.name}: {e}")
    
    return all_data


# ============ 爬虫1: 中医世家 - 中药数据 ============
class ZhongyooHerbCrawler:
    """从中医世家爬取中药数据"""
    
    BASE_URL = "https://www.zhongyoo.com"
    
    # 常见中药列表（约300味核心中药）
    CORE_HERBS = [
        "人参", "黄芪", "当归", "白术", "茯苓", "甘草", "白芍", "熟地黄", "生地黄", "川芎",
        "丹参", "红花", "桃仁", "赤芍", "牡丹皮", "柴胡", "黄芩", "黄连", "黄柏", "栀子",
        "金银花", "连翘", "板蓝根", "蒲公英", "鱼腥草", "麻黄", "桂枝", "紫苏", "生姜",
        "薄荷", "牛蒡子", "蝉蜕", "桑叶", "菊花", "蔓荆子", "升麻", "葛根", "石膏", "知母",
        "芦根", "天花粉", "夏枯草", "决明子", "龙胆", "秦皮", "苦参", "白鲜皮", "玄参", "紫草",
        "水牛角", "青蒿", "白薇", "地骨皮", "银柴胡", "胡黄连", "大黄", "芒硝", "番泻叶",
        "芦荟", "火麻仁", "郁李仁", "独活", "威灵仙", "川乌", "蕲蛇", "乌梢蛇", "木瓜",
        "秦艽", "防己", "桑枝", "五加皮", "桑寄生", "狗脊", "藿香", "佩兰", "苍术", "厚朴",
        "砂仁", "白豆蔻", "草豆蔻", "草果", "薏苡仁", "猪苓", "泽泻", "冬瓜皮", "玉米须",
        "车前子", "滑石", "木通", "通草", "瞿麦", "萹蓄", "地肤子", "海金沙", "石韦",
        "冬葵子", "灯心草", "萆薢", "茵陈", "金钱草", "虎杖", "附子", "干姜", "肉桂",
        "吴茱萸", "小茴香", "丁香", "高良姜", "花椒", "胡椒", "荜茇", "陈皮", "青皮",
        "枳实", "枳壳", "木香", "沉香", "檀香", "川楝子", "乌药", "荔枝核", "香附", "佛手",
        "香橼", "玫瑰花", "薤白", "大腹皮", "甘松", "九香虫", "刀豆", "柿蒂", "山楂",
        "神曲", "麦芽", "谷芽", "莱菔子", "鸡内金", "使君子", "苦楝皮", "槟榔", "南瓜子",
        "雷丸", "鹤虱", "榧子", "小蓟", "大蓟", "地榆", "槐花", "侧柏叶", "白茅根", "苎麻根",
        "三七", "茜草", "蒲黄", "白及", "仙鹤草", "紫珠", "炮姜", "艾叶", "灶心土", "延胡索",
        "郁金", "姜黄", "乳香", "没药", "五灵脂", "益母草", "泽兰", "牛膝", "鸡血藤",
        "王不留行", "月季花", "凌霄花", "土鳖虫", "自然铜", "苏木", "骨碎补", "血竭",
        "儿茶", "刘寄奴", "莪术", "三棱", "水蛭", "虻虫", "斑蝥", "穿山甲", "半夏", "天南星",
        "白芥子", "皂荚", "旋覆花", "白前", "浙贝母", "川贝母", "瓜蒌", "竹茹", "竹沥",
        "天竺黄", "前胡", "桔梗", "胖大海", "海藻", "昆布", "黄药子", "海蛤壳", "瓦楞子",
        "礞石", "紫苏子", "苦杏仁", "白果", "百部", "紫菀", "款冬花", "马兜铃", "枇杷叶",
        "桑白皮", "葶苈子", "矮地茶", "洋金花", "朱砂", "磁石", "龙骨", "琥珀", "酸枣仁",
        "柏子仁", "远志", "合欢皮", "首乌藤", "灵芝", "缬草", "珍珠母", "牡蛎", "紫贝齿",
        "代赭石", "刺蒺藜", "罗布麻", "生铁落", "羚羊角", "牛黄", "珍珠", "钩藤", "天麻",
        "地龙", "全蝎", "蜈蚣", "僵蚕", "麝香", "冰片", "苏合香", "石菖蒲", "蟾酥", "樟脑",
        "西洋参", "党参", "太子参", "山药", "白扁豆", "大枣", "刺五加", "绞股蓝", "红景天",
        "沙棘", "饴糖", "蜂蜜", "鹿茸", "紫河车", "淫羊藿", "巴戟天", "仙茅", "杜仲",
        "续断", "肉苁蓉", "锁阳", "补骨脂", "益智仁", "菟丝子", "沙苑子", "韭菜子", "核桃仁",
        "蛤蚧", "冬虫夏草", "胡芦巴", "海马", "海狗肾", "阳起石", "紫石英", "阿胶", "何首乌",
        "龙眼肉", "楮实子", "北沙参", "南沙参", "百合", "麦冬", "天冬", "石斛", "玉竹",
        "黄精", "明党参", "枸杞子", "墨旱莲", "女贞子", "桑葚", "黑芝麻", "龟甲", "鳖甲",
        "五味子", "乌梅", "五倍子", "罂粟壳", "诃子", "石榴皮", "肉豆蔻", "赤石脂", "禹余粮",
        "山茱萸", "覆盆子", "桑螵蛸", "海螵蛸", "金樱子", "莲子", "芡实", "刺猬皮", "椿皮",
        "鸡冠花", "浮小麦", "麻黄根", "糯稻根须", "常山", "瓜蒂", "胆矾", "藜芦", "雄黄",
        "硫黄", "白矾", "蛇床子", "土荆皮", "蜂房", "大蒜", "升药", "轻粉", "铅丹", "炉甘石", "硼砂"
    ]
    
    def __init__(self):
        self.herbs = []
        self.existing_names = set()
    
    def crawl(self, limit: int = 300) -> List[Dict]:
        """爬取中药数据"""
        print(f"[Crawler] 开始从中医世家爬取中药数据，目标{limit}味...")
        
        herbs_to_crawl = self.CORE_HERBS[:limit]
        
        for i, herb_name in enumerate(herbs_to_crawl):
            if herb_name in self.existing_names:
                print(f"[Crawler] 跳过已存在: {herb_name}")
                continue
            
            if i > 0 and i % 10 == 0:
                print(f"[Crawler] 进度: {i}/{len(herbs_to_crawl)}")
            
            # 构造URL
            encoded_name = quote(herb_name)
            url = f"{self.BASE_URL}/name/{encoded_name}.html"
            
            html = fetch_url(url)
            if not html:
                print(f"[Crawler] 无法获取: {herb_name}")
                continue
            
            herb_data = self._parse_herb_page(html, herb_name)
            if herb_data:
                self.herbs.append(herb_data)
                self.existing_names.add(herb_name)
                print(f"[Crawler] 成功: {herb_name}")
            else:
                print(f"[Crawler] 解析失败: {herb_name}")
            
            sleep_delay()
        
        print(f"[Crawler] 中药爬取完成，成功{len(self.herbs)}味")
        return self.herbs
    
    def _parse_herb_page(self, html: str, herb_name: str) -> Optional[Dict]:
        """解析中药详情页"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 提取信息
            info = {}
            
            # 查找信息表格
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True)
                        val = cells[1].get_text(strip=True)
                        info[key] = val
            
            # 查找详细内容
            content_div = soup.find('div', class_='content') or soup.find('div', class_='article')
            detail_text = ""
            if content_div:
                detail_text = content_div.get_text(separator='\n', strip=True)[:500]
            
            # 构建结构化数据
            nature = info.get('性味归经', '')
            effects = info.get('功效主治', '')
            usage = info.get('用法用量', '煎服')
            
            text = f"""{herb_name}
性味归经：{nature}
功效主治：{effects}
用法用量：{usage}
详细说明：{detail_text[:200]}
"""
            
            doc = {
                "text": text,
                "metadata": {
                    "source_book": "中药大辞典",
                    "source_section": herb_name,
                    "herb_name": herb_name,
                    "nature_flavor": nature,
                    "effects": effects,
                    "usage": usage,
                    "chunk_id": f"herb_{hashlib.md5(herb_name.encode()).hexdigest()[:12]}",
                    "data_source": "zhongyoo_crawler",
                    "type": "herb"
                }
            }
            
            return doc
            
        except Exception as e:
            print(f"[Crawler] 解析 {herb_name} 失败: {e}")
            return None


# ============ 爬虫2: 古诗文网 - 中医古籍 ============
class GushiwenClassicCrawler:
    """从古诗文网爬取中医古籍"""
    
    BASE_URL = "https://www.gushiwen.cn"
    
    # 中医古籍列表
    CLASSICS = [
        {"name": "黄帝内经", "url": "https://so.gushiwen.cn/guwen/book_6.aspx"},
        {"name": "伤寒论", "url": "https://so.gushiwen.cn/guwen/book_7.aspx"},
        {"name": "金匮要略", "url": "https://so.gushiwen.cn/guwen/book_8.aspx"},
        {"name": "神农本草经", "url": "https://so.gushiwen.cn/guwen/book_9.aspx"},
        {"name": "难经", "url": "https://so.gushiwen.cn/guwen/book_10.aspx"},
        {"name": "温病条辨", "url": "https://so.gushiwen.cn/guwen/book_11.aspx"},
        {"name": "本草纲目", "url": "https://so.gushiwen.cn/guwen/book_12.aspx"},
    ]
    
    def __init__(self):
        self.passages = []
    
    def crawl(self) -> List[Dict]:
        """爬取古籍数据"""
        print(f"[Crawler] 开始从古诗文网爬取中医古籍...")
        
        for classic in self.CLASSICS:
            print(f"[Crawler] 爬取《{classic['name']}》...")
            
            html = fetch_url(classic['url'])
            if not html:
                continue
            
            passages = self._parse_classic_page(html, classic['name'])
            self.passages.extend(passages)
            
            print(f"[Crawler] 《{classic['name']}》获取 {len(passages)} 条")
            sleep_delay()
        
        print(f"[Crawler] 古籍爬取完成，共{len(self.passages)}条")
        return self.passages
    
    def _parse_classic_page(self, html: str, book_name: str) -> List[Dict]:
        """解析古籍页面"""
        documents = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 查找内容段落
            content_div = soup.find('div', class_='bookcont') or soup.find('div', class_='main3')
            if not content_div:
                return documents
            
            # 提取所有段落
            paragraphs = content_div.find_all('p') or content_div.find_all('div', class_='cont')
            
            for i, para in enumerate(paragraphs):
                text = para.get_text(strip=True)
                if len(text) < 10:  # 跳过太短的
                    continue
                
                doc = {
                    "text": text[:500],  # 限制长度
                    "metadata": {
                        "source_book": book_name,
                        "source_section": f"第{i+1}段",
                        "chunk_id": f"classic_{hashlib.md5(f'{book_name}_{i}'.encode()).hexdigest()[:12]}",
                        "data_source": "gushiwen_crawler",
                        "type": "classic"
                    }
                }
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            print(f"[Crawler] 解析《{book_name}》失败: {e}")
            return documents


# ============ 爬虫3: 使用API获取数据 ============
class APICrawler:
    """使用API获取中医数据"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or YUNWU_API_KEY
        self.base_url = base_url or YUNWU_BASE_URL
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def generate_herb_data(self, herb_name: str) -> Optional[Dict]:
        """使用API生成中药结构化数据"""
        prompt = f"""请提供中药"{herb_name}"的详细信息，格式如下：
性味归经：
功效主治：
用法用量：
注意事项：
"""
        
        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3
                },
                timeout=30
            )
            
            if resp.status_code == 200:
                data = resp.json()
                content = data['choices'][0]['message']['content']
                
                text = f"""{herb_name}
{content}
"""
                
                doc = {
                    "text": text,
                    "metadata": {
                        "source_book": "中药大辞典",
                        "source_section": herb_name,
                        "herb_name": herb_name,
                        "chunk_id": f"herb_api_{hashlib.md5(herb_name.encode()).hexdigest()[:12]}",
                        "data_source": "api_generated",
                        "type": "herb"
                    }
                }
                return doc
            
        except Exception as e:
            print(f"[API] 获取 {herb_name} 失败: {e}")
        
        return None


# ============ 主程序 ============
def main():
    parser = argparse.ArgumentParser(description="小神农中医AI - 真实网络爬虫")
    parser.add_argument("--output-dir", default="./data/raw", help="输出目录")
    parser.add_argument("--mode", choices=['web', 'api', 'all'], default='all', help="爬取模式")
    parser.add_argument("--limit", type=int, default=300, help="中药数量限制")
    parser.add_argument("--target", type=int, default=100000, help="目标总条数")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("小神农中医AI - 真实网络爬虫")
    print("=" * 60)
    
    all_documents = []
    
    # 加载已有数据
    existing = load_existing_data(args.output_dir)
    if existing:
        print(f"[Crawler] 已有 {len(existing)} 条数据，将继续补充")
        all_documents.extend(existing)
    
    # 1. 爬取中药数据（网页）
    if args.mode in ['web', 'all']:
        herb_crawler = ZhongyooHerbCrawler()
        herb_crawler.existing_names = set(
            d.get('metadata', {}).get('herb_name', '') for d in existing 
            if d.get('metadata', {}).get('type') == 'herb'
        )
        herbs = herb_crawler.crawl(limit=args.limit)
        if herbs:
            save_data(herbs, "crawled_herbs.json", args.output_dir)
            all_documents.extend(herbs)
    
    # 2. 爬取古籍数据
    if args.mode in ['web', 'all']:
        classic_crawler = GushiwenClassicCrawler()
        classics = classic_crawler.crawl()
        if classics:
            save_data(classics, "crawled_classics.json", args.output_dir)
            all_documents.extend(classics)
    
    # 3. 使用API补充
    if args.mode in ['api', 'all']:
        api_crawler = APICrawler()
        # 可以补充更多数据...
    
    # 保存合并文件
    save_data(all_documents, "all_crawled_data.json", args.output_dir)
    
    print("=" * 60)
    print(f"爬取完成！总计: {len(all_documents)} 条")
    print(f"目标: {args.target} 条")
    print(f"差距: {max(0, args.target - len(all_documents))} 条")
    print("=" * 60)


if __name__ == "__main__":
    main()
