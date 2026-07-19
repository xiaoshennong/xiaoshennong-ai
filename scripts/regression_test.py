#!/usr/bin/env python3
"""
小神农中医AI - 关键 API 一键回归测试
覆盖：健康检查、词法检索评测、账号认证、电子病历、问诊流程、
      医馆入驻/审核/订单全链路、商城订单。

用法: python scripts/regression_test.py          # 全量（含 1-2 次 LLM 辨证，约 1-2 分钟）
      python scripts/regression_test.py --quick  # 跳过 LLM 辨证链路
"""
import json
import random
import sys
import time
import urllib.request
import urllib.error

BASE = "http://localhost:5001"
ADMIN = {"X-Admin-Token": "xiaoshennong-admin"}
QUICK = "--quick" in sys.argv

passed, failed = [], []


def call(path, payload=None, token=None, headers=None, method=None, timeout=180):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data,
                                 method=method or ("POST" if payload is not None else "GET"))
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        return json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"http": e.code, **json.loads(e.read().decode("utf-8"))}


def check(name, ok, detail=""):
    (passed if ok else failed).append(name)
    print(f"  [{'PASS' if ok else 'FAIL'}] {name} {detail}")


def sms_code(phone, purpose):
    r = call("/api/auth/sms_code", {"phone": phone, "purpose": purpose})
    return r.get("data", {}).get("dev_code")


print("== 1. 健康检查与词法检索 ==")
r = call("/api/health")
docs = r.get("rag_stats", {}).get("total_documents", 0)
check("GET /api/health", r.get("status") == "ok", f"chroma_docs={docs}")

r = call("/api/retrieve", {"query": "咳嗽", "top_k": 5})["data"]
rel = sum(1 for x in r["results"] if "咳" in x["text"])
check("词法检索 engine=lexical", r.get("engine") == "lexical")
check("咳嗽相关度 >= 3/5", rel >= 3, f"{rel}/5")
q1 = set(x["text"] for x in r["results"])
q2 = set(x["text"] for x in call("/api/retrieve", {"query": "腰痛", "top_k": 5})["data"]["results"])
check("咳嗽/腰痛结果不重叠", not (q1 & q2))
r = call("/api/semantic/search", {"query": "头痛", "top_k": 5})["data"]
check("semantic/search 分组接口", r.get("total", 0) > 0 and r.get("engine") == "lexical")

print("== 2. 账号认证 ==")
phone = f"139{random.randint(10000000, 99999999)}"
code = sms_code(phone, "register")
check("sms_code 开发模式下发", bool(code))
r = call("/api/auth/register", {"phone": phone, "password": "test123456", "code": code, "consent": True})
uid = r.get("data", {}).get("user", {}).get("user_id")
check("注册并发 U 编号", bool(uid and uid.startswith("U-")), str(uid))
r = call("/api/auth/register", {"phone": phone, "password": "test123456", "code": code, "consent": True})
check("重复手机号拒绝", r.get("http") == 400)
r = call("/api/auth/login", {"phone": phone, "password": "wrong"})
check("错误密码拒绝", r.get("http") == 401)
token = call("/api/auth/login", {"phone": phone, "password": "test123456"}).get("data", {}).get("token")
check("账密登录", bool(token))
r = call("/api/auth/me", token=token)
check("me 脱敏手机号", "****" in r.get("data", {}).get("user", {}).get("phone", ""))
check("无 token 401", call("/api/auth/me").get("http") == 401)

print("== 3. 电子病历 ==")
r = call("/api/user/emr/profile", {"past_history": "高血压", "allergy_history": "无",
                                   "medication_history": "无", "height": 172}, token=token, method="PUT")
p = r.get("data", {}).get("profile", {})
check("健康档案写入", p.get("past_history") == "高血压" and p.get("personal_history", {}).get("height") == 172)
r = call("/api/user/emr", token=token)
check("病历列表", r.get("data", {}).get("total", 0) >= 1)

print("== 4. 问诊流程（真医生式） ==")
sid = call("/api/dialogue/start", {})["data"]["session_id"]
r = call("/api/dialogue/turn", {"session_id": sid, "user_input": "胃不舒服，没胃口"})["data"]
check("匿名首轮问年龄性别(PROFILE)", r["phase"] == "profile", r["phase"])
r = call("/api/dialogue/turn", {"session_id": sid, "user_input": "35岁，男"})["data"]
check("资料捕获后离开 PROFILE", r["phase"] != "profile", r["phase"])
if not QUICK:
    r = call("/api/dialogue/turn", {"session_id": sid, "user_input": "还有腹胀，直接辨证"})["data"]
    check("快速通道触发辨证", r.get("is_ready_for_diagnosis") is True and r.get("diagnosis_result") is not None)

sid2 = call("/api/dialogue/start", {}, token=token)["data"]["session_id"]
r = call("/api/dialogue/start", {}, token=token)["data"]
check("登录会话绑定 user_id", r.get("user_id") == uid)
if not QUICK:
    sid3 = r["session_id"]
    r = call("/api/dialogue/turn", {"session_id": sid3, "user_input": "咳嗽痰多，直接辨证"}, token=token)["data"]
    emr_id = r.get("visit_emr_id")
    check("病历写回 EMR 编号", bool(emr_id and emr_id.startswith("EMR-")), str(emr_id))

print("== 5. 医馆入驻 / 审核 / 订单 ==")
cphone = f"137{random.randint(10000000, 99999999)}"
r = call("/api/clinic/apply", {"name": "回春堂中医馆", "license_no": "PDY" + str(random.randint(10000, 99999)),
                               "address": "北京市西城区", "account_phone": cphone, "password": "clinic123",
                               "contact_name": "李医师", "support_decoction": True, "decoction_fee": 1000})
cid = r.get("data", {}).get("clinic_id")
check("入驻申请开通(pending)", bool(cid and cid.startswith("MC-")), str(cid))
ctoken = call("/api/clinic/login", {"phone": cphone, "password": "clinic123"}).get("data", {}).get("token")
check("医馆登录", bool(ctoken))
r = call("/api/clinic/rx/RX-0000-0000/review", {"action": "approve"}, token=ctoken)
check("pending 医馆审核被锁", r.get("http") in (400, 403), r.get("error", ""))
r = call("/api/admin/clinics/" + cid + "/verify", {"action": "verified", "note": "回归测试"}, headers=ADMIN)
check("平台核验解锁", r.get("success"))
check("verified 医馆可见", any(c["clinic_id"] == cid for c in call("/api/clinic/list")["data"]["clinics"]))

if not QUICK:
    sid4 = call("/api/dialogue/start", {}, token=token)["data"]["session_id"]
    call("/api/dialogue/turn", {"session_id": sid4, "user_input": "腰痛，直接辨证"}, token=token)
    r = call("/api/rx/apply", {"session_id": sid4, "clinic_id": cid}, token=token)
    rx = r.get("data", {}).get("rx_id")
    check("开方申请 RX 编号", bool(rx and rx.startswith("RX-")), str(rx))
    # 快速辨证来源也可申请
    r = call("/api/rx/apply", {"clinic_id": cid, "symptoms": "头痛发热", "advice": "建议：风寒感冒，可用桂枝汤"}, token=token)
    rxq = r.get("data", {}).get("rx_id")
    check("快速辨证来源申请", bool(rxq), str(rxq))
    r = call("/api/clinic/rx/" + rx + "/review", {"action": "approve", "note": "同意"}, token=ctoken)
    check("医师审核通过", r.get("success"))
    r = call("/api/orders", {"order_type": "prescription", "rx_id": rx,
                             "fulfillment": "delivery", "decoction": True, "address": "北京市"}, token=token)
    oid = r.get("data", {}).get("order_id")
    check("处方订单创建", bool(oid and oid.startswith("ORD-")), str(oid))
    flow_ok = True
    for st in ["accepted", "preparing", "decocting", "shipped"]:
        rr = call("/api/clinic/orders/" + oid + "/status", {"to_status": st}, token=ctoken)
        flow_ok = flow_ok and rr.get("success", False)
    check("订单全链流转", flow_ok)
    evs = call("/api/orders/" + oid + "/events", token=token).get("data", {}).get("events", [])
    check("order_events 留痕 >= 5", len(evs) >= 5, f"events={len(evs)}")
    r = call("/api/clinic/dashboard", token=ctoken)["data"]
    check("医馆 dashboard", r.get("total_rx", 0) >= 1)

print("== 6. 商城 ==")
r = call("/api/products")["data"]
check("商品列表含合规文案", bool(r.get("notice")) and r.get("raw_herbs_coming_soon") is True)
r = call("/api/orders", {"order_type": "mall", "items": [{"product_id": "sour_plum_soup", "qty": 2}],
                         "fulfillment": "delivery", "address": "北京市"}, token=token)
check("商城订单服务端算价", r.get("data", {}).get("amount") == 3990 * 2, str(r.get("data", {}).get("amount")))

print("== 7. 平台后台（P4） ==")
r = call("/api/admin/stats", headers=ADMIN)["data"]
check("stats 含用户/医馆/订单/处方", all(k in r for k in ("users", "clinics", "orders", "prescriptions")),
      f"clinics={r.get('clinics')}")
r = call("/api/admin/users?page=1&size=5", headers=ADMIN)["data"]
check("admin/users 分页+脱敏", r.get("total", 0) >= 1 and "****" in r["users"][0]["phone"])
r = call("/api/admin/orders?order_type=prescription", headers=ADMIN)["data"]
check("admin/orders 类型过滤", r.get("total", 0) >= 1 and all(
    o["order_type"] == "prescription" for o in r["orders"]))
r = call("/api/admin/orders?status=completed", headers=ADMIN)["data"]
check("admin/orders 状态过滤", all(o["status"] == "completed" for o in r["orders"]))
r = call(f"/api/admin/clinics/{cid}/verifications", headers=ADMIN)["data"]
check("医馆核验记录", any(v.get("cv_id", "").startswith("CV-") for v in r.get("list", [])))

print(f"\n结果: {len(passed)} 通过, {len(failed)} 失败")
if failed:
    print("失败项:", ", ".join(failed))
    sys.exit(1)
print("全部通过")
