# 小神农中医AI

国内首个基于权威古籍+真实疗效双数据库的中医产业可信数字化服务平台。

## 部署状态

- **服务器**: http://43.247.135.91
- **API健康检查**: http://43.247.135.91/api/health
- **测试UI**: http://43.247.135.91/test_ui_v3.html

## 功能特性

- ✅ RAG引擎 v2.0（all-MiniLM-L6-v2 嵌入模型）
- ✅ AI辨证（支持 Yunwu/Kimi/DeepSeek API）
- ✅ 副作用检测（基于症状共现分析）
- ✅ 经典古籍引用（黄帝内经、伤寒论等）
- ✅ 禁忌规则检查
- ✅ 多Agent系统（药物/症状/方剂/副作用/患者/共现/聚类）

## 快速开始

### 本地开发

```bash
# 安装依赖
pip install -r backend/requirements.txt

# 启动API服务
cd backend
python api_server.py

# 访问 http://localhost:5001/api/health
```

### 服务器部署

```bash
# 1. 克隆代码
git clone https://github.com/xiaoshennong/xiaoshennong-ai.git
cd xiaoshennong-ai

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的API Key

# 3. 使用虚拟环境部署（推荐）
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# 4. 启动服务
cd backend
python api_server.py
```

## 配置LLM API

支持以下LLM提供商：

| 提供商 | 环境变量 | 说明 |
|--------|----------|------|
| Yunwu AI | `YUNWU_API_KEY` | 推荐，OpenAI兼容 |
| Kimi | `KIMI_API_KEY` | Moonshot AI |
| DeepSeek | `DEEPSEEK_API_KEY` | 深度求索 |
| OpenAI | `OPENAI_API_KEY` | GPT系列 |

编辑 `.env` 文件配置你的API Key。

## 项目结构

```
xiaoshennong-ai/
├── backend/          # Python后端代码
│   ├── api_server.py           # Flask API服务
│   ├── rag_engine_v2.py        # RAG引擎v2.0
│   ├── dialogue_engine.py      # 对话式问诊
│   ├── multi_agent_system.py   # 多Agent系统
│   ├── critical_thinking_engine.py  # 批判性思维验证
│   ├── symptom_codes.py        # 症状编码体系
│   ├── syndrome_db.py          # 证型数据库
│   └── ...
├── frontend/         # 前端代码
├── data/             # 知识库数据
├── docker/           # Docker配置
├── nginx/            # Nginx配置
└── scripts/          # 部署脚本
```

## API接口

### 健康检查
```
GET /api/health
```

### AI辨证
```
POST /api/diagnosis
Content-Type: application/json

{
  "symptoms": "头痛发热，怕冷，没有汗"
}
```

### 症状列表
```
GET /api/symptoms
```

### 证型列表
```
GET /api/syndromes
```

## 技术栈

- **后端**: Python 3.10 + Flask + ChromaDB
- **AI模型**: all-MiniLM-L6-v2 (嵌入) + Yunwu/Kimi/DeepSeek (LLM)
- **前端**: HTML/JavaScript (微信小程序兼容)
- **部署**: Nginx + systemd + Python venv

## 核心数据

- 症状编码: 282个
- 证型编码: 28个
- 方剂: 23个
- 药物: 30个
- 古籍文档: 7个

## 许可证

MIT License
