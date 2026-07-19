#!/usr/bin/env python3
"""
小神农中医AI - 古籍条文导入 SQLite
将 data/raw/classical_texts*.json 导入 xiaoshennong.db 的 classical_texts 表
（无嵌入检索主路的数据源；与 Chroma 并存，INSERT OR IGNORE 幂等可重跑）

用法: python scripts/import_classical_to_sqlite.py
"""

import os
import sys
import json
import glob
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")

sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
sys.dont_write_bytecode = True

from db import get_conn, init_db  # noqa: E402


def main():
    init_db()
    files = sorted(glob.glob(os.path.join(RAW_DIR, "classical_texts*.json")))
    if not files:
        print("[导入] 未找到 classical_texts 文件")
        return

    conn = get_conn()
    total, inserted = 0, 0
    t0 = time.time()
    try:
        for idx, filepath in enumerate(files, 1):
            with open(filepath, "r", encoding="utf-8") as f:
                entries = json.load(f)
            rows = []
            for e in entries:
                text = (e.get("text") or "").strip()
                if not text:
                    continue
                kw = e.get("keywords") or []
                rows.append((
                    e.get("text_id") or "",
                    e.get("book", ""),
                    e.get("section", ""),
                    text,
                    e.get("symptom", ""),
                    "、".join(kw) if isinstance(kw, list) else str(kw),
                ))
            cur = conn.executemany(
                "INSERT OR IGNORE INTO classical_texts (text_id, book, section, text, symptom, keywords) "
                "VALUES (?,?,?,?,?,?)",
                rows,
            )
            conn.commit()
            total += len(rows)
            inserted += cur.rowcount
            if idx % 20 == 0 or idx == len(files):
                print(f"[导入] ({idx}/{len(files)}) 累计读取 {total}, 新增 {inserted}, "
                      f"耗时 {time.time() - t0:.1f}s")
        count = conn.execute("SELECT COUNT(*) AS c FROM classical_texts").fetchone()["c"]
        print(f"[导入] 完成: 表内共 {count} 条")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
