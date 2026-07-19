# 小神农中医AI - 项目状态 v4.1

## 已完成

### 设计系统（2026-07-19 P1-P3）
- `frontend/assets/xsn-theme.css`: 设计 token（宣纸/朱砂/玉绿/鎏金）+ 动效 token（临界阻尼曲线、时长档位）+ 组件（印章/按钮/徽章/卡片/材质栏/规范弹窗）+ reduced-motion 全局降级
- `frontend/assets/xsn-motion.js`: vanilla 动效引擎（reveal/counter/SVG 描边/视差/XSNModal 规范弹窗：触发点锚定、materialize、进出同路）
- `frontend/DESIGN.md`: 动效规约（蒸馏 emilkowalski/skills apple-design，本土化：中文大标题加宽字距、emoji 禁令）
- 全站 7 个页面全部接入，零彩色 emoji（test_ui.html 约 50 处、kg_visual 5 处已清理）

### 主页（2026-07-19 P2）
- `frontend/home.html`「本草长卷」：吸顶半透明材质 nav、三层 SVG 山水视差 Hero、竖排文字、slogan「古有神农尝百草，今有小神农辩百症」、粘性滚动品牌故事三段、核心能力四卡、数字滚动计数、SVG 墨线描边问诊流程、卷轴医馆入驻、合规页脚；32KB 零外部图片，reduced-motion 全降级

### 平台后台（2026-07-19 P4）
- `GET /api/admin/users`（分页+脱敏+病历/订单数）、`GET /api/admin/orders`（状态/类型过滤）、`GET /api/admin/clinics/<id>/verifications`
- `/api/admin/stats` 扩展：users/clinics(pending)/orders/prescriptions(pending_review)
- admin.html 新增：医馆核验（过滤+核验/冻结+CV 记录）、用户管理（分页）、订单总览（过滤+分页）、Dashboard 四张新统计卡

### 核心系统
- RAG引擎 v2.2: 双源验证+批判性思维+副作用检测
- 古籍知识库: 125,005 条条文已导入 Chroma（data/chroma_db_v2，384 维），含 classical_texts 全量 125 个批次
- 词法检索引擎: 无嵌入主路（别名表+词典+jieba+SQLite 元数据打分），修复英文向量模型中文退化导致的语义搜索失效；LLM 改写仅兜底且结果缓存。古籍条文同步存 SQLite classical_texts 表（125,000 条）
- 对话式问诊引擎 v2: 真医生式问诊——基本资料(年龄/性别)→症状收集→过敏史/用药史→鉴别→辨证；信息完整度评分触发；支持"直接辨证"快速通道；登录用户病历预载、辨证结果写回病历
- 多Agent系统: 7个Agent（药物/症状/方剂/副作用/患者/共现/聚类），全部接入 Yunwu API，每个 Agent 配备专业中医 skill prompt
- LLM 统一入口: 所有 LLM 调用（辨证/Agent/搜索/爬虫）均走 yunwu.ai
- 网络爬虫: Wikipedia+Baidu Baike真实数据爬取
- 编码体系: 282症状SN编码+28证型SY编码+禁忌规则库
- 口语化症状别名: 为胃脘痛/腹胀/食欲不振补充“胃不舒服、胃难受、没胃口”等日常表达别名

### 账号 / 病历 / 医馆 / 订单（SQLite 持久化 data/xiaoshennong.db）
- 账号体系: 手机号锚点+账密+短信验证码（开发模式 dev_code；预留阿里云 SMS）；token 会话 7 天；密码 werkzeug 哈希；手机号展示脱敏
- 电子病历 EMR: 健康档案（身高体重/血型/家族史/既往史/过敏史/用药史/月经婚育史）+ 每次问诊自动写就诊记录
- 医馆体系: 入驻申请（限权开通：可登录后台但审核/接单锁定）→ 平台核验解锁（CV 编号留痕）→ 药方审核（通过可加注加减方/驳回填理由）→ 订单履约（邮寄/自取、代煎）
- 订单体系: 处方线（RX 审核通过才可下单）+ 商城线（服务端按商品价重算金额）；order_events 全链留痕
- 独立编号: U/EMR/MC/CA/RX/ORD/CV-日期-序号，预留 hash 字段供区块链存证
- 商城: 药食同源养生品（合规文案标注）；中药材原材料待二期"医馆货架"

### API接口
- POST /api/health - 健康检查
- POST /api/diagnosis - 快速辨证
- POST /api/diagnosis/stream - 流式辨证（SSE）
- POST /api/dialogue/start - 开始对话（支持 token 预载病历）
- POST /api/dialogue/turn - 对话轮次（辨证完成自动写病历）
- POST /api/retrieve - 古籍检索（词法主路）
- POST /api/semantic/search - 语义搜索（词法主路，分组输出）
- POST /api/auth/sms_code|register|login|login_sms|reset_password|logout；GET /api/auth/me；PUT /api/auth/profile
- GET /api/user/emr；GET|PUT /api/user/emr/profile
- POST /api/clinic/apply|login；GET /api/clinic/list|dashboard|profile|rx_queue|orders；POST /api/clinic/rx/<id>/review；POST /api/clinic/orders/<id>/status
- POST /api/rx/apply；GET /api/rx/list|/api/rx/<id>
- POST|GET /api/orders；GET /api/orders/<id>/events
- GET /api/admin/clinics；POST /api/admin/clinics/<id>/verify
- POST /api/agents/run - 运行Agent
- GET /api/agents/stats - Agent统计
- GET /api/admin/stats - 后台统计
- GET /api/admin/symptoms|syndromes|formulas|drugs - 知识库管理
- GET /api/admin/sessions - 会话管理
- GET /api/admin/logs - 日志查看

### 前端
- home.html: 品牌主页「本草长卷」（2026-07-19）：三层山水视差、粘性品牌故事、slogan「古有神农尝百草，今有小神农辩百症」、数字计数、SVG 描边流程、合规页脚
- index.html: 主对话界面（默认**对话问诊模式**：多轮真医生式问诊——问年龄性别→症状细节→过敏用药史→鉴别→辨证，可切快速辨证）；阶段印章标签、追问胶囊、鎏金进度条；登录预载病历、辨证写回病历并提示 EMR 编号；页头登录/注册、医馆入驻入口弹窗；个人中心（病历/处方/订单）；结果卡片「转医馆审核开方」（对话模式传 session_id 服务端快照，快速模式传 symptoms+advice）；商城 section；XSNModal 规范弹窗
- clinic.html: 医馆管理后台：登录/入驻、Dashboard、药方审核队列与详情、订单流转、医馆资料；pending 锁定态
- admin.html: 平台后台：知识库管理 + 医馆核验 + 用户管理 + 订单总览 + Dashboard 扩展统计
- test_ui_v3.html: 对话式问诊+打字机效果+分步思考展示
- test_ui.html: 综合测试平台
- kg_visual.html: 知识图谱可视化
- 微信小程序 pages/index & pages/diagnosis: 古风主题
- 全站统一：xsn-theme.css + xsn-motion.js + DESIGN.md 规约；零彩色 emoji（全部汉字印章）；favicon 统一朱砂印章

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
- [x] 导出 `merged_symptoms.json` 让 knowledge_base_v3 索引同步口语化别名（2026-07-19）
- [x] 语义搜索失效修复（2026-07-19，无嵌入词法检索替代英文向量模型）
- [x] 用户注册/登录（手机号+账密+短信）（2026-07-19）
- [x] 电子病历表 + AI 问诊读病历（2026-07-19）
- [x] 医馆入驻 + 管理后台 + 药方审核 + 订单（2026-07-19）
- [x] 品牌主页 home.html + 全站苹果动效×古风统一（2026-07-19）
- [ ] 主页改名换位（home.html → index.html 主页语义化，对话页改 chat.html，待主页定型后执行）
- [ ] 微信小程序完整开发（登录对接 /api/auth/login_sms；手机号一键授权需企业主体小程序）
- [ ] 真实短信通道（阿里云 SMS，需企业资质报备签名/模板）
- [ ] 在线支付（微信商户号，一期到店支付/货到付款）
- [ ] 区块链存证集成（编号与 hash 字段已预留）
- [ ] 更多数据源（中医世家解封后）
- [ ] 疗效反馈闭环系统
- [ ] 医馆SaaS系统深化（医馆货架-中药材销售、处方划价）
- [ ] 中文嵌入模型评估（bge-small-zh，作为词法检索的可选增强）

## 关键文件
- backend/api_server.py - API服务（含后台管理接口、OOM 延迟加载优化、强制 Yunwu 模式、auth/emr/clinic/orders 路由）
- backend/db.py - SQLite 持久化层（建表 + 编号发号器）
- backend/lexical_retriever.py - 无嵌入词法检索器（语义搜索主路）
- backend/auth_service.py - 账号认证（手机号锚点 + 会话）
- backend/sms_service.py - 短信验证码（可插拔，开发模式）
- backend/emr_service.py - 电子病历
- backend/clinic_service.py - 医馆/审核/订单状态机
- backend/rag_engine_v2.py - RAG引擎
- backend/dialogue_engine.py - 对话引擎（真医生式问诊）
- backend/multi_agent_system.py - 多Agent系统（已接入 Yunwu API）
- backend/agent_skills.py - Agent 专业 skill 与 Yunwu LLM 封装
- backend/llm_client_yunwu.py - 唯一 LLM 客户端入口（强制 yunwu.ai）
- backend/search_engine.py - 网络搜索（Yunwu AI 检索）
- backend/web_search_agent.py - 联网搜索 Agent（Yunwu AI）
- backend/web_crawler_v2.py - 网络爬虫
- backend/symptom_codes.py - 症状编号体系（含口语化别名）
- scripts/import_classical_texts.py - 古籍导入 Chroma（幂等、可断点续跑）
- scripts/import_classical_to_sqlite.py - 古籍导入 SQLite（词法检索数据源）
- scripts/regression_test.py - 关键 API 回归测试（33 项，--quick 跳过 LLM）
- frontend/index.html - 主站（对话/商城/个人中心）
- frontend/clinic.html - 医馆管理后台
- frontend/test_ui_v3.html - 对话式问诊测试页
- frontend/admin.html - 平台后台管理系统（古风 UI）
