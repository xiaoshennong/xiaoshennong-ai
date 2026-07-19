#!/usr/bin/env python3
"""
小神农中医AI - Flask API服务
提供：AI辨证、知识检索、用户管理、订单接口
"""

import os
import json
import sys
import time
import io
from datetime import datetime
from functools import wraps

# 强制禁用字节码缓存，确保加载最新代码
sys.dont_write_bytecode = True

# Windows 环境下强制 stdout/stderr 使用 UTF-8，避免打印含生僻字符时崩溃
if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="backslashreplace", line_buffering=True)
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="backslashreplace", line_buffering=True)
    except Exception:
        pass

# 加载项目根目录 .env 文件到环境变量
try:
    from dotenv import load_dotenv
    _project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _env_path = os.path.join(_project_root, ".env")
    if os.path.exists(_env_path):
        load_dotenv(_env_path, override=False)
        print(f"[API] 已加载环境变量: {_env_path}")
except Exception as e:
    print(f"[API] 加载 .env 失败（可忽略）: {e}")

from flask import Flask, request, jsonify, Response, g
from flask_cors import CORS

from rag_engine_v2 import XiaoShennongRAGv2, DiagnosisResult

# 症状编号体系（比 knowledge_base_v3 的索引更完整，含口语化别名）
from symptom_codes import find_symptoms_by_text

# 无嵌入词法检索器（语义搜索主路，替代退化的英文向量模型）
from lexical_retriever import retrieve as lexical_retrieve

# 统一使用 Yunwu AI API（用户明确要求所有 API 走 yunwu.ai）
from llm_client_yunwu import get_llm_client, YunwuAIClient
print("[API] 使用 Yunwu AI 客户端")

from data_pipeline import DataPipeline

# 导入对话式问诊引擎
from dialogue_engine import get_dialogue_engine, DialoguePhase

# 导入多Agent系统
from multi_agent_system import get_agent_coordinator

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

app = Flask(__name__)
CORS(app)  # 允许跨域，微信小程序需要

# ============ 全局初始化 ============

# 初始化RAG引擎 v2.0
print("[API] 初始化RAG引擎 v2.0...")
rag_engine = XiaoShennongRAGv2(db_path=os.path.join(DATA_DIR, "chroma_db_v2"))

# 初始化LLM客户端（统一使用 Yunwu AI）
llm_provider = os.getenv("LLM_PROVIDER", "yunwu")
if llm_provider != "yunwu":
    print(f"[API] LLM_PROVIDER={llm_provider}，按用户要求强制使用 yunwu.ai")
    llm_provider = "yunwu"

llm_client = get_llm_client(llm_provider)
print(f"[API] LLM客户端: yunwu")

# ========== 延迟加载的单例 ==========
# 这些组件只在首次请求时初始化，降低启动内存占用并加快启动速度

_data_pipeline_instance = None

def get_data_pipeline():
    """获取数据管道单例（延迟加载）"""
    global _data_pipeline_instance
    if _data_pipeline_instance is None:
        print("[API] 延迟加载数据管道...")
        _data_pipeline_instance = DataPipeline()
        print("[API] 数据管道加载完成")
    return _data_pipeline_instance


_knowledge_base_instance = None

def get_kb():
    """获取知识库单例（延迟加载）"""
    global _knowledge_base_instance
    if _knowledge_base_instance is None:
        print("[API] 延迟加载知识库...")
        try:
            from knowledge_base_v3 import get_knowledge_base
            _knowledge_base_instance = get_knowledge_base()
            print("[API] 知识库延迟加载完成")
        except Exception as e:
            print(f"[API] 知识库延迟加载失败: {e}")
            import traceback
            traceback.print_exc()
            _knowledge_base_instance = None
    return _knowledge_base_instance


_dialogue_engine_instance = None

def get_dialogue_engine_lazy():
    """获取对话式问诊引擎单例（延迟加载）"""
    global _dialogue_engine_instance
    if _dialogue_engine_instance is None:
        print("[API] 延迟加载对话式问诊引擎...")
        _dialogue_engine_instance = get_dialogue_engine()
        print("[API] 对话式问诊引擎加载完成")
    return _dialogue_engine_instance


_agent_coordinator_instance = None

def get_agent_coordinator_lazy():
    """获取多Agent协调器单例（延迟加载）"""
    global _agent_coordinator_instance
    if _agent_coordinator_instance is None:
        print("[API] 延迟加载多Agent系统...")
        _agent_coordinator_instance = get_agent_coordinator(os.path.join(DATA_DIR, "agent_data"))
        print("[API] 多Agent系统加载完成")
    return _agent_coordinator_instance


print("[API] 核心组件已配置为延迟加载模式，将在首次请求时初始化")

# 简单的内存用户存储（MVP阶段，生产环境应使用数据库）
users_db = {}
sessions_db = {}

# ========== 后台管理认证 ==========
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "xiaoshennong-admin")

def require_admin(f):
    """后台管理接口认证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("X-Admin-Token", "")
        if token != ADMIN_TOKEN:
            return jsonify({"success": False, "error": "未授权访问，请提供正确的 X-Admin-Token"}), 401
        return f(*args, **kwargs)
    return decorated


# ============ 工具函数 ============

def format_diagnosis_result(result) -> dict:
    """格式化辨证结果为API响应（v2.2批判性思维+副作用检测格式）"""
    return {
        "constitution": result.constitution,
        "syndrome": result.syndrome,
        "advice": result.advice,
        "sources": [
            {
                "book": s["book"],
                "section": s["section"],
                "original_text": s.get("original_text", ""),
                "text": s["text"]
            }
            for s in result.sources
        ],
        "warning": result.warning,
        "thinking_process": result.thinking_process,
        "total_time_ms": result.total_time_ms,
        "timestamp": datetime.now().isoformat(),
        # v2.0字段
        "symptom_analysis": result.symptom_analysis,
        "matched_formulas": result.matched_formulas,
        "matched_drugs": result.matched_drugs,
        "contraindications": result.contraindications,
        "classic_sources": result.classic_sources,
        # v2.1新增字段
        "syndrome_analysis": result.syndrome_analysis,
        "drug_relations": result.drug_relations,
        "syndrome_matched": result.syndrome_matched,
        "syndrome_match_score": result.syndrome_match_score,
        # v2.2新增字段（批判性思维+副作用检测）
        "credibility_assessment": result.credibility_assessment,
        "cooccurrence_analysis": result.cooccurrence_analysis,
        "adverse_detection": result.adverse_detection,
        "similar_patients": result.similar_patients,
        "knowledge_gap_report": result.knowledge_gap_report,
        "import_suggestions": result.import_suggestions,
    }


def enhance_diagnosis_with_kb(symptoms_text: str, result: dict) -> dict:
    """使用知识库增强诊断结果（补充方剂/药物/医案）"""
    kb = get_kb()
    if not kb:
        print("[API] 知识库不可用，跳过增强")
        return result
    
    try:
        # 识别症状（使用 symptom_codes 的别名索引，含口语化表达）
        matched_symptoms = find_symptoms_by_text(symptoms_text)
        if not matched_symptoms:
            return result
        
        symptom_ids = [s['id'] for s in matched_symptoms]
        
        # 补充方剂（如果RAG结果为空）
        if not result.get('matched_formulas'):
            formulas = kb.find_formulas_by_symptoms(symptom_ids)
            result['matched_formulas'] = [
                {
                    'id': f['id'],
                    'name': f['name'],
                    'source': f['source'],
                    'syndrome': f['syndrome'],
                    'match_score': round(f['match_score'], 2),
                    'matched_symptoms': f['matched_symptoms'],
                    'contraindications': f['contraindications']
                }
                for f in formulas[:5]
            ]
        
        # 补充药物（如果RAG结果为空）
        if not result.get('matched_drugs'):
            drugs = kb.find_drugs_by_symptoms(symptom_ids)
            result['matched_drugs'] = [
                {
                    'id': d['id'],
                    'name': d['name'],
                    'properties': d['properties'],
                    'match_score': round(d['match_score'], 2),
                    'matched_symptoms': d['matched_symptoms'],
                    'contraindications': d['contraindications']
                }
                for d in drugs[:5]
            ]
        
        # 补充相似医案
        similar_cases = kb.search_cases(symptom_ids, limit=3)
        if similar_cases:
            result['similar_cases'] = [
                {
                    'case_id': c['case_id'],
                    'syndrome': c['syndrome'],
                    'formula': c['formula_name'],
                    'effectiveness': c['effectiveness'],
                    'doctor': c['doctor']
                }
                for c in similar_cases
            ]
        
        # 补充知识库统计
        result['knowledge_base_stats'] = kb.get_stats()
        
    except Exception as e:
        print(f"[API] 知识库增强失败: {e}")
    
    return result


def require_auth(f):
    """简单的认证装饰器（MVP阶段）"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # MVP阶段暂不强制认证，生产环境应验证JWT token
        return f(*args, **kwargs)
    return decorated


# ============ API路由 ============

@app.route("/api/health", methods=["GET"])
def health_check():
    """健康检查接口"""
    return jsonify({
        "status": "ok",
        "service": "xiaoshennong-api",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "rag_stats": rag_engine.get_stats()
    })


@app.route("/api/diagnosis", methods=["POST"])
def diagnose():
    """
    AI辨证接口
    
    请求体：
    {
        "symptoms": "头痛发热，怕冷，没有汗",  # 症状描述
        "history": "",                           # 病史（可选）
        "age": 30,                               # 年龄（可选）
        "gender": "male"                         # 性别（可选）
    }
    
    响应：
    {
        "success": true,
        "data": {
            "constitution": "...",
            "syndrome": "...",
            "advice": "...",
            "sources": [...],
            "warning": "..."
        }
    }
    """
    try:
        # 健壮地解析请求数据
        data = None
        try:
            data = request.get_json(force=True, silent=True)
        except Exception:
            pass
        
        # 如果get_json失败，尝试手动解析
        if not data:
            try:
                raw_data = request.get_data(as_text=True)
                if raw_data:
                    data = json.loads(raw_data)
            except Exception:
                pass
        
        if not data or "symptoms" not in data:
            return jsonify({
                "success": False,
                "error": "缺少症状描述（symptoms字段）"
            }), 400
        
        symptoms = data["symptoms"]
        history = data.get("history", "")
        age = data.get("age", "")
        gender = data.get("gender", "")
        
        # 构建查询
        query = f"症状：{symptoms}"
        if history:
            query += f"，病史：{history}"
        if age:
            query += f"，年龄：{age}岁"
        if gender:
            query += f"，性别：{'男' if gender == 'male' else '女'}"
        
        print(f"[API] 辨证请求: {query[:50]}...")
        
        # 调用RAG引擎
        start_time = time.time()
        result = rag_engine.diagnose(query, llm_client)
        latency = (time.time() - start_time) * 1000
        
        print(f"[API] 辨证完成，耗时{latency:.0f}ms")
        print(f"[API] 结果: constitution={result.constitution[:20]}, syndrome={result.syndrome[:20]}")
        print(f"[API] 思考步骤: {len(result.thinking_process)}")
        print(f"[API] v2.0字段: symptom_analysis={bool(result.symptom_analysis)}, formulas={len(result.matched_formulas)}, drugs={len(result.matched_drugs)}, contras={len(result.contraindications)}")
        sys.stdout.flush()
        
        formatted = format_diagnosis_result(result)
        print(f"[API] formatted: symptom_analysis={bool(formatted.get('symptom_analysis'))}, formulas={len(formatted.get('matched_formulas', []))}, drugs={len(formatted.get('matched_drugs', []))}")
        sys.stdout.flush()
        
        # 使用知识库增强结果（补充方剂/药物/医案）
        kb = get_kb()
        if kb:
            print(f"[API] 知识库增强输入: symptoms='{symptoms[:30]}...', type={type(symptoms)}")
            formatted = enhance_diagnosis_with_kb(symptoms, formatted)
            print(f"[API] 知识库增强后: formulas={len(formatted.get('matched_formulas', []))}, drugs={len(formatted.get('matched_drugs', []))}")
        else:
            print(f"[API] 知识库未加载，跳过增强")
        
        return jsonify({
            "success": True,
            "data": formatted,
            "meta": {
                "latency_ms": round(latency, 2),
                "model": llm_provider
            }
        })
    
    except Exception as e:
        import traceback
        print(f"[API] 辨证错误: {e}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"系统处理失败: {str(e)}"
        }), 500


@app.route("/api/diagnosis/stream", methods=["POST"])
def diagnose_stream():
    """
    流式 AI 辨证接口（SSE）
    返回结构兼容前端 showDiagnosisResult：
      data.diagnosis = { symptoms, formulas, acupoints, dietary, qigong, massage }
    """
    def _err_stream(msg):
        payload = json.dumps({'type': 'error', 'data': msg}, ensure_ascii=False)
        yield f"data: {payload}\n\n"

    try:
        data = request.get_json(force=True, silent=True) or {}
        if not data or "symptoms" not in data:
            return Response(_err_stream("缺少症状描述（symptoms字段）"), mimetype='text/event-stream')

        symptoms_text = data["symptoms"]
        history = data.get("history", "")
        age = data.get("age", "")
        gender = data.get("gender", "")

        query = f"症状：{symptoms_text}"
        if history:
            query += f"，病史：{history}"
        if age:
            query += f"，年龄：{age}岁"
        if gender:
            query += f"，性别：{'男' if gender == 'male' else '女'}"

        def generate():
            # 调用 RAG 引擎
            result = rag_engine.diagnose(query, llm_client)
            formatted = format_diagnosis_result(result)
            kb = get_kb()
            if kb:
                formatted = enhance_diagnosis_with_kb(symptoms_text, formatted)

            # 发送思考步骤
            for step in formatted.get('thinking_process', []):
                payload = json.dumps({'type': 'thinking', 'data': step}, ensure_ascii=False)
                yield f"data: {payload}\n\n"

            # 用症状编号体系把输入症状映射为结构化症状节点
            matched_symptoms = find_symptoms_by_text(symptoms_text) or []

            # 构建前端需要的结构化 diagnosis
            diagnosis = {
                'symptoms': [
                    {'id': s.get('id', ''), 'name': s.get('name', '')}
                    for s in matched_symptoms[:10]
                ],
                'formulas': [
                    {
                        'id': f.get('id', ''),
                        'name': f.get('name', ''),
                        'functions': f.get('syndrome', '') or f.get('source', ''),
                        'composition': []
                    }
                    for f in formatted.get('matched_formulas', [])[:5]
                ],
                'acupoints': [],
                'dietary': [],
                'qigong': [],
                'massage': []
            }

            # 确保新结构化字段存在且为数组
            for key in ['acupoints', 'dietary', 'qigong', 'massage']:
                diagnosis.setdefault(key, [])

            # 精简文本，避免 SSE JSON 被浏览器插件截断
            def _strip_emojis(text):
                if not isinstance(text, str):
                    return text
                import re
                return re.sub(r'[\U00010000-\U0010ffff]', '', text)

            stream_result = {
                'diagnosis': diagnosis,
                'constitution': formatted.get('constitution', ''),
                'syndrome': formatted.get('syndrome', ''),
                'advice': _strip_emojis(formatted.get('advice', '')),
                'warning': formatted.get('warning', ''),
                'matched_formulas': [f.get('name', '') for f in formatted.get('matched_formulas', [])[:3]],
                'matched_drugs': [d.get('name', '') for d in formatted.get('matched_drugs', [])[:3]],
                'contraindications': formatted.get('contraindications', [])[:3]
            }
            payload = json.dumps({'type': 'result', 'data': stream_result}, ensure_ascii=False)
            yield f"data: {payload}\n\n"

            payload = json.dumps({'type': 'done'}, ensure_ascii=False)
            yield f"data: {payload}\n\n"

        return Response(generate(), mimetype='text/event-stream')

    except Exception as e:
        import traceback
        print(f"[API] 流式辨证错误: {e}")
        traceback.print_exc()
        return Response(_err_stream(f"系统处理失败: {str(e)}"), mimetype='text/event-stream')


@app.route("/api/retrieve", methods=["POST"])
def retrieve():
    """
    知识检索接口（仅返回检索结果，不生成回答）
    
    请求体：
    {
        "query": "麻黄汤",
        "top_k": 5
    }
    """
    try:
        data = request.get_json()
        query = data.get("query", "")
        top_k = data.get("top_k", 5)
        
        if not query:
            return jsonify({"success": False, "error": "缺少查询内容"}), 400
        
        # 词法检索主路（别名+元数据打分）；零结果时回退向量检索兜底
        chunks = lexical_retrieve(query, top_k=top_k)
        engine = "lexical"
        if not chunks:
            chunks = rag_engine.retrieve(query, top_k=top_k)
            engine = "vector"
        
        results = []
        for chunk in chunks:
            results.append({
                "text": chunk.text,
                "source_book": chunk.source_book,
                "source_section": chunk.source_section,
                "original_text": chunk.original_text,
                "score": round(chunk.score, 4)
            })
        
        return jsonify({
            "success": True,
            "data": {
                "query": query,
                "engine": engine,
                "results": results,
                "total": len(results)
            }
        })
    
    except Exception as e:
        print(f"[API] 检索错误: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/semantic/search", methods=["POST"])
def semantic_search():
    """
    语义搜索接口（前端兼容别名，底层复用 /api/retrieve）
    返回按类型分组的检索结果，方便前端展示。
    """
    try:
        data = request.get_json() or {}
        query = data.get("query", "")
        top_k = data.get("top_k", 10)

        if not query:
            return jsonify({"success": False, "error": "缺少查询内容"}), 400

        # 词法检索主路；零结果时回退向量检索兜底
        chunks = lexical_retrieve(query, top_k=top_k)
        engine = "lexical"
        if not chunks:
            chunks = rag_engine.retrieve(query, top_k=top_k)
            engine = "vector"

        # 按来源/类型分组，兼容前端展示
        grouped = {}
        for chunk in chunks:
            book = chunk.source_book or "古籍"
            grouped.setdefault(book, []).append({
                "text": chunk.text,
                "source_book": chunk.source_book,
                "source_section": chunk.source_section,
                "original_text": chunk.original_text,
                "score": round(chunk.score, 4)
            })

        return jsonify({
            "success": True,
            "data": {
                "query": query,
                "engine": engine,
                "results": grouped,
                "total": len(chunks)
            }
        })

    except Exception as e:
        print(f"[API] 语义搜索错误: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/knowledge/stats", methods=["GET"])
def knowledge_stats():
    """知识库统计信息"""
    return jsonify({
        "success": True,
        "data": rag_engine.get_stats()
    })


@app.route("/api/knowledge/import", methods=["POST"])
def import_knowledge():
    """
    导入知识库数据
    
    请求体：
    {
        "documents": [
            {
                "text": "...",
                "metadata": {
                    "source_book": "...",
                    "source_section": "..."
                }
            }
        ]
    }
    """
    try:
        data = request.get_json()
        documents = data.get("documents", [])
        
        if not documents:
            return jsonify({"success": False, "error": "缺少文档数据"}), 400
        
        rag_engine.add_documents(documents)
        
        return jsonify({
            "success": True,
            "data": {
                "imported_count": len(documents),
                "total_count": rag_engine.get_stats()["total_documents"]
            }
        })
    
    except Exception as e:
        print(f"[API] 导入错误: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/knowledge/batch_import", methods=["POST"])
def batch_import():
    """批量导入目录下的数据文件"""
    try:
        data = request.get_json() or {}
        data_dir = data.get("data_dir", os.path.join(DATA_DIR, "raw"))
        
        count = get_data_pipeline().batch_import(rag_engine, data_dir)
        
        return jsonify({
            "success": True,
            "data": {
                "imported_count": count,
                "total_count": rag_engine.get_stats()["total_documents"]
            }
        })
    
    except Exception as e:
        print(f"[API] 批量导入错误: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ============ 用户相关接口（简化版） ============
# 注意：以下两个接口为早期 MVP 内存版，已废弃（deprecated），
# 新系统请使用 /api/auth/* （手机号+密码+短信绑定，SQLite 持久化）。
# 保留仅为避免旧前端/小程序骨架 404，内存数据重启即失。

@app.route("/api/user/register", methods=["POST"])
def user_register():
    """用户注册"""
    data = request.get_json()
    user_id = data.get("openid", f"user_{int(time.time())}")
    
    users_db[user_id] = {
        "id": user_id,
        "created_at": datetime.now().isoformat(),
        "health_profile": data.get("health_profile", {})
    }
    
    return jsonify({
        "success": True,
        "data": {"user_id": user_id}
    })


@app.route("/api/user/profile", methods=["GET"])
def user_profile():
    """获取用户资料"""
    user_id = request.args.get("user_id", "")
    
    if user_id not in users_db:
        return jsonify({"success": False, "error": "用户不存在"}), 404
    
    return jsonify({
        "success": True,
        "data": users_db[user_id]
    })


# ============ 账号认证接口（手机号锚点，M2） ============

from auth_service import (
    register_user, login_by_password, login_by_sms, reset_password,
    update_profile, logout as auth_logout, require_user,
)
from sms_service import send_code, verify_code


@app.route("/api/auth/sms_code", methods=["POST"])
def auth_sms_code():
    """发送短信验证码（开发模式下响应带 dev_code）"""
    data = request.get_json() or {}
    phone = data.get("phone", "").strip()
    purpose = data.get("purpose", "register")
    if purpose not in ("register", "login", "reset"):
        return jsonify({"success": False, "error": "不支持的验证码用途"}), 400
    result = send_code(phone, purpose)
    if not result["success"]:
        return jsonify({"success": False, "error": result["error"]}), 400
    resp = {"success": True, "data": {"message": "验证码已发送"}}
    if result.get("dev_code"):
        resp["data"]["dev_code"] = result["dev_code"]
        resp["data"]["dev_mode"] = True
    return jsonify(resp)


@app.route("/api/auth/register", methods=["POST"])
def auth_register():
    """注册：手机号+密码+短信验证码+知情同意"""
    data = request.get_json() or {}
    phone = data.get("phone", "").strip()
    password = data.get("password", "")
    code = data.get("code", "").strip()
    consent = bool(data.get("consent"))
    nickname = data.get("nickname", "").strip()

    if not verify_code(phone, code, "register"):
        return jsonify({"success": False, "error": "验证码错误或已过期"}), 400

    user, err = register_user(phone, password, consent, nickname)
    if err:
        return jsonify({"success": False, "error": err}), 400
    return jsonify({"success": True, "data": {"user": user}})


@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    """账密登录"""
    data = request.get_json() or {}
    token, user, err = login_by_password(data.get("phone", "").strip(), data.get("password", ""))
    if err:
        return jsonify({"success": False, "error": err}), 401
    return jsonify({"success": True, "data": {"token": token, "user": user}})


@app.route("/api/auth/login_sms", methods=["POST"])
def auth_login_sms():
    """验证码登录（Web 备用 / 小程序一期）"""
    data = request.get_json() or {}
    phone = data.get("phone", "").strip()
    code = data.get("code", "").strip()
    if not verify_code(phone, code, "login"):
        return jsonify({"success": False, "error": "验证码错误或已过期"}), 400
    token, user, err = login_by_sms(phone)
    if err:
        return jsonify({"success": False, "error": err}), 401
    return jsonify({"success": True, "data": {"token": token, "user": user}})


@app.route("/api/auth/reset_password", methods=["POST"])
def auth_reset_password():
    """短信验证码重置密码"""
    data = request.get_json() or {}
    phone = data.get("phone", "").strip()
    code = data.get("code", "").strip()
    if not verify_code(phone, code, "reset"):
        return jsonify({"success": False, "error": "验证码错误或已过期"}), 400
    ok, err = reset_password(phone, data.get("new_password", ""))
    if not ok:
        return jsonify({"success": False, "error": err}), 400
    return jsonify({"success": True, "data": {"message": "密码已重置，请重新登录"}})


@app.route("/api/auth/me", methods=["GET"])
@require_user
def auth_me():
    from auth_service import get_user
    user = get_user(g.current_user["user_id"])
    return jsonify({"success": True, "data": {"user": user}})


@app.route("/api/auth/profile", methods=["PUT"])
@require_user
def auth_update_profile():
    data = request.get_json() or {}
    user = update_profile(g.current_user["user_id"], data)
    return jsonify({"success": True, "data": {"user": user}})


@app.route("/api/auth/logout", methods=["POST"])
def auth_logout_route():
    auth = request.headers.get("Authorization", "")
    token = auth[7:].strip() if auth.startswith("Bearer ") else request.headers.get("X-User-Token", "")
    if token:
        auth_logout(token)
    return jsonify({"success": True, "data": {"message": "已退出登录"}})


@app.route("/api/auth/wx_phone_login", methods=["POST"])
def auth_wx_phone_login():
    """微信小程序手机号一键登录（二期实现：需企业主体小程序，约 3 分/次）。
    一期小程序端请走 /api/auth/login_sms。"""
    return jsonify({
        "success": False,
        "error": "微信一键登录二期开放，请使用手机号验证码登录"
    }), 501


# ============ 电子病历接口（M3） ============

from emr_service import ensure_profile, update_profile as emr_update_profile, list_records


@app.route("/api/user/emr", methods=["GET"])
@require_user
def emr_list():
    """我的病历列表（健康档案 + 历次就诊记录）"""
    records = list_records(g.current_user["user_id"])
    return jsonify({"success": True, "data": {"records": records, "total": len(records)}})


@app.route("/api/user/emr/profile", methods=["GET"])
@require_user
def emr_profile_get():
    """查看健康档案"""
    profile = ensure_profile(g.current_user["user_id"])
    return jsonify({"success": True, "data": {"profile": profile}})


@app.route("/api/user/emr/profile", methods=["PUT"])
@require_user
def emr_profile_put():
    """编辑健康档案（身高体重/血型/家族史 + 既往史/过敏史/用药史/月经婚育史）"""
    data = request.get_json() or {}
    profile = emr_update_profile(g.current_user["user_id"], data)
    return jsonify({"success": True, "data": {"profile": profile}})


# ============ 医馆入驻 / 药方审核 / 处方订单接口（M4） ============

from auth_service import require_clinic, create_session as auth_create_session
from clinic_service import (
    apply_clinic, login_clinic, get_clinic, list_verified_clinics, verify_clinic,
    list_all_clinics, apply_prescription, rx_queue, review_prescription,
    get_user_rx, get_rx, create_order, update_order_status, list_orders,
    order_events, clinic_dashboard,
)


@app.route("/api/clinic/apply", methods=["POST"])
def clinic_apply():
    """医馆入驻申请：立即开通账号（pending），审核/接单权限待平台核验后解锁"""
    data = request.get_json() or {}
    result, err = apply_clinic(
        name=data.get("name", "").strip(),
        license_no=data.get("license_no", "").strip(),
        address=data.get("address", "").strip(),
        phone=data.get("phone", "").strip(),
        account_phone=data.get("account_phone", "").strip(),
        password=data.get("password", ""),
        contact_name=data.get("contact_name", "").strip(),
        support_decoction=bool(data.get("support_decoction")),
        decoction_fee=int(data.get("decoction_fee") or 0),
        delivery_scope=data.get("delivery_scope", "").strip(),
    )
    if err:
        return jsonify({"success": False, "error": err}), 400
    return jsonify({"success": True, "data": result})


@app.route("/api/clinic/login", methods=["POST"])
def clinic_login():
    data = request.get_json() or {}
    clinic_id, name, err = login_clinic(data.get("phone", "").strip(), data.get("password", ""))
    if err:
        return jsonify({"success": False, "error": err}), 401
    token = auth_create_session(clinic_id, "clinic", clinic_id=clinic_id)
    clinic = get_clinic(clinic_id)
    return jsonify({"success": True, "data": {
        "token": token, "clinic_id": clinic_id, "name": name,
        "clinic_name": clinic["name"] if clinic else "",
        "status": clinic["status"] if clinic else "",
    }})


@app.route("/api/clinic/list", methods=["GET"])
def clinic_list():
    """给用户挑选的医馆列表（仅已核验，含代煎/配送信息）"""
    return jsonify({"success": True, "data": {"clinics": list_verified_clinics()}})


@app.route("/api/clinic/dashboard", methods=["GET"])
@require_clinic
def clinic_dash():
    return jsonify({"success": True, "data": clinic_dashboard(g.current_user["clinic_id"])})


@app.route("/api/clinic/profile", methods=["GET"])
@require_clinic
def clinic_profile():
    clinic = get_clinic(g.current_user["clinic_id"])
    return jsonify({"success": True, "data": {"clinic": clinic}})


@app.route("/api/clinic/rx_queue", methods=["GET"])
@require_clinic
def clinic_rx_queue():
    status = request.args.get("status", "pending_review")
    return jsonify({"success": True, "data": {"list": rx_queue(g.current_user["clinic_id"], status)}})


@app.route("/api/clinic/rx/<rx_id>/review", methods=["POST"])
@require_clinic
def clinic_rx_review(rx_id):
    """医师审核：approve（可带 adjusted_formula 加减）/ reject（填 note）"""
    data = request.get_json() or {}
    ok, err = review_prescription(
        clinic_id=g.current_user["clinic_id"],
        rx_id=rx_id,
        action=data.get("action", ""),
        reviewer=g.current_user["user_id"],
        note=data.get("note", "").strip(),
        adjusted_formula=data.get("adjusted_formula"),
    )
    if not ok:
        code = 403 if "权限" in (err or "") else 400
        return jsonify({"success": False, "error": err}), code
    return jsonify({"success": True, "data": {"rx_id": rx_id}})


@app.route("/api/clinic/orders", methods=["GET"])
@require_clinic
def clinic_orders():
    return jsonify({"success": True, "data": {"orders": list_orders(clinic_id=g.current_user["clinic_id"])}})


@app.route("/api/clinic/orders/<order_id>/status", methods=["POST"])
@require_clinic
def clinic_order_status(order_id):
    data = request.get_json() or {}
    ok, err = update_order_status(
        clinic_id=g.current_user["clinic_id"],
        order_id=order_id,
        to_status=data.get("to_status", ""),
        operator=f"clinic:{g.current_user['user_id']}",
        note=data.get("note", "").strip(),
    )
    if not ok:
        code = 403 if "权限" in (err or "") else 400
        return jsonify({"success": False, "error": err}), code
    return jsonify({"success": True, "data": {"order_id": order_id}})


# ---- 用户端：开方申请与订单 ----

@app.route("/api/rx/apply", methods=["POST"])
@require_user
def rx_apply():
    """发起开方申请：AI 建议+病历快照推给选定医馆审核。
    两种来源：
    - 对话模式：传 session_id（服务端取会话快照，可信来源）
    - 快速辨证：传 symptoms + advice（客户端回传，快照标注 source=quick，医师审核时可见）"""
    data = request.get_json() or {}
    session_id = data.get("session_id", "")
    clinic_id = data.get("clinic_id", "")
    user_id = g.current_user["user_id"]

    from emr_service import get_profile_for_dialogue

    if session_id:
        dialogue_engine = get_dialogue_engine_lazy()
        state = dialogue_engine.get_session(session_id)
        if not state or state.user_id != user_id:
            return jsonify({"success": False, "error": "问诊会话不存在或不属于当前用户"}), 400
        if not state.last_diagnosis:
            return jsonify({"success": False, "error": "该会话尚未完成辨证，无法申请开方"}), 400
        snapshot = {
            "source": "dialogue",
            "profile": get_profile_for_dialogue(user_id),
            "collected_symptoms": [
                {"id": s.symptom_id, "name": s.name} for s in state.collected_symptoms.values()
            ],
            "first_complaint": state.first_complaint,
        }
        ai_advice = state.last_diagnosis.get("advice", "")
    else:
        symptoms_text = (data.get("symptoms") or "").strip()
        ai_advice = (data.get("advice") or "").strip()
        if not symptoms_text or not ai_advice:
            return jsonify({"success": False, "error": "缺少症状或辨证建议内容"}), 400
        snapshot = {
            "source": "quick",
            "profile": get_profile_for_dialogue(user_id),
            "symptoms_text": symptoms_text[:500],
        }
        ai_advice = ai_advice[:5000]

    rx_id, err = apply_prescription(
        user_id=user_id, clinic_id=clinic_id, session_id=session_id,
        emr_snapshot=snapshot, ai_advice=ai_advice,
    )
    if err:
        return jsonify({"success": False, "error": err}), 400
    return jsonify({"success": True, "data": {"rx_id": rx_id, "status": "pending_review"}})


@app.route("/api/rx/list", methods=["GET"])
@require_user
def rx_list():
    return jsonify({"success": True, "data": {"list": get_user_rx(g.current_user["user_id"])}})


@app.route("/api/rx/<rx_id>", methods=["GET"])
@require_user
def rx_detail(rx_id):
    rx = get_rx(rx_id)
    if not rx or rx["user_id"] != g.current_user["user_id"]:
        return jsonify({"success": False, "error": "处方不存在"}), 404
    return jsonify({"success": True, "data": {"rx": rx}})


@app.route("/api/orders", methods=["POST"])
@require_user
def order_create():
    """创建订单：prescription 线需 RX 已审核；mall 线服务端按商品价重算金额"""
    data = request.get_json() or {}
    order_type = data.get("order_type", "mall")
    items = data.get("items") or []
    amount = 0
    if order_type == "mall":
        price_map = {p["id"]: p["price"] for p in products_db}
        for it in items:
            pid = it.get("product_id")
            qty = max(1, int(it.get("qty") or 1))
            if pid not in price_map:
                return jsonify({"success": False, "error": f"商品不存在: {pid}"}), 400
            amount += price_map[pid] * qty
            it["qty"] = qty
    order_id, err = create_order(
        user_id=g.current_user["user_id"],
        order_type=order_type,
        items=items,
        rx_id=data.get("rx_id", ""),
        fulfillment=data.get("fulfillment", ""),
        decoction=bool(data.get("decoction")),
        address=data.get("address", "").strip(),
        amount=int(data.get("amount") or amount),
    )
    if err:
        return jsonify({"success": False, "error": err}), 400
    return jsonify({"success": True, "data": {"order_id": order_id, "amount": amount}})


@app.route("/api/orders", methods=["GET"])
@require_user
def order_list():
    return jsonify({"success": True, "data": {"orders": list_orders(user_id=g.current_user["user_id"])}})


@app.route("/api/orders/<order_id>/events", methods=["GET"])
@require_user
def order_event_list(order_id):
    return jsonify({"success": True, "data": {"events": order_events(order_id)}})


# ---- 平台端：医馆核验 ----

@app.route("/api/admin/clinics", methods=["GET"])
@require_admin
def admin_clinics():
    return jsonify({"success": True, "data": {"clinics": list_all_clinics()}})


@app.route("/api/admin/clinics/<clinic_id>/verify", methods=["POST"])
@require_admin
def admin_clinic_verify(clinic_id):
    """核验解锁（verified）/ 冻结（frozen），动作生成 CV 编号审核记录"""
    data = request.get_json() or {}
    ok, err = verify_clinic(
        clinic_id=clinic_id,
        action=data.get("action", ""),
        reviewer="admin",
        note=data.get("note", "").strip(),
    )
    if not ok:
        return jsonify({"success": False, "error": err}), 400
    return jsonify({"success": True, "data": {"clinic_id": clinic_id}})


@app.route("/api/admin/users", methods=["GET"])
@require_admin
def admin_users():
    """用户管理列表（P4）：分页、手机号脱敏、含病历数/订单数"""
    from db import get_conn
    from auth_service import mask_phone
    page = max(1, int(request.args.get("page", 1)))
    size = min(100, max(1, int(request.args.get("size", 20))))
    conn = get_conn()
    try:
        total = conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
        rows = conn.execute(
            """SELECT u.user_id, u.phone, u.nickname, u.gender, u.birth_year, u.created_at,
                      (SELECT COUNT(*) FROM emr e WHERE e.user_id = u.user_id) AS emr_count,
                      (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.user_id) AS order_count
               FROM users u ORDER BY u.created_at DESC LIMIT ? OFFSET ?""",
            (size, (page - 1) * size),
        ).fetchall()
        users = []
        for r in rows:
            d = dict(r)
            d["phone"] = mask_phone(d["phone"])
            users.append(d)
        return jsonify({"success": True, "data": {"users": users, "total": total, "page": page, "size": size}})
    finally:
        conn.close()


@app.route("/api/admin/orders", methods=["GET"])
@require_admin
def admin_orders():
    """订单总览（P4）：按状态/类型过滤，含医馆名"""
    from db import get_conn
    status = request.args.get("status", "")
    order_type = request.args.get("order_type", "")
    page = max(1, int(request.args.get("page", 1)))
    size = min(100, max(1, int(request.args.get("size", 20))))
    where, params = [], []
    if status:
        where.append("o.status = ?")
        params.append(status)
    if order_type:
        where.append("o.order_type = ?")
        params.append(order_type)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    conn = get_conn()
    try:
        total = conn.execute(f"SELECT COUNT(*) c FROM orders o {where_sql}", params).fetchone()["c"]
        rows = conn.execute(
            f"""SELECT o.*, c.name AS clinic_name
                FROM orders o LEFT JOIN clinics c ON c.clinic_id = o.clinic_id
                {where_sql} ORDER BY o.created_at DESC LIMIT ? OFFSET ?""",
            params + [size, (page - 1) * size],
        ).fetchall()
        orders = []
        for r in rows:
            d = dict(r)
            if d.get("items"):
                try:
                    d["items"] = json.loads(d["items"])
                except Exception:
                    pass
            orders.append(d)
        return jsonify({"success": True, "data": {"orders": orders, "total": total, "page": page, "size": size}})
    finally:
        conn.close()


@app.route("/api/admin/clinics/<clinic_id>/verifications", methods=["GET"])
@require_admin
def admin_clinic_verifications(clinic_id):
    """某医馆的核验记录（CV 编号留痕）"""
    from db import get_conn
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM clinic_verifications WHERE clinic_id=? ORDER BY created_at DESC",
            (clinic_id,),
        ).fetchall()
        return jsonify({"success": True, "data": {"list": [dict(r) for r in rows]}})
    finally:
        conn.close()


# ============ 养生商城接口（简化版） ============

# MVP商品数据（内存存储）
products_db = [
    {
        "id": "sour_plum_soup",
        "name": "小神农·酸梅汤",
        "subtitle": "正宗宫廷配方，清热解暑",
        "price": 3990,  # 单位：分
        "original_price": 5990,
        "image": "https://example.com/sour_plum.jpg",
        "category": "基础爆款",
        "source": "《本草纲目》·梅",
        "expert": "中国中医科学院配方监制",
        "ingredients": ["乌梅", "山楂", "甘草", "陈皮", "冰糖"],
        "suitable_constitutions": ["阴虚质", "湿热质"],
        "stock": 1000,
        "sales": 256
    },
    {
        "id": "dampness_tea",
        "name": "小神农·祛湿茶",
        "subtitle": "赤小豆薏米升级版，健脾祛湿",
        "price": 4990,
        "original_price": 6990,
        "image": "https://example.com/dampness.jpg",
        "category": "功效刚需",
        "source": "《食疗本草》",
        "expert": "中国中医科学院配方监制",
        "ingredients": ["赤小豆", "薏苡仁", "茯苓", "芡实", "陈皮"],
        "suitable_constitutions": ["痰湿质", "湿热质"],
        "stock": 800,
        "sales": 189
    },
    {
        "id": "qing_bu_liang",
        "name": "小神农·清补凉",
        "subtitle": "岭南经典，清热润燥",
        "price": 2990,
        "original_price": 3990,
        "image": "https://example.com/qingbu.jpg",
        "category": "基础爆款",
        "source": "《岭南采药录》",
        "expert": "中国中医科学院配方监制",
        "ingredients": ["沙参", "玉竹", "莲子", "百合", "银耳"],
        "suitable_constitutions": ["阴虚质", "气虚质"],
        "stock": 600,
        "sales": 134
    },
    {
        "id": "sishen_tang",
        "name": "小神农·四神汤",
        "subtitle": "健脾养胃，调理脾胃",
        "price": 3990,
        "original_price": 4990,
        "image": "https://example.com/sishen.jpg",
        "category": "基础爆款",
        "source": "《本草纲目》·山药/茯苓",
        "expert": "中国中医科学院配方监制",
        "ingredients": ["山药", "茯苓", "芡实", "莲子"],
        "suitable_constitutions": ["气虚质", "阳虚质"],
        "stock": 500,
        "sales": 167
    },
    {
        "id": "chrysanthemum_tea",
        "name": "小神农·菊花枸杞茶",
        "subtitle": "清肝明目，滋阴降火",
        "price": 2990,
        "original_price": 3990,
        "image": "https://example.com/chrysanthemum.jpg",
        "category": "办公室养生",
        "source": "《神农本草经》·菊花",
        "expert": "中国中医科学院配方监制",
        "ingredients": ["菊花", "枸杞", "决明子"],
        "suitable_constitutions": ["阴虚质", "气郁质"],
        "stock": 1200,
        "sales": 312
    }
]


@app.route("/api/products", methods=["GET"])
def list_products():
    """获取商品列表"""
    category = request.args.get("category")
    constitution = request.args.get("constitution")  # 按体质推荐
    
    products = products_db
    
    if category:
        products = [p for p in products if p["category"] == category]
    
    if constitution:
        # 推荐适合该体质的商品
        products = [p for p in products if constitution in p.get("suitable_constitutions", [])]
    
    return jsonify({
        "success": True,
        "data": {
            "products": products,
            "total": len(products),
            "notice": "本商城产品均为药食同源养生品，不能替代药品。中药材原材料销售将于「医馆货架」二期开放，由具备药品经营资质的入驻医馆提供。",
            "raw_herbs_coming_soon": True
        }
    })


@app.route("/api/products/<product_id>", methods=["GET"])
def product_detail(product_id):
    """获取商品详情"""
    product = next((p for p in products_db if p["id"] == product_id), None)
    
    if not product:
        return jsonify({"success": False, "error": "商品不存在"}), 404
    
    return jsonify({
        "success": True,
        "data": product
    })


@app.route("/api/products/recommend", methods=["POST"])
def recommend_products():
    """
    根据体质推荐商品
    
    请求体：
    {
        "constitution": "湿热质",
        "limit": 3
    }
    """
    data = request.get_json()
    constitution = data.get("constitution", "")
    limit = data.get("limit", 3)
    
    # 匹配适合该体质的商品
    matched = [p for p in products_db if constitution in p.get("suitable_constitutions", [])]
    
    # 按销量排序
    matched.sort(key=lambda x: x["sales"], reverse=True)
    
    return jsonify({
        "success": True,
        "data": {
            "constitution": constitution,
            "recommendations": matched[:limit]
        }
    })


# ============ 对话式问诊接口 ============

@app.route("/api/dialogue/start", methods=["POST"])
def dialogue_start():
    """
    开始新的对话式问诊会话
    
    响应：
    {
        "success": true,
        "data": {
            "session_id": "dialogue_xxx",
            "bot_response": "您好！我是小神农AI助手...",
            "phase": "greeting",
            "suggested_questions": ["我最近头痛发热", "失眠多梦"],
            "progress_percent": 0
        }
    }
    """
    try:
        dialogue_engine = get_dialogue_engine_lazy()
        
        # 可选：登录用户（body 传 user_id 或 Authorization token），预载病历
        data = request.get_json(silent=True) or {}
        user_id = data.get("user_id", "")
        if not user_id:
            from auth_service import resolve_token
            auth = request.headers.get("Authorization", "")
            token = auth[7:].strip() if auth.startswith("Bearer ") else request.headers.get("X-User-Token", "")
            sess = resolve_token(token) if token else None
            if sess and sess["role"] == "user":
                user_id = sess["user_id"]
        
        session_id = dialogue_engine.create_session(user_id=user_id or None)
        
        # 模拟第一轮（问候语）
        result = dialogue_engine.process_turn(session_id, "")
        
        return jsonify({
            "success": True,
            "data": {
                "session_id": session_id,
                "user_id": user_id or None,
                "bot_response": result["bot_response"],
                "phase": result["phase"],
                "suggested_questions": result["suggested_questions"],
                "progress_percent": result["progress_percent"],
                "collected_symptoms": result["collected_symptoms"],
                "thinking_steps": result["thinking_steps"],
            }
        })
    
    except Exception as e:
        print(f"[API] 对话启动错误: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/dialogue/turn", methods=["POST"])
def dialogue_turn():
    """
    对话式问诊 - 处理一轮对话
    
    请求体：
    {
        "session_id": "dialogue_xxx",
        "user_input": "我最近头痛发热"
    }
    
    响应：
    {
        "success": true,
        "data": {
            "session_id": "dialogue_xxx",
            "phase": "collecting",
            "bot_response": "我注意到您提到了头痛、发热...",
            "collected_symptoms": [{"id": "SN-TB-S-001", "name": "头痛"}],
            "symptom_count": 2,
            "is_ready_for_diagnosis": false,
            "suggested_questions": ["还有其他不舒服吗？"],
            "progress_percent": 66,
            "thinking_steps": [...]
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or "session_id" not in data or "user_input" not in data:
            return jsonify({
                "success": False,
                "error": "缺少session_id或user_input"
            }), 400
        
        session_id = data["session_id"]
        user_input = data["user_input"]
        
        # 处理对话轮次
        dialogue_engine = get_dialogue_engine_lazy()
        result = dialogue_engine.process_turn(session_id, user_input)
        
        # 如果准备辨证，调用RAG引擎
        diagnosis_result = None
        if result["is_ready_for_diagnosis"] and result["diagnosis_query"]:
            print(f"[API] 对话达到辨证条件，触发辨证: {result['diagnosis_query']}")
            diag = rag_engine.diagnose(result["diagnosis_query"], llm_client)
            diagnosis_result = format_diagnosis_result(diag)
            # 保存快照到会话，供「转医馆审核开方」使用（服务端可信来源）
            sess_state = dialogue_engine.get_session(session_id)
            if sess_state is not None:
                sess_state.last_diagnosis = diagnosis_result
        
        # 登录用户：问诊完成写回一条就诊病历（M3）
        visit_emr_id = None
        if diagnosis_result and result.get("user_id"):
            try:
                from emr_service import add_visit
                symptom_names = "、".join(s["name"] for s in result["collected_symptoms"])
                visit_emr_id = add_visit(
                    user_id=result["user_id"],
                    chief_complaint=result.get("first_complaint") or symptom_names,
                    present_illness=f"共问诊{result['turn_count']}轮，收集症状：{symptom_names}",
                    ai_diagnosis=diagnosis_result,
                )
                print(f"[API] 就诊病历已写回: {visit_emr_id}")
            except Exception as e:
                print(f"[API] 病历写回失败（不影响辨证）: {e}")
        
        response_data = {
            "session_id": result["session_id"],
            "phase": result["phase"],
            "bot_response": result["bot_response"],
            "collected_symptoms": result["collected_symptoms"],
            "symptom_count": result["symptom_count"],
            "is_ready_for_diagnosis": result["is_ready_for_diagnosis"],
            "suggested_questions": result["suggested_questions"],
            "progress_percent": result["progress_percent"],
            "turn_count": result["turn_count"],
            "thinking_steps": result["thinking_steps"],
        }
        
        if diagnosis_result:
            response_data["diagnosis_result"] = diagnosis_result
        if visit_emr_id:
            response_data["visit_emr_id"] = visit_emr_id
        
        return jsonify({
            "success": True,
            "data": response_data
        })
    
    except Exception as e:
        print(f"[API] 对话处理错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/dialogue/<session_id>", methods=["GET"])
def dialogue_status(session_id):
    """获取对话会话状态"""
    try:
        dialogue_engine = get_dialogue_engine_lazy()
        summary = dialogue_engine.get_session_summary(session_id)
        if not summary:
            return jsonify({"success": False, "error": "会话不存在"}), 404
        
        return jsonify({
            "success": True,
            "data": summary
        })
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============ 多Agent系统接口 ============

@app.route("/api/agents/stats", methods=["GET"])
def agents_stats():
    """获取所有Agent统计信息"""
    try:
        agent_coordinator = get_agent_coordinator_lazy()
        stats = agent_coordinator.get_all_stats()
        return jsonify({
            "success": True,
            "data": stats
        })
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/agents/run", methods=["POST"])
def agents_run():
    """
    运行Agent任务
    
    请求体：
    {
        "tasks": [
            {"agent": "drug", "params": {"drug_name": "麻黄"}},
            {"agent": "symptom", "params": {"symptom_name": "头痛", "body_part": "TB"}}
        ]
    }
    """
    try:
        data = request.get_json()
        tasks = data.get("tasks", [])
        
        if not tasks:
            return jsonify({"success": False, "error": "缺少任务列表"}), 400
        
        agent_coordinator = get_agent_coordinator_lazy()
        results = agent_coordinator.run_pipeline(tasks)
        
        return jsonify({
            "success": True,
            "data": {
                "results": results,
                "total": len(results),
                "success_count": sum(1 for r in results if r.get("success"))
            }
        })
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/agents/analyze", methods=["POST"])
def agents_analyze():
    """
    Agent 综合分析接口（前端兼容）
    根据用户输入，自动匹配症状/药物/方剂，并调用对应 Agent 生成结构化分析。
    """
    try:
        data = request.get_json() or {}
        query = data.get("query", "")

        if not query:
            return jsonify({"success": False, "error": "缺少query"}), 400

        # 1. 先用 RAG 检索相关上下文
        chunks = rag_engine.retrieve(query, top_k=8)
        retrieved = [
            {
                "text": c.text,
                "source_book": c.source_book,
                "source_section": c.source_section,
                "score": round(c.score, 4)
            }
            for c in chunks
        ]

        # 2. 从知识库匹配症状、药物、方剂
        kb = get_kb()
        matched_symptoms, matched_drugs, matched_formulas = [], [], []
        if kb:
            try:
                matched_symptoms = find_symptoms_by_text(query) or []
                matched_drugs = kb.find_drugs_by_text(query) or []
                matched_formulas = kb.find_formulas_by_text(query) or []
            except Exception as e:
                print(f"[API] Agent分析知识库匹配失败: {e}")

        # 3. 构建 Agent 任务：对最相关的症状/药物/方剂各运行一个 Agent
        tasks = []
        if matched_symptoms:
            s = matched_symptoms[0]
            tasks.append({"agent": "symptom", "params": {"symptom_name": s.get("name", query), "body_part": "QT", "category": "Z"}})
        if matched_drugs:
            d = matched_drugs[0]
            tasks.append({"agent": "drug", "params": {"drug_name": d.get("name", query)}})
        if matched_formulas:
            f = matched_formulas[0]
            tasks.append({"agent": "formula", "params": {"formula_name": f.get("name", query)}})

        # 如果什么都没匹配到，至少运行一个 symptom agent 兜底
        if not tasks:
            tasks.append({"agent": "symptom", "params": {"symptom_name": query, "body_part": "QT", "category": "Z"}})

        # 4. 运行 Agent 流水线
        agent_coordinator = get_agent_coordinator_lazy()
        agent_results = agent_coordinator.run_pipeline(tasks)

        # 5. 使用 Yunwu LLM 生成最终综合分析
        sources_text = "\n".join(
            f"[出处：《{r.get('source_book', '未知')}》·{r.get('source_section', '')}] {r.get('text', '')}"
            for r in retrieved[:5]
        )

        agent_summary = []
        for r in agent_results:
            if r.get("success"):
                result = r.get("result", {})
                name = result.get("name") or result.get("symptom_name") or result.get("formula_name") or result.get("drug_name") or "未知"
                agent_summary.append(f"- {r.get('agent')}：{name}")

        final_prompt = f"""你是小神农中医AI，基于以下检索到的权威资料，对用户问题进行简明分析。

用户输入：{query}

参考资料：
{sources_text}

Agent分析摘要：
{chr(10).join(agent_summary) if agent_summary else '（未触发Agent）'}

请输出：
1. 核心证候/药物/方剂判断
2. 关键调理建议（3-5条）
3. 注意事项与禁忌
要求言简意赅，只基于参考资料，不要编造。"""

        final_analysis = llm_client.generate(final_prompt, temperature=0.3, max_tokens=1500)

        return jsonify({
            "success": True,
            "data": {
                "query": query,
                "analysis": final_analysis,
                "retrieved_sources": retrieved,
                "matched_symptoms": [{"id": s.get("id"), "name": s.get("name")} for s in matched_symptoms[:5]],
                "matched_drugs": [{"id": d.get("id"), "name": d.get("name")} for d in matched_drugs[:5]],
                "matched_formulas": [{"id": f.get("id"), "name": f.get("name")} for f in matched_formulas[:5]],
                "agent_results": agent_results,
                "model": llm_provider
            }
        })

    except Exception as e:
        print(f"[API] Agent分析错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


# ============ 后台管理系统接口 ============

@app.route("/api/admin/auth", methods=["POST"])
def admin_auth():
    """后台登录验证"""
    try:
        data = request.get_json() or {}
        token = data.get("token", "")
        if token == ADMIN_TOKEN:
            return jsonify({
                "success": True,
                "data": {
                    "authenticated": True,
                    "expires_at": (datetime.now().timestamp() + 86400) * 1000
                }
            })
        return jsonify({"success": False, "error": "管理令牌错误"}), 401
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/admin/stats", methods=["GET"])
@require_admin
def admin_stats():
    """后台首页统计数据"""
    try:
        from symptom_codes import SYMPTOM_MAP, BODY_PARTS, CATEGORY_CODES
        from syndrome_db import SYNDROME_DATABASE
        from drug_formula_db import FORMULA_DATABASE, DRUG_DATABASE, DRUG_CATEGORIES
        from contraindication_db import RULE_GROUP_CODES
        
        rag_stats = rag_engine.get_stats()
        
        # 统计对话会话
        dialogue_engine = get_dialogue_engine_lazy()
        session_count = len(dialogue_engine.sessions) if dialogue_engine else 0
        
        # 统计用户/医馆/订单/处方（SQLite 持久层，P4）
        from db import get_conn as _get_stats_conn
        _conn = _get_stats_conn()
        try:
            user_count = _conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
            clinic_total = _conn.execute("SELECT COUNT(*) c FROM clinics").fetchone()["c"]
            clinic_pending = _conn.execute("SELECT COUNT(*) c FROM clinics WHERE status='pending'").fetchone()["c"]
            order_total = _conn.execute("SELECT COUNT(*) c FROM orders").fetchone()["c"]
            rx_total = _conn.execute("SELECT COUNT(*) c FROM prescriptions").fetchone()["c"]
            rx_pending = _conn.execute("SELECT COUNT(*) c FROM prescriptions WHERE status='pending_review'").fetchone()["c"]
        finally:
            _conn.close()
        
        return jsonify({
            "success": True,
            "data": {
                "symptoms": {"total": len(SYMPTOM_MAP), "body_parts": len(BODY_PARTS), "categories": len(CATEGORY_CODES)},
                "syndromes": {"total": len(SYNDROME_DATABASE)},
                "formulas": {"total": len(FORMULA_DATABASE)},
                "drugs": {"total": len(DRUG_DATABASE), "categories": len(DRUG_CATEGORIES)},
                "knowledge": rag_stats,
                "sessions": {"active": session_count},
                "users": {"total": user_count},
                "clinics": {"total": clinic_total, "pending": clinic_pending},
                "orders": {"total": order_total},
                "prescriptions": {"total": rx_total, "pending_review": rx_pending},
                "rules": {"total": sum(len(rules) for rules in RULE_GROUP_CODES.values()) if isinstance(RULE_GROUP_CODES, dict) else 0},
                "timestamp": datetime.now().isoformat()
            }
        })
    except Exception as e:
        print(f"[Admin] 统计错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/admin/symptoms", methods=["GET"])
@require_admin
def admin_symptoms():
    """症状列表"""
    try:
        from symptom_codes import SYMPTOM_MAP, BODY_PARTS, CATEGORY_CODES
        
        keyword = request.args.get("keyword", "").strip()
        body_part = request.args.get("body_part", "").strip()
        category = request.args.get("category", "").strip()
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))
        
        items = []
        for sid, info in SYMPTOM_MAP.items():
            parts = sid.split("-")
            bp_code = parts[1] if len(parts) > 1 else ""
            cat_code = parts[2] if len(parts) > 2 else ""
            
            if keyword and keyword not in info.get("name", "") and keyword not in ",".join(info.get("aliases", [])):
                continue
            if body_part and bp_code != body_part:
                continue
            if category and cat_code != category:
                continue
            
            items.append({
                "id": sid,
                "name": info.get("name", ""),
                "aliases": info.get("aliases", []),
                "body_part": BODY_PARTS.get(bp_code, bp_code),
                "category": CATEGORY_CODES.get(cat_code, cat_code),
                "classic_refs": info.get("classic_refs", [])
            })
        
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        
        return jsonify({
            "success": True,
            "data": {
                "items": items[start:end],
                "total": total,
                "page": page,
                "page_size": page_size,
                "filters": {
                    "body_parts": [{"code": k, "name": v} for k, v in BODY_PARTS.items()],
                    "categories": [{"code": k, "name": v} for k, v in CATEGORY_CODES.items()]
                }
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/admin/syndromes", methods=["GET"])
@require_admin
def admin_syndromes():
    """证型列表"""
    try:
        from syndrome_db import SYNDROME_DATABASE
        
        keyword = request.args.get("keyword", "").strip()
        system = request.args.get("system", "").strip()
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))
        
        items = []
        systems = set()
        for sid, info in SYNDROME_DATABASE.items():
            sys_name = info.get("system", "")
            systems.add(sys_name)
            
            if keyword and keyword not in info.get("name", "") and keyword not in str(info):
                continue
            if system and sys_name != system:
                continue
            
            items.append({
                "id": sid,
                "name": info.get("name", ""),
                "system": sys_name,
                "pathogenesis": info.get("pathogenesis", "")[:80],
                "treatment_principle": info.get("treatment_principle", "")[:80],
                "main_formula": info.get("main_formula", {}),
                "severity": info.get("severity", ""),
                "source": info.get("source", "")
            })
        
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        
        return jsonify({
            "success": True,
            "data": {
                "items": items[start:end],
                "total": total,
                "page": page,
                "page_size": page_size,
                "filters": {
                    "systems": sorted(list(systems))
                }
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/admin/formulas", methods=["GET"])
@require_admin
def admin_formulas():
    """方剂列表"""
    try:
        from drug_formula_db import FORMULA_DATABASE
        
        keyword = request.args.get("keyword", "").strip()
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))
        
        items = []
        for fid, info in FORMULA_DATABASE.items():
            if keyword and keyword not in info.get("name", "") and keyword not in str(info):
                continue
            
            items.append({
                "id": fid,
                "name": info.get("name", ""),
                "source": info.get("source", ""),
                "indications": info.get("indications", []),
                "composition": info.get("composition", []),
                "effects": info.get("effects", "")[:100],
                "contraindications": info.get("contraindications", []),
                "symptom_count": len(info.get("indications", []))
            })
        
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        
        return jsonify({
            "success": True,
            "data": {
                "items": items[start:end],
                "total": total,
                "page": page,
                "page_size": page_size
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/admin/drugs", methods=["GET"])
@require_admin
def admin_drugs():
    """药物列表"""
    try:
        from drug_formula_db import DRUG_DATABASE, DRUG_CATEGORIES
        
        keyword = request.args.get("keyword", "").strip()
        category = request.args.get("category", "").strip()
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))
        
        items = []
        for did, info in DRUG_DATABASE.items():
            cat_code = did.split("-")[1] if len(did.split("-")) > 1 else ""
            
            if keyword and keyword not in info.get("name", "") and keyword not in str(info):
                continue
            if category and cat_code != category:
                continue
            
            props = info.get("properties", {})
            items.append({
                "id": did,
                "name": info.get("name", ""),
                "category": DRUG_CATEGORIES.get(cat_code, cat_code),
                "properties": props,
                "nature": props.get("nature", ""),
                "taste": props.get("taste", ""),
                "meridian": props.get("meridian", ""),
                "contraindications": info.get("contraindications", []),
                "indication_count": len(info.get("indications", []))
            })
        
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        
        return jsonify({
            "success": True,
            "data": {
                "items": items[start:end],
                "total": total,
                "page": page,
                "page_size": page_size,
                "filters": {
                    "categories": [{"code": k, "name": v} for k, v in DRUG_CATEGORIES.items()]
                }
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/admin/sessions", methods=["GET"])
@require_admin
def admin_sessions():
    """对话会话列表"""
    try:
        dialogue_engine = get_dialogue_engine_lazy()
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))
        
        items = []
        for sid, state in dialogue_engine.sessions.items():
            items.append({
                "session_id": sid,
                "phase": state.phase.value if state.phase else "unknown",
                "turn_count": state.turn_count,
                "symptom_count": len(state.collected_symptoms),
                "created_at": state.created_at,
                "last_activity": state.last_activity,
                "diagnosis_triggered": state.diagnosis_triggered,
                "user_profile": state.user_profile
            })
        
        # 按最后活动时间倒序
        items.sort(key=lambda x: x["last_activity"], reverse=True)
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        
        return jsonify({
            "success": True,
            "data": {
                "items": items[start:end],
                "total": total,
                "page": page,
                "page_size": page_size
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/admin/sessions/<session_id>", methods=["GET"])
@require_admin
def admin_session_detail(session_id):
    """对话会话详情"""
    try:
        dialogue_engine = get_dialogue_engine_lazy()
        state = dialogue_engine.sessions.get(session_id)
        if not state:
            return jsonify({"success": False, "error": "会话不存在"}), 404
        
        summary = dialogue_engine.get_session_summary(session_id)
        return jsonify({
            "success": True,
            "data": summary
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/admin/logs", methods=["GET"])
@require_admin
def admin_logs():
    """查看服务端日志"""
    try:
        log_file = request.args.get("file", "api_server.log")
        lines = int(request.args.get("lines", 100))
        
        # 限制可读取的日志文件，防止目录遍历
        allowed_logs = ["api_server.log", "api.log", "frontend.log"]
        if log_file not in allowed_logs:
            return jsonify({"success": False, "error": "不允许读取该日志文件"}), 400
        
        log_path = os.path.join(BASE_DIR, log_file)
        if not os.path.exists(log_path):
            return jsonify({"success": True, "data": {"lines": [], "file": log_file}})
        
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
        
        return jsonify({
            "success": True,
            "data": {
                "file": log_file,
                "total": len(all_lines),
                "lines": [line.rstrip() for line in all_lines[-lines:]]
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/admin/system", methods=["GET"])
@require_admin
def admin_system_info():
    """系统信息"""
    try:
        import platform
        
        return jsonify({
            "success": True,
            "data": {
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "llm_provider": llm_provider,
                "admin_token_configured": ADMIN_TOKEN != "xiaoshennong-admin",
                "data_dir": DATA_DIR,
                "timestamp": datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/kg/graph", methods=["GET"])
def kg_graph():
    """知识图谱数据（供前端 kg_visual.html 使用）"""
    try:
        graph_path = os.path.join(DATA_DIR, "kg_graph.json")
        if os.path.exists(graph_path):
            with open(graph_path, "r", encoding="utf-8") as f:
                graph_data = json.load(f)
            return jsonify({"success": True, "data": graph_data})
        return jsonify({"success": False, "error": "知识图谱文件不存在"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/knowledge/reset", methods=["POST"])
def reset_knowledge():
    """
    重置知识库（删除所有数据）
    警告：此操作不可恢复！
    """
    try:
        collection = rag_engine._get_collection()
        count = collection.count()
        
        # 获取所有ID并删除
        if count > 0:
            all_data = collection.get(include=[])
            all_ids = all_data['ids']
            # 分批删除
            batch_size = 100
            for i in range(0, len(all_ids), batch_size):
                batch = all_ids[i:i+batch_size]
                collection.delete(ids=batch)
        
        return jsonify({
            "success": True,
            "data": {
                "deleted_count": count,
                "message": "知识库已重置"
            }
        })
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============ 错误处理 ============

@app.errorhandler(404)
def not_found(e):
    return jsonify({"success": False, "error": "接口不存在"}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"success": False, "error": "服务器内部错误"}), 500


# ============ 启动 ============

if __name__ == "__main__":
    # 自动导入示例数据（如果知识库为空）
    if rag_engine.get_stats()["total_documents"] == 0:
        print("[API] 知识库为空，自动导入示例数据...")
        from data_pipeline import create_sample_data
        create_sample_data()
        # 仅导入 sample 数据，避免 raw 目录下大量 bulk 生成文件导致启动过慢
        sample_files = ["shanghanlun.json", "huangdi_neijing.json", "formulas.json"]
        pipeline = get_data_pipeline()
        for fname in sample_files:
            fpath = os.path.join(DATA_DIR, "raw", fname)
            if os.path.exists(fpath):
                try:
                    docs = pipeline.process_json_file(fpath)
                    if docs:
                        rag_engine.add_documents(docs)
                        print(f"[API] 导入 {fname}: {len(docs)} 条")
                except Exception as e:
                    print(f"[API] 导入 {fname} 失败: {e}")
    
    port = int(os.getenv("PORT", 5001))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    
    print(f"[API] 启动服务，端口: {port}, 调试模式: {debug}")
    app.run(host="0.0.0.0", port=port, debug=debug)
