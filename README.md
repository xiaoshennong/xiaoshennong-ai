# 小神农中医AI v3.0

> 国内首个基于权威古籍+真实疗效双数据库的中医产业可信数字化服务平台

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-green)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## 核心特性

- **零幻觉RAG引擎**：100%基于权威古籍数据，所有输出可溯源
- **对话式问诊**：AI主动追问，多轮收集症状，3轮触发辨证
- **批判性思维验证**：三阶九维可信度评估 + 症状共现分析 + 副作用检测
- **多Agent知识库扩展**：7个独立Agent自动联网爬取真实数据
- **完整编码体系**：282个症状编码 + 28个证型编码 + 禁忌规则库

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Web UI     │  │ 微信小程序  │  │  对话式问诊(v3.0)   │ │
│  │  test_ui    │  │  pages/     │  │  打字机效果+分步展示 │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      API服务层 (Flask)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ /api/health │  │ /api/diagnosis│  │ /api/dialogue/*   │ │
│  │ 健康检查    │  │ 快速辨证    │  │ 对话式问诊        │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ /api/retrieve│  │ /api/agents/*│  │ /api/knowledge/*   │ │
│  │ 古籍检索    │  │ Agent系统   │  │ 知识库管理        │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      RAG引擎 v2.2                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ 症状标准化  │  │ 古籍检索    │  │ 方剂药物匹配        │ │
│  │ SN编码体系  │  │ ChromaDB   │  │ 禁忌规则检查        │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ 证型识别    │  │ 批判性思维  │  │ 副作用检测          │ │
│  │ SY编码体系  │  │ 三阶九维    │  │ 时间窗口分析        │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    多Agent知识库扩展                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────────────┐│
│  │DrugAgent│ │Symptom  │ │Formula  │ │AdverseEvent        ││
│  │药物档案 │ │症状节点 │ │方剂档案 │ │副作用检测          ││
│  └─────────┘ └─────────┘ └─────────┘ └─────────────────────┘│
│  ┌─────────┐ ┌─────────┐ ┌─────────────────────────────────┐│
│  │Patient  │ │Cluster  │ │Cooccurrence                     ││
│  │患者档案 │ │聚类分析 │ │症状共现分析                      ││
│  └─────────┘ └─────────┘ └─────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    网络爬虫层                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Wikipedia   │  │ Baidu Baike │  │ 预留: 中医世家    │ │
│  │ 中文维基   │  │ 百度百科    │  │ 方剂网 知网       │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 快速开始

### 环境要求

- Python 3.12+
- pip

### 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 启动后端服务

```bash
cd backend
python api_server.py
```

服务将在 `http://127.0.0.1:5001` 启动

### 启动前端

```bash
# 方式1：直接打开HTML文件
cd frontend
open test_ui_v3.html

# 方式2：用Python启动HTTP服务器
cd frontend
python -m http.server 8080
# 然后访问 http://127.0.0.1:8080/test_ui_v3.html
```

## API接口文档

### 健康检查
```bash
curl http://127.0.0.1:5001/api/health
```

### 快速辨证
```bash
curl -X POST http://127.0.0.1:5001/api/diagnosis \
  -H "Content-Type: application/json" \
  -d '{"symptoms": "头痛发热，怕冷，没有汗"}'
```

### 对话式问诊 - 开始会话
```bash
curl -X POST http://127.0.0.1:5001/api/dialogue/start
```

### 对话式问诊 - 发送消息
```bash
curl -X POST http://127.0.0.1:5001/api/dialogue/turn \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your_session_id",
    "user_input": "我最近头痛"
  }'
```

### 古籍检索
```bash
curl -X POST http://127.0.0.1:5001/api/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "麻黄汤", "top_k": 5}'
```

### Agent系统 - 运行任务
```bash
curl -X POST http://127.0.0.1:5001/api/agents/run \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {"agent": "drug", "params": {"drug_name": "麻黄", "use_web_search": true}},
      {"agent": "formula", "params": {"formula_name": "麻黄汤", "use_web_search": true}}
    ]
  }'
```

### Agent系统 - 查看统计
```bash
curl http://127.0.0.1:5001/api/agents/stats
```

## 核心模块

| 模块 | 文件 | 功能 |
|------|------|------|
| RAG引擎 | `rag_engine_v2.py` | 双源验证+批判性思维+副作用检测 |
| 对话引擎 | `dialogue_engine.py` | 多轮问诊+智能追问+症状收集 |
| 多Agent系统 | `multi_agent_system.py` | 7个Agent知识库扩展 |
| 网络爬虫 | `web_crawler_v2.py` | Wikipedia+Baidu Baike爬取 |
| 症状编码 | `symptom_codes.py` | 282个症状SN编码体系 |
| 证型编码 | `syndrome_db.py` | 28个证型SY编码体系 |
| 禁忌规则 | `contraindication_db.py` | 十八反/十九畏/七情配伍 |
| 批判性思维 | `critical_thinking_engine.py` | 三阶九维评估+共现分析 |

## 编码体系

### 症状编码 (SN-XX-X-XXX)
- `SN-TB-S-001` = 头部-自觉-头痛
- `SN-QT-Z-001` = 全身-自觉-发热
- `SN-FB-T-003` = 腹部-体征-口苦

### 证型编码 (SY-XX-XXX)
- `SY-SH-001` = 伤寒-太阳表实证
- `SY-WB-001` = 温病-卫分证
- `SY-QX-001` = 气血-气虚证

### 药物编码 (DR-XXXX)
- `DR-0001` = 麻黄
- `DR-0002` = 桂枝

### 方剂编码 (FP-XXXX)
- `FP-0001` = 麻黄汤

## 对话式问诊流程

```
用户: "我最近头痛"
AI: "我注意到您提到了头痛。还有其他不舒服的地方吗？
    比如饮食、睡眠、大小便、精神状态等方面？"
    [进度: 33%]

用户: "还有发热，怕冷"
AI: "感谢您提供的信息！我已收集到您2个症状
    （头痛、发热、怕冷），现在为您进行AI辨证分析..."
    [进度: 100%]
    
→ 触发辨证 → 返回完整辨证报告
```

## 数据流

```
用户输入
  → 症状提取 (SN编码)
  → 古籍检索 (ChromaDB)
  → 方剂匹配 (FP编码)
  → 证型识别 (SY编码)
  → 禁忌检查 (RL编码)
  → 批判性思维验证
  → 副作用检测
  → LLM生成回答
  → 输出校验
  → 返回结果
```

## 配置

### LLM API配置

在 `backend/api_server.py` 中配置：

```python
# Yunwu AI (当前使用)
YUNWU_API_KEY = "your_key"
YUNWU_BASE_URL = "https://yunwu.ai/v1"

# 或 Kimi API
KIMI_API_KEY = "your_key"
KIMI_BASE_URL = "https://api.moonshot.cn/v1"
```

### 环境变量

```bash
export LLM_PROVIDER="yunwu"  # 或 kimi, deepseek, mock
export PORT=5001
export FLASK_DEBUG=false
```

## 项目结构

```
xiaoshennong-ai/
├── backend/                    # Python后端
│   ├── api_server.py          # Flask API服务
│   ├── rag_engine_v2.py       # RAG引擎 v2.2
│   ├── dialogue_engine.py     # 对话式问诊引擎
│   ├── multi_agent_system.py  # 多Agent系统
│   ├── web_crawler_v2.py      # 网络爬虫
│   ├── search_engine.py       # 搜索引擎
│   ├── critical_thinking_engine.py  # 批判性思维
│   ├── symptom_codes.py       # 症状编码
│   ├── syndrome_db.py         # 证型编码
│   ├── contraindication_db.py # 禁忌规则
│   ├── drug_formula_db.py     # 药物方剂库
│   ├── code_system.py         # 编码验证
│   ├── data_pipeline.py       # 数据管道
│   ├── llm_client*.py         # LLM客户端
│   ├── requirements.txt       # 依赖
│   └── data/                  # 数据目录
│       ├── chroma_db_v2/      # 向量数据库
│       ├── raw/               # 原始数据
│       └── processed/         # 处理后数据
├── frontend/                   # 前端
│   ├── test_ui_v3.html        # Web UI v3.0
│   ├── test_ui.html           # Web UI v2.0
│   ├── index.html             # 入口页面
│   └── pages/                 # 微信小程序
├── scripts/                    # 数据导入脚本
│   ├── import_classics.py
│   ├── import_data.py
│   └── ...
├── start.sh                    # Linux启动脚本
├── start.bat                   # Windows启动脚本
└── README.md                   # 本文档
```

## 开发计划

- [x] RAG引擎 v2.2（双源验证+批判性思维）
- [x] 对话式问诊引擎
- [x] 多Agent知识库扩展系统
- [x] 网络爬虫（Wikipedia+Baidu）
- [x] 症状/证型/药物编码体系
- [ ] 微信小程序完整开发
- [ ] 区块链存证集成
- [ ] 更多数据源（中医世家、知网）
- [ ] 疗效反馈闭环系统
- [ ] 医馆SaaS系统

## 贡献

欢迎提交Issue和PR！

## 许可证

MIT License

## 免责声明

本系统仅供学习和研究使用，不构成医疗建议。如有不适，请及时就医。

---

**小神农AI - 让中医更可信**
