#!/usr/bin/env python3
"""
小神农中医AI - 电子病历（EMR）服务

两类记录：
- profile：健康档案（每人一条，注册后首次访问自动创建），存放身高体重、
  既往史、过敏史、用药史、个人史、月经婚育史等基础信息；
- visit：就诊记录（每次问诊辨证完成自动写入），含主诉、现病史、AI 结论快照。

所有记录带 EMR-日期-序号 编号，预留 hash 字段供后期取证存证。
"""

import json
from typing import Optional, Dict, List

from db import get_conn, next_id, now_iso

PROFILE_STRUCTURED_KEYS = {"height", "weight", "blood_type", "smoking", "drinking", "family_history"}
PROFILE_TEXT_KEYS = {"past_history", "allergy_history", "medication_history", "gynecology_history"}


def _row_to_dict(row) -> Dict:
    d = dict(row)
    if d.get("personal_history"):
        try:
            d["personal_history"] = json.loads(d["personal_history"])
        except Exception:
            pass
    if d.get("ai_diagnosis"):
        try:
            d["ai_diagnosis"] = json.loads(d["ai_diagnosis"])
        except Exception:
            pass
    return d


def ensure_profile(user_id: str) -> Dict:
    """获取（不存在则创建）用户的健康档案"""
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM emr WHERE user_id=? AND record_type='profile' ORDER BY created_at LIMIT 1",
            (user_id,),
        ).fetchone()
        if row:
            return _row_to_dict(row)
        emr_id = next_id("EMR", conn)
        conn.execute(
            "INSERT INTO emr (emr_id, user_id, record_type, personal_history, created_at) VALUES (?,?,?,?,?)",
            (emr_id, user_id, "profile", "{}", now_iso()),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM emr WHERE emr_id=?", (emr_id,)).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def update_profile(user_id: str, fields: Dict) -> Dict:
    """更新健康档案。结构化字段进 personal_history(JSON)，长文本字段独立列。"""
    profile = ensure_profile(user_id)
    structured = profile.get("personal_history") or {}
    if not isinstance(structured, dict):
        structured = {}

    text_updates = {}
    for k, v in fields.items():
        if k in PROFILE_STRUCTURED_KEYS:
            structured[k] = v
        elif k in PROFILE_TEXT_KEYS:
            text_updates[k] = v

    conn = get_conn()
    try:
        sets = ["personal_history=?"]
        vals = [json.dumps(structured, ensure_ascii=False)]
        for k, v in text_updates.items():
            sets.append(f"{k}=?")
            vals.append(v)
        vals.append(profile["emr_id"])
        conn.execute(f"UPDATE emr SET {', '.join(sets)} WHERE emr_id=?", vals)
        conn.commit()
    finally:
        conn.close()
    return ensure_profile(user_id)


def add_visit(user_id: str, chief_complaint: str, present_illness: str,
              ai_diagnosis=None, tongue_pulse: str = "") -> str:
    """问诊完成，写入一条就诊记录，返回 EMR 编号"""
    conn = get_conn()
    try:
        emr_id = next_id("EMR", conn)
        conn.execute(
            """INSERT INTO emr (emr_id, user_id, record_type, chief_complaint, present_illness,
                                tongue_pulse, ai_diagnosis, created_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (emr_id, user_id, "visit", chief_complaint or "", present_illness or "",
             tongue_pulse or "",
             json.dumps(ai_diagnosis, ensure_ascii=False) if ai_diagnosis else "",
             now_iso()),
        )
        conn.commit()
        return emr_id
    finally:
        conn.close()


def list_records(user_id: str, record_type: Optional[str] = None) -> List[Dict]:
    conn = get_conn()
    try:
        if record_type:
            rows = conn.execute(
                "SELECT * FROM emr WHERE user_id=? AND record_type=? ORDER BY created_at DESC",
                (user_id, record_type),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM emr WHERE user_id=? ORDER BY created_at DESC", (user_id,),
            ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def get_profile_for_dialogue(user_id: str) -> Dict:
    """供对话引擎预载：把档案转成 user_profile 扁平结构"""
    profile = ensure_profile(user_id)
    structured = profile.get("personal_history") or {}
    flat = {
        "past_history": profile.get("past_history") or "",
        "allergy_history": profile.get("allergy_history") or "",
        "medication_history": profile.get("medication_history") or "",
        "gynecology_history": profile.get("gynecology_history") or "",
    }
    if isinstance(structured, dict):
        for k in ("height", "weight", "blood_type"):
            if structured.get(k):
                flat[k] = structured[k]
    # 从 users 表补年龄性别
    conn = get_conn()
    try:
        row = conn.execute("SELECT gender, birth_year FROM users WHERE user_id=?", (user_id,)).fetchone()
        if row:
            if row["gender"]:
                flat["gender"] = row["gender"]
            if row["birth_year"]:
                from datetime import datetime
                flat["age"] = str(datetime.now().year - row["birth_year"])
    finally:
        conn.close()
    return flat
