# 小神农中医AI - 项目状态 v3.0

## 已完成

### 核心系统
- RAG引擎 v2.2: 双源验证+批判性思维+副作用检测
- 对话式问诊引擎: 多轮对话，3轮触发辨证
- 多Agent系统: 7个Agent（药物/症状/方剂/副作用/患者/共现/聚类），全部接入 Yunwu API，每个 Agent 配备专业中医 skill prompt
- LLM 统一入口: 所有 LLM 调用（辨证/Agent/搜索/爬虫）均走 yunwu.ai
- 网络爬虫: Wikipedia+Baidu Baike真实数据爬取
- 编码体系: 282症状SN编码+28证型SY编码+禁忌规则库
- 口语化症状别名: 为胃脘痛/腹胀/食欲不振补充“胃不舒服、胃难受、没胃口”等日常表达别名

### API接口
- POST /api/health - 健康检查
- POST /api/diagnosis - 快速辨证
- POST /api/diagnosis/stream - 流式辨证（SSE）
- POST /api/dialogue/start - 开始对话
- POST /api/dialogue/turn - 对话轮次
- POST /api/retrieve - 古籍检索
- POST /api/agents/run - 运行Agent
- GET /api/agents/stats - Agent统计
- GET /api/admin/stats - 后台统计
- GET /api/admin/symptoms|syndromes|formulas|drugs - 知识库管理
- GET /api/admin/sessions - 会话管理
- GET /api/admin/logs - 日志查看

### 前端
- index.html: 主对话界面（古风宣纸/朱砂/墨绿/鎏金主题）
- test_ui_v3.html: 对话式问诊+打字机效果+分步思考展示（古风主题）
- test_ui.html: 综合测试平台（古风主题）
- kg_visual.html: 知识图谱可视化（古风主题）
- admin.html: 后台管理系统（古风主题）
- 微信小程序 pages/index & pages/diagnosis: 古风主题
- 支持模式切换: 对话问诊/快速辨证

## GitHub仓库
https://github.com/xiaoshennong/xiaoshennong-ai

## 启动命令
```bash
cd backend && python api_server.py
cd frontend && python -m http.server 8080
```

## 待办事项
- [x] 更新LLM API key（已迁移到 `.env`，代码不再硬编码）
- [x] 口语化症状别名匹配（胃不舒服/胃难受/没胃口等已可命中标准编号）
- [ ] 微信小程序完整开发
- [ ] 区块链存证集成
- [ ] 更多数据源（中医世家解封后）
- [ ] 疗效反馈闭环系统
- [ ] 医馆SaaS系统
- [ ] 导出 `merged_symptoms.json` 让 knowledge_base_v3 索引同步口语化别名

## 关键文件
- backend/api_server.py - API服务（含后台管理接口、OOM 延迟加载优化、强制 Yunwu 模式）
- backend/rag_engine_v2.py - RAG引擎
- backend/dialogue_engine.py - 对话引擎
- backend/multi_agent_system.py - 多Agent系统（已接入 Yunwu API）
- backend/agent_skills.py - Agent 专业 skill 与 Yunwu LLM 封装
- backend/llm_client_yunwu.py - 唯一 LLM 客户端入口（强制 yunwu.ai）
- backend/search_engine.py - 网络搜索（Yunwu AI 检索）
- backend/web_search_agent.py - 联网搜索 Agent（Yunwu AI）
- backend/web_crawler_v2.py - 网络爬虫
- backend/symptom_codes.py - 症状编号体系（含口语化别名）
- frontend/test_ui_v3.html - 前端UI
- frontend/admin.html - 后台管理系统（古风 UI）
