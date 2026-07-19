#!/usr/bin/env python3
"""
小神农中医AI - 账号认证服务
手机号为跨端身份锚点：Web 端手机号+密码（短信绑定），小程序端手机号授权（预留）。

- 密码：werkzeug 哈希，不落明文
- 会话：随机 token，存 sessions 表，7 天有效
- 角色：user（患者）/ clinic（医馆账号）/ admin（平台，沿用 X-Admin-Token）
"""

import re
import time
import secrets
from functools import wraps
from typing import Optional, Tuple

from flask import request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash

from db import get_conn, next_id, now_iso
from sms_service import is_valid_phone

SESSION_TTL = 7 * 24 * 3600  # 7 天

PASSWORD_MIN_LEN = 6


def mask_phone(phone: str) -> str:
    """展示层脱敏：138****5678"""
    if phone and len(phone) == 11:
        return phone[:3] + "****" + phone[7:]
    return phone or ""


def _public_user(row) -> dict:
    return {
        "user_id": row["user_id"],
        "phone": mask_phone(row["phone"]),
        "nickname": row["nickname"],
        "gender": row["gender"],
        "birth_year": row["birth_year"],
        "created_at": row["created_at"],
    }


# ============ 用户操作 ============

def register_user(phone: str, password: str, consent: bool, nickname: str = "") -> Tuple[Optional[dict], Optional[str]]:
    """注册新用户，成功返回 (user_info, None)，失败返回 (None, 错误信息)"""
    if not is_valid_phone(phone):
        return None, "手机号格式不正确"
    if not password or len(password) < PASSWORD_MIN_LEN:
        return None, f"密码至少 {PASSWORD_MIN_LEN} 位"
    if not consent:
        return None, "请先阅读并同意《用户协议与隐私政策》"

    conn = get_conn()
    try:
        if conn.execute("SELECT 1 FROM users WHERE phone=?", (phone,)).fetchone():
            return None, "该手机号已注册，请直接登录"

        user_id = next_id("U", conn)
        conn.execute(
            "INSERT INTO users (user_id, phone, nickname, consent_agreed, created_at) VALUES (?,?,?,?,?)",
            (user_id, phone, nickname or "", 1, now_iso()),
        )
        conn.execute(
            "INSERT INTO user_credentials (user_id, password_hash) VALUES (?,?)",
            (user_id, generate_password_hash(password)),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        return _public_user(row), None
    finally:
        conn.close()


def login_by_password(phone: str, password: str) -> Tuple[Optional[str], Optional[dict], Optional[str]]:
    """账密登录，成功返回 (token, user_info, None)"""
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM users WHERE phone=?", (phone,)).fetchone()
        if not row:
            return None, None, "手机号未注册"
        cred = conn.execute("SELECT password_hash FROM user_credentials WHERE user_id=?",
                            (row["user_id"],)).fetchone()
        if not cred or not check_password_hash(cred["password_hash"], password or ""):
            return None, None, "密码错误"
        token = create_session(row["user_id"], "user", conn=conn)
        conn.commit()
        return token, _public_user(row), None
    finally:
        conn.close()


def login_by_sms(phone: str) -> Tuple[Optional[str], Optional[dict], Optional[str]]:
    """验证码登录（Web 备用 / 小程序一期）：手机号已注册才允许"""
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM users WHERE phone=?", (phone,)).fetchone()
        if not row:
            return None, None, "手机号未注册，请先注册"
        token = create_session(row["user_id"], "user", conn=conn)
        conn.commit()
        return token, _public_user(row), None
    finally:
        conn.close()


def reset_password(phone: str, new_password: str) -> Tuple[bool, Optional[str]]:
    conn = get_conn()
    try:
        row = conn.execute("SELECT user_id FROM users WHERE phone=?", (phone,)).fetchone()
        if not row:
            return False, "手机号未注册"
        if not new_password or len(new_password) < PASSWORD_MIN_LEN:
            return False, f"密码至少 {PASSWORD_MIN_LEN} 位"
        conn.execute("UPDATE user_credentials SET password_hash=? WHERE user_id=?",
                     (generate_password_hash(new_password), row["user_id"]))
        # 重置后吊销旧会话
        conn.execute("DELETE FROM sessions WHERE user_id=?", (row["user_id"],))
        conn.commit()
        return True, None
    finally:
        conn.close()


def update_profile(user_id: str, fields: dict) -> Optional[dict]:
    allowed = {"nickname", "gender", "birth_year"}
    sets, vals = [], []
    for k, v in fields.items():
        if k in allowed:
            sets.append(f"{k}=?")
            vals.append(v)
    if not sets:
        return get_user(user_id)
    vals.append(user_id)
    conn = get_conn()
    try:
        conn.execute(f"UPDATE users SET {', '.join(sets)} WHERE user_id=?", vals)
        conn.commit()
    finally:
        conn.close()
    return get_user(user_id)


def get_user(user_id: str) -> Optional[dict]:
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        return _public_user(row) if row else None
    finally:
        conn.close()


# ============ 会话 ============

def create_session(user_id: str, role: str = "user", clinic_id: str = "", conn=None) -> str:
    token = secrets.token_hex(32)
    own = conn is None
    if own:
        conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO sessions (token, user_id, role, clinic_id, expires_at) VALUES (?,?,?,?,?)",
            (token, user_id, role, clinic_id, time.time() + SESSION_TTL),
        )
        if own:
            conn.commit()
    finally:
        if own:
            conn.close()
    return token


def resolve_token(token: str) -> Optional[dict]:
    """token → 会话信息（含角色），过期自动清理"""
    if not token:
        return None
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM sessions WHERE token=?", (token,)).fetchone()
        if not row:
            return None
        if row["expires_at"] < time.time():
            conn.execute("DELETE FROM sessions WHERE token=?", (token,))
            conn.commit()
            return None
        return {"user_id": row["user_id"], "role": row["role"], "clinic_id": row["clinic_id"]}
    finally:
        conn.close()


def logout(token: str) -> None:
    conn = get_conn()
    try:
        conn.execute("DELETE FROM sessions WHERE token=?", (token,))
        conn.commit()
    finally:
        conn.close()


def _extract_token() -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:].strip()
    return request.headers.get("X-User-Token", "")


def require_user(f):
    """患者身份装饰器：校验通过后将 (user_id, role) 挂到 g.current_user"""
    @wraps(f)
    def decorated(*args, **kwargs):
        sess = resolve_token(_extract_token())
        if not sess or sess["role"] != "user":
            return jsonify({"success": False, "error": "请先登录"}), 401
        g.current_user = sess
        return f(*args, **kwargs)
    return decorated


def require_clinic(f):
    """医馆身份装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        sess = resolve_token(_extract_token())
        if not sess or sess["role"] != "clinic":
            return jsonify({"success": False, "error": "请先以医馆账号登录"}), 401
        g.current_user = sess
        return f(*args, **kwargs)
    return decorated
