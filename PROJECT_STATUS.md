# 小神农中医AI - 项目状态 v3.0

## 已完成

### 核心系统
- RAG引擎 v2.2: 双源验证+批判性思维+副作用检测
- 对话式问诊引擎: 多轮对话，3轮触发辨证
- 多Agent系统: 7个Agent（药物/症状/方剂/副作用/患者/共现/聚类）
- 网络爬虫: Wikipedia+Baidu Baike真实数据爬取
- 编码体系: 282症状SN编码+28证型SY编码+禁忌规则库

### API接口
- POST /api/health - 健康检查
- POST /api/diagnosis - 快速辨证
- POST /api/dialogue/start - 开始对话
- POST /api/dialogue/turn - 对话轮次
- POST /api/retrieve - 古籍检索
- POST /api/agents/run - 运行Agent
- GET /api/agents/stats - Agent统计

### 前端
- test_ui_v3.html: 对话式问诊+打字机效果+分步思考展示
- 支持模式切换: 对话问诊/快速辨证

## GitHub仓库
https://github.com/xiaoshennong/xiaoshennong-ai

## 启动命令
```bash
cd backend && python api_server.py
cd frontend && python -m http.server 8080
```

## 待办事项
- [ ] 更新LLM API key（当前Yunwu AI和Kimi都403）
- [ ] 微信小程序完整开发
- [ ] 区块链存证集成
- [ ] 更多数据源（中医世家解封后）
- [ ] 疗效反馈闭环系统
- [ ] 医馆SaaS系统

## 关键文件
- backend/api_server.py - API服务
- backend/rag_engine_v2.py - RAG引擎
- backend/dialogue_engine.py - 对话引擎
- backend/multi_agent_system.py - 多Agent系统
- backend/web_crawler_v2.py - 网络爬虫
- frontend/test_ui_v3.html - 前端UI
