#!/usr/bin/env python3
"""
小神农中医AI - Flask API服务
提供：AI辨证、知识检索、用户管理、订单接口
"""

import os
import json
import sys
import time
from datetime import datetime
from functools import wraps

# 强制禁用字节码缓存，确保加载最新代码
sys.dont_write_bytecode = True

from flask import Flask, request, jsonify, Response
from flask_cors import CORS

from rag_engine_v2 import XiaoShennongRAGv2, DiagnosisResult

# 优先使用Yunwu AI API（用户提供的API Key）
try:
    from llm_client_yunwu import get_llm_client, YunwuAIClient
    print("[API] 使用Yunwu AI客户端")
except ImportError:
    try:
        from llm_client_v3 import get_llm_client
        print("[API] 使用Kimi Code CLI客户端")
    except ImportError:
        try:
            from llm_client_v2 import get_llm_client
            print("[API] 使用新版LLM客户端（支持Kimi开放平台）")
        except ImportError:
            from llm_client import get_llm_client
            print("[API] 使用旧版LLM客户端")

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

# 初始化LLM客户端
# 优先级：Yunwu AI > Kimi Code CLI > Kimi开放平台 > DeepSeek > Mock
llm_provider = os.getenv("LLM_PROVIDER", "auto")

if llm_provider == "auto":
    # 自动检测：优先Yunwu AI（用户明确提供）
    try:
        from llm_client_yunwu import YunwuAIClient
        _temp_client = YunwuAIClient()
        if _temp_client.api_key:
            llm_provider = "yunwu"
            print("[API] 检测到Yunwu AI API Key，使用yunwu模式")
        else:
            raise Exception("No API key")
    except Exception:
        try:
            from llm_client_v3 import KimiCodeCLIClient
            _temp_client = KimiCodeCLIClient()
            if _temp_client.access_token:
                llm_provider = "kimi-code"
                print("[API] 检测到Kimi Code CLI已登录，使用kimi-code模式")
            else:
                raise Exception("No token")
        except Exception:
            if os.getenv("KIMI_API_KEY"):
                llm_provider = "kimi"
                print("[API] 检测到KIMI_API_KEY环境变量，使用kimi开放平台模式")
            elif os.getenv("DEEPSEEK_API_KEY"):
                llm_provider = "deepseek"
                print("[API] 检测到DEEPSEEK_API_KEY环境变量，使用deepseek模式")
            else:
                llm_provider = "mock"
                print("[API] 未检测到任何API Key，使用mock模式")

llm_client = get_llm_client(llm_provider)
print(f"[API] LLM客户端: {llm_provider}")

# 初始化数据管道
data_pipeline = DataPipeline()

# 导入新的知识库（延迟加载模式）
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

# 尝试预加载知识库
print("[API] 初始化大规模知识库...")
knowledge_base = get_kb()
if knowledge_base:
    print("[API] 大规模知识库预加载完成")
else:
    print("[API] 知识库预加载失败，将在首次请求时重试")

# 初始化对话式问诊引擎
print("[API] 初始化对话式问诊引擎...")
dialogue_engine = get_dialogue_engine()

# 初始化多Agent协调器
print("[API] 初始化多Agent系统...")
agent_coordinator = get_agent_coordinator(os.path.join(DATA_DIR, "agent_data"))

# 简单的内存用户存储（MVP阶段，生产环境应使用数据库）
users_db = {}
sessions_db = {}

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
        # 识别症状
        matched_symptoms = kb.find_symptoms_by_text(symptoms_text)
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
        if knowledge_base:
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
            if knowledge_base:
                formatted = enhance_diagnosis_with_kb(symptoms_text, formatted)

            # 发送思考步骤
            for step in formatted.get('thinking_process', []):
                payload = json.dumps({'type': 'thinking', 'data': step}, ensure_ascii=False)
                yield f"data: {payload}\n\n"

            # 用知识库把输入症状映射为结构化症状节点
            kb = get_kb()
            matched_symptoms = []
            if kb:
                try:
                    matched_symptoms = kb.find_symptoms_by_text(symptoms_text) or []
                except Exception as e:
                    print(f"[API] 流式症状映射失败: {e}")

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
                'advice': _strip_emojis(formatted.get('advice', ''))[:800],
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
        
        chunks = rag_engine.retrieve(query, top_k=top_k)
        
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
                "results": results,
                "total": len(results)
            }
        })
    
    except Exception as e:
        print(f"[API] 检索错误: {e}")
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
        
        count = data_pipeline.batch_import(rag_engine, data_dir)
        
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
            "total": len(products)
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
        session_id = dialogue_engine.create_session()
        
        # 模拟第一轮（问候语）
        result = dialogue_engine.process_turn(session_id, "")
        
        return jsonify({
            "success": True,
            "data": {
                "session_id": session_id,
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
        result = dialogue_engine.process_turn(session_id, user_input)
        
        # 如果准备辨证，调用RAG引擎
        diagnosis_result = None
        if result["is_ready_for_diagnosis"] and result["diagnosis_query"]:
            print(f"[API] 对话达到辨证条件，触发辨证: {result['diagnosis_query']}")
            diag = rag_engine.diagnose(result["diagnosis_query"], llm_client)
            diagnosis_result = format_diagnosis_result(diag)
        
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
        data_pipeline.batch_import(rag_engine, os.path.join(DATA_DIR, "raw"))
    
    port = int(os.getenv("PORT", 5001))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    
    print(f"[API] 启动服务，端口: {port}, 调试模式: {debug}")
    app.run(host="0.0.0.0", port=port, debug=debug)
