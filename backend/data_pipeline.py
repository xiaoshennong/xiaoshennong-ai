#!/usr/bin/env python3
"""
小神农中医AI - 数据导入管道
功能：OCR识别 → 结构化 → 向量化入库
"""

import os
import json
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
import argparse


class DataPipeline:
    """
    数据导入管道
    处理流程：原始数据 → 清洗 → 分块 → 结构化 → 向量化 → 入库
    """
    
    def __init__(self, raw_dir: str = "./data/raw", processed_dir: str = "./data/processed"):
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    
    def process_json_file(self, filepath: str) -> List[Dict]:
        """
        处理结构化的JSON古籍文件
        输入格式：{"book_name": "...", "sections": [{"section_name": "...", "original_text": "..."}]}
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        book_name = data.get("book_name", "未知")
        dynasty = data.get("dynasty", "未知")
        author = data.get("author", "佚名")
        
        documents = []
        
        for section in data.get("sections", []):
            section_name = section.get("section_name", "未知篇章")
            original_text = section.get("original_text", "")
            
            if not original_text.strip():
                continue
            
            # 分块处理（按句子或段落）
            chunks = self._split_text(original_text, max_length=300)
            
            for i, chunk_text in enumerate(chunks):
                # 生成唯一ID（使用hash确保唯一）
                unique_str = f"{book_name}_{section_name}_{chunk_text[:50]}_{i}"
                chunk_id = f"{self._slugify(book_name)}_{self._slugify(section_name)}_{hashlib.md5(unique_str.encode()).hexdigest()[:8]}"
                
                doc = {
                    "text": chunk_text,
                    "metadata": {
                        "source_book": book_name,
                        "source_section": section_name,
                        "dynasty": dynasty,
                        "author": author,
                        "original_text": original_text if i == 0 else "",  # 只在第一个chunk存全文
                        "chunk_index": i,
                        "chunk_id": chunk_id,
                        "data_source": "json_import"
                    }
                }
                documents.append(doc)
        
        return documents
    
    def process_text_file(self, filepath: str, book_name: str, 
                          section_pattern: str = None) -> List[Dict]:
        """
        处理纯文本古籍文件
        可以按特定模式自动分篇章
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
        
        documents = []
        
        if section_pattern:
            # 按正则表达式分篇章
            sections = re.split(section_pattern, text)
            section_names = re.findall(section_pattern, text)
            
            for i, (section_text, section_name) in enumerate(zip(sections[1:], section_names)):
                chunks = self._split_text(section_text, max_length=300)
                
                for j, chunk_text in enumerate(chunks):
                    chunk_id = f"{self._slugify(book_name)}_sec{i}_chunk{j}"
                    
                    doc = {
                        "text": chunk_text,
                        "metadata": {
                            "source_book": book_name,
                            "source_section": section_name,
                            "original_text": section_text if j == 0 else "",
                            "chunk_index": j,
                            "chunk_id": chunk_id,
                            "data_source": "text_import"
                        }
                    }
                    documents.append(doc)
        else:
            # 不分篇章，整体处理
            chunks = self._split_text(text, max_length=300)
            
            for i, chunk_text in enumerate(chunks):
                chunk_id = f"{self._slugify(book_name)}_chunk{i}"
                
                doc = {
                    "text": chunk_text,
                    "metadata": {
                        "source_book": book_name,
                        "source_section": "全文",
                        "original_text": text if i == 0 else "",
                        "chunk_index": i,
                        "chunk_id": chunk_id,
                        "data_source": "text_import"
                    }
                }
                documents.append(doc)
        
        return documents
    
    def process_formula_file(self, filepath: str) -> List[Dict]:
        """
        处理方剂JSON文件
        输入格式：方剂列表
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            formulas = json.load(f)
        
        documents = []
        
        for formula in formulas:
            formula_name = formula.get("formula_name", "未知方剂")
            source_book = formula.get("source_book", "未知")
            source_section = formula.get("source_section", "未知")
            
            # 构建文本描述
            composition = formula.get("composition", [])
            comp_text = "，".join([
                f"{c['herb']}{c.get('dosage', '')}{c.get('preparation', '')}" 
                for c in composition
            ])
            
            indications = formula.get("indications", [])
            effects = formula.get("effects", [])
            
            text = f"""{formula_name}，出自《{source_book}》{source_section}。
组成：{comp_text}。
主治：{"、".join(indications)}。
功效：{"、".join(effects)}。
"""
            
            chunk_id = f"formula_{self._slugify(formula_name)}"
            
            doc = {
                "text": text,
                "metadata": {
                    "source_book": source_book,
                    "source_section": source_section,
                    "formula_name": formula_name,
                    "original_text": formula.get("source_text", ""),
                    "chunk_id": chunk_id,
                    "data_source": "formula_import",
                    "type": "formula"
                }
            }
            documents.append(doc)
        
        return documents
    
    def _split_text(self, text: str, max_length: int = 300, overlap: int = 50) -> List[str]:
        """
        将长文本分块
        策略：按句子边界切分，保持语义完整
        """
        # 按句号、问号、感叹号分句
        sentences = re.split(r'([。！？；])', text)
        
        # 合并句子和标点
        chunks = []
        current = ""
        
        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            if i + 1 < len(sentences):
                sentence += sentences[i + 1]  # 加上标点
            
            if len(current) + len(sentence) <= max_length:
                current += sentence
            else:
                if current:
                    chunks.append(current.strip())
                current = sentence
        
        if current:
            chunks.append(current.strip())
        
        return chunks if chunks else [text[:max_length]]
    
    def _slugify(self, text: str) -> str:
        """生成URL友好的ID"""
        # 移除标点，保留中文和数字
        text = re.sub(r'[^\u4e00-\u9fff\w]', '_', text)
        return text[:30]
    
    def save_processed(self, documents: List[Dict], output_name: str) -> str:
        """保存处理后的数据"""
        output_path = self.processed_dir / f"{output_name}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(documents, f, ensure_ascii=False, indent=2)
        
        print(f"[Pipeline] 保存 {len(documents)} 条文档到 {output_path}")
        return str(output_path)
    
    def batch_import(self, rag_engine, data_dir: str = "./data/raw") -> int:
        """
        批量导入目录下的所有数据文件
        """
        data_path = Path(data_dir)
        total = 0
        
        # 处理JSON古籍文件
        for json_file in sorted(data_path.glob("*.json")):
            print(f"[Pipeline] 处理 {json_file.name}")
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    first_char = f.read(1)
                    f.seek(0)
                    
                    if first_char == '[':
                        # 方剂列表格式
                        documents = self.process_formula_file(str(json_file))
                    else:
                        # 古籍格式
                        documents = self.process_json_file(str(json_file))
                
                if documents:
                    rag_engine.add_documents(documents)
                    total += len(documents)
                    
                    # 保存处理后的数据
                    self.save_processed(documents, json_file.stem)
            
            except Exception as e:
                print(f"[Pipeline] 处理 {json_file.name} 失败: {e}")
        
        # 处理纯文本文件
        for txt_file in sorted(data_path.glob("*.txt")):
            print(f"[Pipeline] 处理 {txt_file.name}")
            
            try:
                # 从文件名推断书名
                book_name = txt_file.stem
                documents = self.process_text_file(str(txt_file), book_name)
                
                if documents:
                    rag_engine.add_documents(documents)
                    total += len(documents)
                    self.save_processed(documents, txt_file.stem)
            
            except Exception as e:
                print(f"[Pipeline] 处理 {txt_file.name} 失败: {e}")
        
        print(f"[Pipeline] 批量导入完成，共 {total} 条文档")
        return total


def create_sample_data(base_dir=None):
    """创建示例数据文件，用于测试"""
    
    import os
    if base_dir is None:
        base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    sample_dir = Path(base_dir) / "raw"
    sample_dir.mkdir(parents=True, exist_ok=True)
    
    # 示例1：伤寒论片段
    shanghanlun = {
        "book_name": "伤寒论",
        "dynasty": "东汉",
        "author": "张仲景",
        "sections": [
            {
                "section_name": "太阳病篇第一条",
                "original_text": "太阳之为病，脉浮，头项强痛而恶寒。"
            },
            {
                "section_name": "第35条",
                "original_text": "太阳病，头痛发热，身疼腰痛，骨节疼痛，恶风无汗而喘者，麻黄汤主之。"
            },
            {
                "section_name": "第12条",
                "original_text": "太阳中风，阳浮而阴弱，阳浮者，热自发，阴弱者，汗自出，啬啬恶寒，淅淅恶风，翕翕发热，鼻鸣干呕者，桂枝汤主之。"
            }
        ]
    }
    
    with open(sample_dir / "shanghanlun.json", 'w', encoding='utf-8') as f:
        json.dump(shanghanlun, f, ensure_ascii=False, indent=2)
    
    # 示例2：黄帝内经片段
    huangdi = {
        "book_name": "黄帝内经",
        "dynasty": "先秦",
        "author": "佚名",
        "sections": [
            {
                "section_name": "素问·上古天真论",
                "original_text": "昔在黄帝，生而神灵，弱而能言，幼而徇齐，长而敦敏，成而登天。乃问于天师曰：余闻上古之人，春秋皆度百岁，而动作不衰；今时之人，年半百而动作皆衰者，时世异耶？人将失之耶？"
            },
            {
                "section_name": "素问·阴阳应象大论",
                "original_text": "阴阳者，天地之道也，万物之纲纪，变化之父母，生杀之本始，神明之府也。"
            }
        ]
    }
    
    with open(sample_dir / "huangdi_neijing.json", 'w', encoding='utf-8') as f:
        json.dump(huangdi, f, ensure_ascii=False, indent=2)
    
    # 示例3：方剂数据
    formulas = [
        {
            "formula_id": "mahuang_tang",
            "formula_name": "麻黄汤",
            "source_book": "伤寒论",
            "source_section": "第35条",
            "composition": [
                {"herb": "麻黄", "dosage": "三两", "preparation": "去节"},
                {"herb": "桂枝", "dosage": "二两", "preparation": "去皮"},
                {"herb": "杏仁", "dosage": "七十个", "preparation": "去皮尖"},
                {"herb": "甘草", "dosage": "一两", "preparation": "炙"}
            ],
            "indications": ["太阳病", "头痛发热", "身疼腰痛", "恶风无汗而喘"],
            "contraindications": ["表虚自汗", "阴虚火旺"],
            "effects": ["发汗解表", "宣肺平喘"],
            "source_text": "太阳病，头痛发热，身疼腰痛，骨节疼痛，恶风无汗而喘者，麻黄汤主之。"
        },
        {
            "formula_id": "guizhi_tang",
            "formula_name": "桂枝汤",
            "source_book": "伤寒论",
            "source_section": "第12条",
            "composition": [
                {"herb": "桂枝", "dosage": "三两", "preparation": "去皮"},
                {"herb": "芍药", "dosage": "三两", "preparation": ""},
                {"herb": "甘草", "dosage": "二两", "preparation": "炙"},
                {"herb": "生姜", "dosage": "三两", "preparation": "切"},
                {"herb": "大枣", "dosage": "十二枚", "preparation": "擘"}
            ],
            "indications": ["太阳中风", "发热汗出", "恶风恶寒", "鼻鸣干呕"],
            "contraindications": ["表实无汗", "温病初起"],
            "effects": ["解肌发表", "调和营卫"],
            "source_text": "太阳中风，阳浮而阴弱，阳浮者，热自发，阴弱者，汗自出，啬啬恶寒，淅淅恶风，翕翕发热，鼻鸣干呕者，桂枝汤主之。"
        }
    ]
    
    with open(sample_dir / "formulas.json", 'w', encoding='utf-8') as f:
        json.dump(formulas, f, ensure_ascii=False, indent=2)
    
    print(f"[Sample] 创建示例数据完成，位于 {sample_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="小神农数据导入管道")
    parser.add_argument("--create-samples", action="store_true", help="创建示例数据")
    parser.add_argument("--import-all", action="store_true", help="导入所有数据")
    
    args = parser.parse_args()
    
    if args.create_samples:
        create_sample_data()
    
    if args.import_all:
        from rag_engine import XiaoShennongRAG
        
        rag = XiaoShennongRAG()
        pipeline = DataPipeline()
        
        # 先创建示例数据
        create_sample_data()
        
        # 批量导入
        pipeline.batch_import(rag, "./data/raw")
        
        print(f"\n知识库统计: {rag.get_stats()}")
