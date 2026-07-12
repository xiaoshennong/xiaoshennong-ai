#!/usr/bin/env python3
"""
小神农中医AI - 数据导入脚本
将所有JSON数据导入Chroma向量数据库
"""

import os
import sys
import json
import glob

# 添加backend到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from rag_engine import XiaoShennongRAG

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
RAW_DIR = os.path.join(DATA_DIR, 'raw')

def import_all_data():
    """导入所有数据到向量数据库"""
    print("=" * 60)
    print("小神农中医AI - 数据导入工具")
    print("=" * 60)
    
    db_path = os.path.join(DATA_DIR, 'chroma_db_v2')
    
    # 如果旧数据库存在，删除它（如果未被占用）
    old_db_path = os.path.join(DATA_DIR, 'chroma_db')
    if os.path.exists(old_db_path):
        try:
            import shutil
            shutil.rmtree(old_db_path)
            print(f"[INFO] 已删除旧数据库: {old_db_path}")
        except Exception as e:
            print(f"[INFO] 旧数据库无法删除（可能被占用）: {e}")
            print(f"[INFO] 将使用新数据库路径: {db_path}")
    
    # 初始化RAG引擎（会创建新数据库）
    rag = XiaoShennongRAG(db_path=db_path)
    
    print(f"[INFO] 使用数据库路径: {db_path}")
    
    # 收集所有数据文件
    data_files = []
    
    # 1. 爬取的数据文件
    crawled_files = [
        'all_crawled_data.json',
        'crawled_herbs.json', 
        'crawled_formulas.json',
        'crawled_acupuncture.json',
        'crawled_mappings.json',
        'crawled_therapies.json'
    ]
    
    for fname in crawled_files:
        fpath = os.path.join(RAW_DIR, fname)
        if os.path.exists(fpath):
            data_files.append(fpath)
    
    # 2. 经典古籍文件
    classic_files = glob.glob(os.path.join(RAW_DIR, '*.json'))
    for fpath in classic_files:
        if fpath not in data_files and os.path.basename(fpath) not in crawled_files:
            data_files.append(fpath)
    
    print(f"[INFO] 找到 {len(data_files)} 个数据文件")
    
    total_imported = 0
    total_records = 0
    
    for fpath in data_files:
        fname = os.path.basename(fpath)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 处理不同格式
            documents = []
            
            # 格式1: 经典古籍格式 {"book_name": "...", "sections": [...]}
            if isinstance(data, dict) and 'book_name' in data and 'sections' in data:
                book_name = data['book_name']
                dynasty = data.get('dynasty', '')
                author = data.get('author', '')
                for section in data['sections']:
                    section_name = section.get('section_name', '')
                    original_text = section.get('original_text', '')
                    if original_text:
                        # 构建text：原文 + 出处
                        text = f"《{book_name}》·{section_name}\n{original_text}"
                        documents.append({
                            'text': text,
                            'metadata': {
                                'source_book': f'《{book_name}》',
                                'source_section': section_name,
                                'original_text': original_text,
                                'dynasty': dynasty,
                                'author': author,
                                'chunk_id': f"classic_{book_name}_{section_name}",
                                'type': 'classic'
                            }
                        })
            
            # 格式2: 标准列表格式 [{"text": "...", "metadata": {...}}]
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and 'text' in item and 'metadata' in item:
                        documents.append(item)
                    elif isinstance(item, dict):
                        # 尝试转换
                        text = item.get('text', '')
                        if not text:
                            # 从其他字段构建text
                            text_parts = []
                            for k, v in item.items():
                                if k != 'metadata' and v and isinstance(v, str):
                                    text_parts.append(f"{k}: {v}")
                            text = '\n'.join(text_parts)
                        
                        metadata = item.get('metadata', {})
                        if not metadata:
                            metadata = {k: str(v) for k, v in item.items() if k != 'text'}
                        
                        if text:
                            documents.append({
                                'text': text,
                                'metadata': metadata
                            })
            
            elif isinstance(data, dict):
                # 字典格式
                for key, value in data.items():
                    if isinstance(value, dict):
                        text = value.get('text', '')
                        metadata = value.get('metadata', {})
                        if text:
                            documents.append({'text': text, 'metadata': metadata})
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict) and 'text' in item:
                                documents.append(item)
            
            if documents:
                # 批量导入，每批100条
                batch_size = 100
                for i in range(0, len(documents), batch_size):
                    batch = documents[i:i+batch_size]
                    rag.add_documents(batch)
                
                total_imported += len(documents)
                print(f"[OK] {fname}: 导入 {len(documents)} 条文档")
            else:
                print(f"[WARN] {fname}: 无有效文档")
                
        except Exception as e:
            print(f"[ERROR] {fname}: {e}")
    
    # 验证
    final_count = rag._get_collection().count()
    print(f"\n{'=' * 60}")
    print(f"导入完成！")
    print(f"尝试导入: {total_imported} 条")
    print(f"实际存储: {final_count} 条")
    print(f"{'=' * 60}")
    
    return final_count

if __name__ == '__main__':
    count = import_all_data()
    print(f"\n知识库当前共有 {count} 条文档")
