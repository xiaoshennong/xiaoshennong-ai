#!/usr/bin/env python3
"""
小神农中医AI - 短信验证码服务（可插拔）

- 未配置短信服务商密钥时为开发模式：验证码打印到后端日志，并在接口响应中
  以 dev_code 字段返回（仅供本地开发，配置正式密钥后自动关闭）。
- 预留阿里云短信实现位（SMS_PROVIDER=aliyun 时走 HTTP API，暂不引入 SDK）。

.env 配置项：
    SMS_PROVIDER          空=开发模式 / aliyun
    SMS_ALIYUN_ACCESS_KEY / SMS_ALIYUN_SECRET / SMS_ALIYUN_SIGN / SMS_ALIYUN_TEMPLATE
"""

import os
import re
import time
import random

from db import get_conn

CODE_TTL_SECONDS = 600       # 验证码 10 分钟有效
RESEND_INTERVAL = 60         # 60 秒内不允许重发
MAX_VERIFY_TRIES = 5         # 单码最多试错次数

PHONE_RE = re.compile(r"^1[3-9]\d{9}$")


def is_valid_phone(phone: str) -> bool:
    return bool(PHONE_RE.match(phone or ""))


def is_dev_mode() -> bool:
    return not os.getenv("SMS_PROVIDER")


def send_code(phone: str, purpose: str) -> dict:
    """
    发送验证码。返回 {"success": bool, "dev_code": str|None, "error": str|None}
    purpose: register / login / reset
    """
    if not is_valid_phone(phone):
        return {"success": False, "dev_code": None, "error": "手机号格式不正确"}

    conn = get_conn()
    try:
        # 60 秒重发限制
        row = conn.execute(
            "SELECT id, expires_at FROM sms_codes WHERE phone=? AND purpose=? ORDER BY id DESC LIMIT 1",
            (phone, purpose),
        ).fetchone()
        if row and row["expires_at"] - CODE_TTL_SECONDS + RESEND_INTERVAL > time.time():
            return {"success": False, "dev_code": None, "error": "验证码已发送，请 60 秒后再试"}

        code = f"{random.randint(0, 999999):06d}"
        conn.execute(
            "INSERT INTO sms_codes (phone, code, purpose, expires_at, used) VALUES (?,?,?,?,0)",
            (phone, code, purpose, time.time() + CODE_TTL_SECONDS),
        )
        conn.commit()
    finally:
        conn.close()

    if is_dev_mode():
        print(f"[SMS·开发模式] 向 {phone} 发送 {purpose} 验证码: {code}")
        return {"success": True, "dev_code": code, "error": None}

    # TODO: 阿里云短信通道（SMS_PROVIDER=aliyun），上线前按签名/模板报备后实现
    print(f"[SMS] 服务商 {os.getenv('SMS_PROVIDER')} 尚未实现，验证码未发出")
    return {"success": False, "dev_code": None, "error": "短信服务未配置，请联系管理员"}


def verify_code(phone: str, code: str, purpose: str) -> bool:
    """校验验证码（一次性，过期/错误次数过多即失效）"""
    if not phone or not code:
        return False
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT id, code, expires_at, used FROM sms_codes "
            "WHERE phone=? AND purpose=? ORDER BY id DESC LIMIT 1",
            (phone, purpose),
        ).fetchone()
        if not row or row["used"] >= MAX_VERIFY_TRIES:
            return False
        if row["expires_at"] < time.time():
            return False
        if row["code"] != code:
            conn.execute("UPDATE sms_codes SET used = used + 1 WHERE id=?", (row["id"],))
            conn.commit()
            return False
        conn.execute(f"UPDATE sms_codes SET used = {MAX_VERIFY_TRIES} WHERE id=?", (row["id"],))
        conn.commit()
        return True
    finally:
        conn.close()
