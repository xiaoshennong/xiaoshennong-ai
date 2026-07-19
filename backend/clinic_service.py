#!/usr/bin/env python3
"""
小神农中医AI - 医馆服务
入驻申请（限权开通）→ 平台资质核验 → 药方审核 → 处方订单履约留痕。

合规设计：AI 只出"建议"，入驻医馆的执业医师审核通过才生成正式处方；
医馆未通过资质核验（status != verified）时，审核/接单权限锁定。
"""

import json
from typing import Optional, Dict, List, Tuple

from werkzeug.security import generate_password_hash, check_password_hash

from db import get_conn, next_id, now_iso
from sms_service import is_valid_phone

# 订单状态机（处方线）
ORDER_STATUS = ["created", "accepted", "preparing", "decocting", "shipped", "awaiting_pickup", "completed", "cancelled"]
STATUS_LABELS = {
    "created": "待接单", "accepted": "已接单", "preparing": "配药中",
    "decocting": "代煎中", "shipped": "已发货", "awaiting_pickup": "待取货",
    "completed": "已完成", "cancelled": "已取消",
}


# ============ 入驻与登录 ============

def apply_clinic(name: str, license_no: str, address: str, phone: str,
                 account_phone: str, password: str, contact_name: str = "",
                 support_decoction: bool = False, decoction_fee: int = 0,
                 delivery_scope: str = "") -> Tuple[Optional[dict], Optional[str]]:
    """医馆入驻申请：立即开通账号（status=pending），审核/接单权限待核验后解锁"""
    if not name or len(name) < 2:
        return None, "请填写医馆名称"
    if not license_no:
        return None, "请填写医疗机构执业许可证号"
    if not is_valid_phone(account_phone):
        return None, "登录手机号格式不正确"
    if not password or len(password) < 6:
        return None, "密码至少 6 位"

    conn = get_conn()
    try:
        if conn.execute("SELECT 1 FROM clinic_accounts WHERE phone=?", (account_phone,)).fetchone():
            return None, "该手机号已注册医馆账号，请直接登录"
        clinic_id = next_id("MC", conn)
        account_id = next_id("CA", conn)
        conn.execute(
            """INSERT INTO clinics (clinic_id, name, license_no, address, phone,
                                    support_decoction, decoction_fee, delivery_scope, status, created_at)
               VALUES (?,?,?,?,?,?,?,?, 'pending', ?)""",
            (clinic_id, name, license_no, address or "", phone or account_phone,
             1 if support_decoction else 0, decoction_fee or 0, delivery_scope or "", now_iso()),
        )
        conn.execute(
            "INSERT INTO clinic_accounts (account_id, clinic_id, phone, password_hash, name, title) VALUES (?,?,?,?,?,?)",
            (account_id, clinic_id, account_phone, generate_password_hash(password), contact_name or "", "医师"),
        )
        conn.commit()
        return {"clinic_id": clinic_id, "account_id": account_id, "status": "pending"}, None
    finally:
        conn.close()


def login_clinic(phone: str, password: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """医馆账号登录，返回 (clinic_id, account_name, error)"""
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM clinic_accounts WHERE phone=?", (phone,)).fetchone()
        if not row or not check_password_hash(row["password_hash"], password or ""):
            return None, None, "手机号或密码错误"
        return row["clinic_id"], row["name"], None
    finally:
        conn.close()


def get_clinic(clinic_id: str) -> Optional[dict]:
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM clinics WHERE clinic_id=?", (clinic_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def list_verified_clinics() -> List[dict]:
    """给用户挑选的医馆列表（仅已核验）"""
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT clinic_id, name, address, support_decoction, decoction_fee, delivery_scope "
            "FROM clinics WHERE status='verified' ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def verify_clinic(clinic_id: str, action: str, reviewer: str, note: str = "") -> Tuple[bool, Optional[str]]:
    """平台核验：verified 解锁权限 / frozen 冻结"""
    if action not in ("verified", "frozen"):
        return False, "不支持的核验动作"
    conn = get_conn()
    try:
        if not conn.execute("SELECT 1 FROM clinics WHERE clinic_id=?", (clinic_id,)).fetchone():
            return False, "医馆不存在"
        conn.execute("UPDATE clinics SET status=? WHERE clinic_id=?", (action, clinic_id))
        cv_id = next_id("CV", conn)
        conn.execute(
            "INSERT INTO clinic_verifications (cv_id, clinic_id, reviewer, action, note, created_at) VALUES (?,?,?,?,?,?)",
            (cv_id, clinic_id, reviewer or "admin", action, note or "", now_iso()),
        )
        conn.commit()
        return True, None
    finally:
        conn.close()


def list_all_clinics() -> List[dict]:
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM clinics ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _clinic_verified(conn, clinic_id: str) -> bool:
    row = conn.execute("SELECT status FROM clinics WHERE clinic_id=?", (clinic_id,)).fetchone()
    return bool(row and row["status"] == "verified")


# ============ 药方审核 ============

def apply_prescription(user_id: str, clinic_id: str, session_id: str,
                       emr_snapshot: dict, ai_advice: str) -> Tuple[Optional[str], Optional[str]]:
    """用户从问诊会话发起开方申请 → RX 编号，推入医馆审核队列"""
    conn = get_conn()
    try:
        if not _clinic_verified(conn, clinic_id):
            return None, "该医馆暂未开通审核服务，请更换医馆"
        rx_id = next_id("RX", conn)
        conn.execute(
            """INSERT INTO prescriptions (rx_id, user_id, clinic_id, session_id, emr_snapshot,
                                          ai_advice, status, created_at)
               VALUES (?,?,?,?,?,?, 'pending_review', ?)""",
            (rx_id, user_id, clinic_id, session_id or "",
             json.dumps(emr_snapshot or {}, ensure_ascii=False), ai_advice or "", now_iso()),
        )
        conn.commit()
        return rx_id, None
    finally:
        conn.close()


def rx_queue(clinic_id: str, status: str = "pending_review") -> List[dict]:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM prescriptions WHERE clinic_id=? AND status=? ORDER BY created_at",
            (clinic_id, status),
        ).fetchall()
        return [_rx_to_dict(r) for r in rows]
    finally:
        conn.close()


def _rx_to_dict(row) -> dict:
    d = dict(row)
    for k in ("emr_snapshot", "adjusted_formula"):
        if d.get(k):
            try:
                d[k] = json.loads(d[k])
            except Exception:
                pass
    return d


def review_prescription(clinic_id: str, rx_id: str, action: str, reviewer: str,
                        note: str = "", adjusted_formula=None) -> Tuple[bool, Optional[str]]:
    """医师审核：approve（可带加减方）/ reject（填理由）。未核验医馆 403。"""
    if action not in ("approve", "reject"):
        return False, "不支持的审核动作"
    if action == "reject" and not note:
        return False, "驳回时请填写理由"
    conn = get_conn()
    try:
        if not _clinic_verified(conn, clinic_id):
            return False, "资质审核中，暂未开通审核权限"
        row = conn.execute("SELECT status FROM prescriptions WHERE rx_id=? AND clinic_id=?",
                           (rx_id, clinic_id)).fetchone()
        if not row:
            return False, "处方不存在"
        if row["status"] != "pending_review":
            return False, "该处方已审核，请勿重复操作"
        new_status = "approved" if action == "approve" else "rejected"
        conn.execute(
            """UPDATE prescriptions SET status=?, reviewed_by=?, review_note=?,
                                       adjusted_formula=?, reviewed_at=? WHERE rx_id=?""",
            (new_status, reviewer or "", note or "",
             json.dumps(adjusted_formula, ensure_ascii=False) if adjusted_formula else "",
             now_iso(), rx_id),
        )
        conn.commit()
        return True, None
    finally:
        conn.close()


def get_user_rx(user_id: str) -> List[dict]:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM prescriptions WHERE user_id=? ORDER BY created_at DESC", (user_id,),
        ).fetchall()
        return [_rx_to_dict(r) for r in rows]
    finally:
        conn.close()


def get_rx(rx_id: str) -> Optional[dict]:
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM prescriptions WHERE rx_id=?", (rx_id,)).fetchone()
        return _rx_to_dict(row) if row else None
    finally:
        conn.close()


# ============ 订单 ============

def create_order(user_id: str, order_type: str, items, clinic_id: str = "",
                 rx_id: str = "", fulfillment: str = "", decoction: bool = False,
                 address: str = "", amount: int = 0) -> Tuple[Optional[str], Optional[str]]:
    """创建订单（处方线需 RX 已审核通过；商城线直接创建）"""
    conn = get_conn()
    try:
        if order_type == "prescription":
            rx = conn.execute("SELECT * FROM prescriptions WHERE rx_id=?", (rx_id,)).fetchone()
            if not rx or rx["user_id"] != user_id:
                return None, "处方不存在"
            if rx["status"] != "approved":
                return None, "处方尚未审核通过，暂不能下单"
            clinic_id = rx["clinic_id"]
            if fulfillment not in ("delivery", "pickup"):
                return None, "请选择邮寄或自取"
            if decoction:
                clinic = conn.execute("SELECT support_decoction FROM clinics WHERE clinic_id=?",
                                      (clinic_id,)).fetchone()
                if not clinic or not clinic["support_decoction"]:
                    return None, "该医馆暂不支持代煎服务"
        order_id = next_id("ORD", conn)
        conn.execute(
            """INSERT INTO orders (order_id, user_id, clinic_id, rx_id, order_type, items,
                                   fulfillment, decoction, address, amount, status, pay_status, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?, 'created', 'unpaid', ?)""",
            (order_id, user_id, clinic_id, rx_id, order_type,
             json.dumps(items or [], ensure_ascii=False), fulfillment or "",
             1 if decoction else 0, address or "", amount or 0, now_iso()),
        )
        _add_event(conn, order_id, "", "created", f"user:{user_id}", "订单创建")
        conn.commit()
        return order_id, None
    finally:
        conn.close()


def _add_event(conn, order_id: str, from_status: str, to_status: str, operator: str, note: str = ""):
    conn.execute(
        "INSERT INTO order_events (order_id, from_status, to_status, operator, note, created_at) VALUES (?,?,?,?,?,?)",
        (order_id, from_status, to_status, operator or "", note or "", now_iso()),
    )


def update_order_status(clinic_id: str, order_id: str, to_status: str,
                        operator: str, note: str = "") -> Tuple[bool, Optional[str]]:
    """医馆侧订单流转，全部留痕"""
    if to_status not in ORDER_STATUS:
        return False, "非法状态"
    conn = get_conn()
    try:
        if not _clinic_verified(conn, clinic_id):
            return False, "资质审核中，暂未开通接单权限"
        row = conn.execute("SELECT status FROM orders WHERE order_id=? AND clinic_id=?",
                           (order_id, clinic_id)).fetchone()
        if not row:
            return False, "订单不存在"
        _add_event(conn, order_id, row["status"], to_status, operator, note)
        conn.execute("UPDATE orders SET status=? WHERE order_id=?", (to_status, order_id))
        conn.commit()
        return True, None
    finally:
        conn.close()


def list_orders(user_id: str = "", clinic_id: str = "") -> List[dict]:
    conn = get_conn()
    try:
        if user_id:
            rows = conn.execute("SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC", (user_id,)).fetchall()
        elif clinic_id:
            rows = conn.execute("SELECT * FROM orders WHERE clinic_id=? ORDER BY created_at DESC", (clinic_id,)).fetchall()
        else:
            rows = []
        result = []
        for r in rows:
            d = dict(r)
            if d.get("items"):
                try:
                    d["items"] = json.loads(d["items"])
                except Exception:
                    pass
            d["status_label"] = STATUS_LABELS.get(d["status"], d["status"])
            result.append(d)
        return result
    finally:
        conn.close()


def order_events(order_id: str) -> List[dict]:
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM order_events WHERE order_id=? ORDER BY id", (order_id,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def clinic_dashboard(clinic_id: str) -> dict:
    conn = get_conn()
    try:
        pending_rx = conn.execute(
            "SELECT COUNT(*) c FROM prescriptions WHERE clinic_id=? AND status='pending_review'", (clinic_id,)).fetchone()["c"]
        active_orders = conn.execute(
            "SELECT COUNT(*) c FROM orders WHERE clinic_id=? AND status NOT IN ('completed','cancelled')", (clinic_id,)).fetchone()["c"]
        total_rx = conn.execute(
            "SELECT COUNT(*) c FROM prescriptions WHERE clinic_id=?", (clinic_id,)).fetchone()["c"]
        total_orders = conn.execute(
            "SELECT COUNT(*) c FROM orders WHERE clinic_id=?", (clinic_id,)).fetchone()["c"]
        clinic = conn.execute("SELECT name, status FROM clinics WHERE clinic_id=?", (clinic_id,)).fetchone()
        return {
            "clinic_name": clinic["name"] if clinic else "",
            "clinic_status": clinic["status"] if clinic else "",
            "pending_rx": pending_rx,
            "active_orders": active_orders,
            "total_rx": total_rx,
            "total_orders": total_orders,
        }
    finally:
        conn.close()
