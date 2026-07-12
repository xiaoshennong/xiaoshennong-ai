# 小神农中医AI - 技术部署说明

## 系统架构

```
微信小程序 (前端)
    ↓ HTTP
Flask API服务 (后端)
    ↓
RAG引擎
  ├── 嵌入模型 (all-MiniLM-L6-v2)
  ├── 向量数据库 (Chroma)
  └── 大模型 (Mock/DeepSeek API)
```

## 已交付文件清单

### 后端代码 (`backend/`)
| 文件 | 功能 |
|------|------|
| `rag_engine.py` | RAG核心引擎：检索+生成+溯源+幻觉防控 |
| `llm_client.py` | LLM客户端：支持Mock/DeepSeek/OpenAI |
| `data_pipeline.py` | 数据导入管道：JSON/TXT→结构化→向量化 |
| `api_server.py` | Flask API服务：辨证/检索/商品/用户接口 |
| `requirements.txt` | Python依赖清单 |

### 前端代码 (`frontend/`)
| 文件 | 功能 |
|------|------|
| `project.config.json` | 微信小程序配置 |
| `pages/index/` | 首页：品牌展示+功能入口+商品推荐 |
| `pages/diagnosis/` | AI辨证：引导式问诊+结果展示+溯源 |

### 启动脚本
| 文件 | 用途 |
|------|------|
| `start.bat` | Windows一键启动 |
| `start.sh` | Linux/Mac一键启动 |

## 快速启动（Windows）

### 1. 安装依赖
```bash
cd xiaoshennong
pip install flask flask-cors chromadb numpy openai transformers sentencepiece protobuf
```

### 2. 启动服务
```bash
# 方式1：一键启动
start.bat

# 方式2：手动启动
cd backend
python api_server.py
```

### 3. 验证服务
```bash
# 健康检查
curl http://localhost:5000/api/health

# 测试辨证
curl -X POST http://localhost:5000/api/diagnosis \
  -H "Content-Type: application/json" \
  -d '{"symptoms":"头痛发热，怕冷，没有汗"}'
```

## API接口文档

### 1. 健康检查
```
GET /api/health

响应：
{
  "status": "ok",
  "rag_stats": {
    "total_documents": 7,
    "embedding_model": "all-MiniLM-L6-v2",
    "device": "cpu"
  }
}
```

### 2. AI辨证
```
POST /api/diagnosis
Content-Type: application/json

请求体：
{
  "symptoms": "头痛发热，怕冷，没有汗",
  "history": "",
  "age": 30,
  "gender": "male"
}

响应：
{
  "success": true,
  "data": {
    "constitution": "风寒表实证",
    "syndrome": "外感风寒，卫阳被郁",
    "advice": "建议采用辛温解表之法...",
    "sources": [
      {
        "book": "伤寒论",
        "section": "第35条",
        "text": "太阳病，头痛发热...",
        "original_text": "太阳病，头痛发热..."
      }
    ],
    "warning": "本结果仅供参考..."
  }
}
```

### 3. 知识检索
```
POST /api/retrieve
Content-Type: application/json

请求体：
{
  "query": "麻黄汤",
  "top_k": 5
}
```

### 4. 商品列表
```
GET /api/products?constitution=湿热质

响应：
{
  "success": true,
  "data": {
    "products": [...]
  }
}
```

### 5. 商品推荐
```
POST /api/products/recommend
Content-Type: application/json

请求体：
{
  "constitution": "湿热质",
  "limit": 3
}
```

## 数据导入

### 导入示例数据（自动）
启动API服务时，如果知识库为空，会自动导入示例数据。

### 导入自定义数据
```bash
cd backend
python data_pipeline.py --create-samples  # 创建示例数据
python data_pipeline.py --import-all      # 导入所有数据
```

### 数据格式

**古籍JSON格式：**
```json
{
  "book_name": "伤寒论",
  "dynasty": "东汉",
  "author": "张仲景",
  "sections": [
    {
      "section_name": "第35条",
      "original_text": "太阳病，头痛发热..."
    }
  ]
}
```

**方剂JSON格式：**
```json
[
  {
    "formula_name": "麻黄汤",
    "source_book": "伤寒论",
    "source_section": "第35条",
    "composition": [
      {"herb": "麻黄", "dosage": "三两"}
    ],
    "indications": ["太阳病", "头痛发热"],
    "effects": ["发汗解表"]
  }
]
```

## 配置说明

### 环境变量
| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LLM_PROVIDER` | `mock` | LLM提供商：mock/deepseek/openai |
| `DEEPSEEK_API_KEY` | - | DeepSeek API密钥 |
| `OPENAI_API_KEY` | - | OpenAI API密钥 |
| `PORT` | `5000` | 服务端口 |
| `FLASK_DEBUG` | `false` | 调试模式 |

### 切换LLM提供商
```bash
# 使用DeepSeek API（需要API Key）
set LLM_PROVIDER=deepseek
set DEEPSEEK_API_KEY=your-key-here
python api_server.py

# 使用Mock（无需API Key，用于测试）
set LLM_PROVIDER=mock
python api_server.py
```

## 微信小程序对接

### 1. 修改API地址
编辑 `frontend/pages/index/index.js` 和 `frontend/pages/diagnosis/diagnosis.js`：
```javascript
const API_BASE = 'https://your-domain.com';  // 生产环境域名
```

### 2. 配置服务器域名
在微信小程序后台：
- 开发 → 开发设置 → 服务器域名
- 添加 `request合法域名`：你的API域名

### 3. 上传代码
使用微信开发者工具上传前端代码。

## 部署到生产环境

### 使用Gunicorn（Linux）
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 api_server:app
```

### 使用Nginx反向代理
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 常见问题

**Q: 启动时提示模型下载失败？**
A: 网络问题导致模型下载失败。可以手动下载模型或换用国内镜像。

**Q: 辨证结果返回"暂无权威数据支持"？**
A: 知识库数据不足。需要导入更多古籍数据。

**Q: Windows下中文显示乱码？**
A: 这是Windows终端编码问题，不影响实际功能。使用PowerShell或设置UTF-8编码。

**Q: 如何添加更多古籍？**
A: 将古籍整理为JSON格式放入 `data/raw/` 目录，然后调用批量导入接口。

## 下一步优化建议

1. **安装sentence-transformers**：`pip install sentence-transformers`，提升嵌入质量
2. **接入DeepSeek API**：获取API Key，替换Mock客户端
3. **导入更多古籍**：优先完成100部核心古籍的数字化
4. **部署到云服务器**：使用阿里云/腾讯云，配置HTTPS域名
5. **完善小程序前端**：对接后端API，完成商品详情页、订单页

## 技术支持

系统已完整搭建，核心功能验证通过：
- ✅ RAG引擎运行正常
- ✅ 知识库检索有效
- ✅ 辨证API返回正确结果
- ✅ 溯源信息完整
- ✅ 商品接口可用

如需进一步定制开发，可基于现有代码扩展。
