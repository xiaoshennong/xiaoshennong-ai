#!/usr/bin/env python3
"""
小神农中医AI - SQLite 持久化层
单文件数据库 data/xiaoshennong.db，承载：
- classical_texts  古籍条文（无嵌入检索主路的数据源）
- id_counters      全实体编号发号器（日期+序号，便于排序与取证）
- users / sessions / sms_codes  账号认证（手机号锚点）
- emr              电子病历
- clinics / clinic_accounts / clinic_verifications  医馆体系
- prescriptions / orders / order_events  处方与订单（含留痕）
- query_cache      检索 LLM 改写缓存

所有表通过 init_db() 幂等创建。
"""

import os
import sqlite3
import threading
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "xiaoshennong.db")

_init_lock = threading.Lock()
_initialized = False

SCHEMA = """
CREATE TABLE IF NOT EXISTS classical_texts (
    text_id  TEXT PRIMARY KEY,
    book     TEXT,
    section  TEXT,
    text     TEXT,
    symptom  TEXT,
    keywords TEXT
);
CREATE INDEX IF NOT EXISTS idx_ct_symptom ON classical_texts(symptom);

CREATE TABLE IF NOT EXISTS id_counters (
    prefix TEXT NOT NULL,
    date   TEXT NOT NULL,
    seq    INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (prefix, date)
);

CREATE TABLE IF NOT EXISTS users (
    user_id        TEXT PRIMARY KEY,
    phone          TEXT UNIQUE NOT NULL,
    nickname       TEXT DEFAULT '',
    gender         TEXT DEFAULT '',
    birth_year     INTEGER,
    consent_agreed INTEGER DEFAULT 0,
    openid         TEXT DEFAULT '',
    created_at     TEXT,
    hash           TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS user_credentials (
    user_id       TEXT PRIMARY KEY REFERENCES users(user_id),
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    token      TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL,
    role       TEXT NOT NULL DEFAULT 'user',
    clinic_id  TEXT DEFAULT '',
    expires_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);

CREATE TABLE IF NOT EXISTS sms_codes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    phone      TEXT NOT NULL,
    code       TEXT NOT NULL,
    purpose    TEXT NOT NULL,
    expires_at REAL NOT NULL,
    used       INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_sms_phone ON sms_codes(phone, purpose);

CREATE TABLE IF NOT EXISTS emr (
    emr_id              TEXT PRIMARY KEY,
    user_id             TEXT NOT NULL REFERENCES users(user_id),
    record_type         TEXT NOT NULL DEFAULT 'visit',
    chief_complaint     TEXT DEFAULT '',
    present_illness     TEXT DEFAULT '',
    past_history        TEXT DEFAULT '',
    allergy_history     TEXT DEFAULT '',
    medication_history  TEXT DEFAULT '',
    personal_history    TEXT DEFAULT '',
    gynecology_history  TEXT DEFAULT '',
    tongue_pulse        TEXT DEFAULT '',
    ai_diagnosis        TEXT DEFAULT '',
    created_at          TEXT,
    hash                TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_emr_user ON emr(user_id);

CREATE TABLE IF NOT EXISTS clinics (
    clinic_id         TEXT PRIMARY KEY,
    name              TEXT NOT NULL,
    license_no        TEXT DEFAULT '',
    address           TEXT DEFAULT '',
    phone             TEXT DEFAULT '',
    support_decoction INTEGER DEFAULT 0,
    decoction_fee     INTEGER DEFAULT 0,
    delivery_scope    TEXT DEFAULT '',
    status            TEXT NOT NULL DEFAULT 'pending',
    created_at        TEXT,
    hash              TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS clinic_accounts (
    account_id    TEXT PRIMARY KEY,
    clinic_id     TEXT NOT NULL REFERENCES clinics(clinic_id),
    phone         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name          TEXT DEFAULT '',
    title         TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS clinic_verifications (
    cv_id      TEXT PRIMARY KEY,
    clinic_id  TEXT NOT NULL REFERENCES clinics(clinic_id),
    reviewer   TEXT DEFAULT '',
    action     TEXT NOT NULL,
    note       TEXT DEFAULT '',
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS prescriptions (
    rx_id            TEXT PRIMARY KEY,
    user_id          TEXT NOT NULL REFERENCES users(user_id),
    clinic_id        TEXT NOT NULL REFERENCES clinics(clinic_id),
    session_id       TEXT DEFAULT '',
    emr_snapshot     TEXT DEFAULT '',
    ai_advice        TEXT DEFAULT '',
    status           TEXT NOT NULL DEFAULT 'pending_review',
    reviewed_by      TEXT DEFAULT '',
    review_note      TEXT DEFAULT '',
    adjusted_formula TEXT DEFAULT '',
    created_at       TEXT,
    reviewed_at      TEXT,
    hash             TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_rx_clinic ON prescriptions(clinic_id, status);
CREATE INDEX IF NOT EXISTS idx_rx_user ON prescriptions(user_id);

CREATE TABLE IF NOT EXISTS orders (
    order_id    TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL REFERENCES users(user_id),
    clinic_id   TEXT DEFAULT '',
    rx_id       TEXT DEFAULT '',
    order_type  TEXT NOT NULL DEFAULT 'mall',
    items       TEXT DEFAULT '',
    fulfillment TEXT DEFAULT '',
    decoction   INTEGER DEFAULT 0,
    address     TEXT DEFAULT '',
    amount      INTEGER DEFAULT 0,
    status      TEXT NOT NULL DEFAULT 'created',
    pay_status  TEXT NOT NULL DEFAULT 'unpaid',
    created_at  TEXT,
    hash        TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_clinic ON orders(clinic_id, status);

CREATE TABLE IF NOT EXISTS order_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id    TEXT NOT NULL REFERENCES orders(order_id),
    from_status TEXT DEFAULT '',
    to_status   TEXT NOT NULL,
    operator    TEXT DEFAULT '',
    note        TEXT DEFAULT '',
    created_at  TEXT
);
CREATE INDEX IF NOT EXISTS idx_oe_order ON order_events(order_id);

CREATE TABLE IF NOT EXISTS query_cache (
    query      TEXT PRIMARY KEY,
    rewritten  TEXT NOT NULL,
    created_at TEXT
);
"""


def get_conn() -> sqlite3.Connection:
    """每请求新建连接（线程安全），WAL 模式支持多读单写"""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """幂等建表（进程内只执行一次）"""
    global _initialized
    with _init_lock:
        if _initialized:
            return
        conn = get_conn()
        try:
            conn.executescript(SCHEMA)
            conn.commit()
        finally:
            conn.close()
        _initialized = True


def next_id(prefix: str, conn: sqlite3.Connection = None) -> str:
    """
    发放实体编号：{prefix}-{YYYYMMDD}-{四位序号}
    事务内自增，保证并发唯一。调用方传 conn 则随其事务提交，否则自管连接。
    """
    today = datetime.now().strftime("%Y%m%d")
    own = conn is None
    if own:
        conn = get_conn()
    try:
        row = conn.execute(
            """
            INSERT INTO id_counters (prefix, date, seq) VALUES (?, ?, 1)
            ON CONFLICT(prefix, date) DO UPDATE SET seq = seq + 1
            RETURNING seq
            """,
            (prefix, today),
        ).fetchone()
        if own:
            conn.commit()
        return f"{prefix}-{today}-{row['seq']:04d}"
    finally:
        if own:
            conn.close()


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


# 模块导入即建表，成本可忽略
init_db()
