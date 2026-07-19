# 小神农中医 AI — 会话上下文记忆

> 整理时间：2026-07-16  
> 状态：本地变更已整理，已按用户要求准备推送 GitHub；服务器部署仍待用户配合

---

## 1. 项目基本信息

| 项 | 内容 |
|---|---|
| 项目名 | 小神农中医 AI (`xiaoshennong-ai`) |
| GitHub | `xiaoshennong/xiaoshennong-ai` |
| 服务器 IP | `43.247.135.91` |
| 部署路径 | `/opt/xiaoshennong` |
| 后端入口 | `/opt/xiaoshennong/backend/api_server.py` |
| 前端入口 | `/opt/xiaoshennong/frontend/index.html` |
| 服务进程 | `/opt/xiaoshennong/venv/bin/python -B api_server.py` |
| 反向代理 | nginx 80 → 后端 5005 |

---

## 2. 已完成的工作

### 2.1 知识图谱构建
- 建立了六类实体编码体系：药物（DR）、症状（SN）、证型（SY）、方剂（FP）、禁忌规则（RL）、古籍条文（CL）。
- 实现了 v2.0 副作用辨别引擎：症状共现网络、患者档案、时间窗口分析、相似患者匹配。
- 使用多 Agent 并行生成了症状、方剂、副作用、患者、聚类、共现网络等数据。

### 2.2 部署
- 已部署到 `43.247.135.91`。
- 前端通过 nginx 或直连 `5005` 访问。

### 2.3 修复前端 `TypeError: Cannot read properties of undefined (reading 'symptoms')`
**根因**：`/api/diagnosis/stream` 返回的 `result` 数据是平铺字段，缺少前端期望的 `diagnosis` 包装和 `symptoms/formulas/acupoints/dietary/qigong/massage` 数组。

**修复提交**：`1690822`
- `backend/api_server.py`：新增/修正 `/api/diagnosis/stream`，返回结构化的 `data.diagnosis`。
- `frontend/index.html`：
  - `API_BASE` 改回空字符串，走 nginx 同源代理。
  - `showDiagnosisResult` 增加 `normalizeDiagnosis`，兼容旧版/精简版后端字段。

### 2.4 修复启动内存占用过高（OOM 优化）
**根因**：`api_server.py` 在启动时预加载了 `knowledge_base_v3`、对话引擎、多 Agent 协调器、数据管道等重组件，导致 baseline 内存过高，8G 服务器容易 OOM。

**变更文件**：`backend/api_server.py`（未提交）
- 移除 `knowledge_base` 强制预加载，恢复为首次请求时延迟加载。
- `DataPipeline`、`DialogueEngine`、`AgentCoordinator` 改为延迟加载单例。
- 保留 RAG 引擎和 LLM 客户端在启动时初始化（核心路径）。
- Windows 本地开发环境增加 stdout/stderr UTF-8 适配，避免含生僻字符的日志打印崩溃。

**本地验证**：
- `GET /api/health` ✅
- `POST /api/dialogue/start` ✅（触发对话引擎延迟加载）
- `GET /api/agents/stats` ✅（触发 Agent 协调器延迟加载）
- 启动日志不再出现“初始化大规模知识库”“初始化对话式问诊引擎”“初始化多 Agent 系统”等预加载输出。

### 2.5 新增后台管理系统（古风 UI）
**变更文件**：
- `backend/api_server.py`：新增 `/api/admin/*` 系列接口，包含统计、症状/证型/方剂/药物管理、会话管理、日志查看、系统信息。
- `frontend/admin.html`：全新后台管理前端，采用古风宣纸、朱砂、墨绿、鎏金配色，支持登录、Dashboard、数据列表、筛选分页、详情弹窗。

**本地验证**：
- `POST /api/admin/auth` ✅
- `GET /api/admin/stats` ✅
- `GET /api/admin/symptoms|syndromes|formulas|drugs` ✅
- `GET /api/admin/sessions` ✅
- `GET /api/admin/logs` ✅
- `GET /api/admin/system` ✅
- `frontend/admin.html` 通过 `python -m http.server 8080` 可正常访问 ✅

### 2.6 修复本地运行时前端 501 / 后端 500 错误
**问题 1：前端请求命中静态文件服务器**
- `index.html` / `admin.html` 原 `API_BASE = ''`，本地用 `python -m http.server 8080` 启动前端时，POST 请求会发给 8080 的静态服务器，返回 `501 Unsupported method`；直接双击 HTML 文件（`file://` 协议）也会失败。
- 已改为更健壮的动态判断：
  - `file://` 协议 → `http://localhost:5001`
  - `localhost` / `127.0.0.1` 且非 5001 端口 → `http://localhost:5001`
  - 生产 nginx 环境 → 走相对路径
  - 支持 `localStorage.setItem('xsn_api_base', 'http://...')` 手动覆盖

**问题 2：ChromaDB 嵌入维度不一致导致辨证 500**
- 本地 `data/chroma_db_v2` 中的文档为 128 维（旧 fallback 编码生成），而当前 `all-MiniLM-L6-v2` 输出 384 维，查询时报 `Collection expecting embedding with dimension of 128, got 384`。
- 已在 `rag_engine_v2.py` 启动时增加维度校验：若现有文档维度与当前模型不一致，自动删除旧集合并重建。
- 已清理本地旧库，新库维度为 384，辨证接口可正常返回 SSE 流。

**问题 3：启动时导入全部 raw 数据过慢**
- `api_server.py` 启动时原 `batch_import(data/raw)` 会处理大量 bulk 生成文件，导致启动超时。
- 已改为仅自动导入 `create_sample_data()` 生成的示例文件（`shanghanlun.json` / `huangdi_neijing.json` / `formulas.json`），启动时间大幅缩短。

**本地验证**：
- `GET /api/health` ✅
- `POST /api/diagnosis/stream` 返回 thinking SSE 流 ✅
- 知识库维度：`384`，文档数：`5` ✅

### 2.7 统一所有 LLM API 调用到 yunwu.ai
**变更文件**：
- `backend/llm_client_yunwu.py`：重写为唯一 LLM 入口。移除内置的 Kimi / DeepSeek / mock 分支与硬编码 key；`get_llm_client` 无论传入什么 provider 均返回 `YunwuAIClient`；新增通用 `chat()` 方法支持自定义 messages 与 `response_format`。
- `backend/api_server.py`：移除 llm_client_v3 / v2 / v1 的 fallback 导入与 provider 自动检测逻辑；`LLM_PROVIDER` 非 `yunwu` 时强制切换为 `yunwu`。
- `backend/search_engine.py`：移除 `KIMI_API_KEY` 变量，LLM 搜索统一使用 `YUNWU_API_KEY` / `YUNWU_BASE_URL`。
- `backend/web_search_agent.py`：默认优先读取 `YUNWU_API_KEY` / `YUNWU_API_BASE` / `YUNWU_MODEL`，兼容旧 `WEBSEARCH_*` 名称；默认模型改为 `gpt-4o-mini`。
- `backend/real_crawler.py`：移除硬编码 `KIMI_API_KEY` 与硬编码 `YUNWU_API_KEY`，改为从环境变量读取。
- `backend/local_api_v5.py`：移除硬编码 `WEBSEARCH_API_KEY`，改为从 `YUNWU_API_KEY` 读取。
- `backend/agent_system.py`：未配置密钥时的提示改为 `YUNWU_API_KEY`。
- `.env.example`：精简为 Yunwu-only 配置，移除 Kimi / DeepSeek / OpenAI 示例。

**安全提示**：此前硬编码的 key 仍存在于 Git 历史提交中，建议视为已泄露，后续应在 Yunwu 后台刷新或轮换该 key。

**本地验证**：
- 启动日志显示 `[API] 使用 Yunwu AI 客户端`、`LLM_PROVIDER=auto，按用户要求强制使用 yunwu.ai` ✅
- `py_compile` 通过全部关键文件 ✅
- `/api/health`、`/api/diagnosis/stream`、`/api/agents/run`、`/api/admin/auth` 均正常 ✅
- Agent 返回 `llm_enriched: true`，thinking log 完整 ✅

### 2.8 全站 UI 统一为古风古色古香主题
**变更文件**：
- `frontend/index.html`：主对话界面改为宣纸/朱砂/墨绿/鎏金古风主题，含纸纹背景、卷轴角饰、衬线字体。
- `frontend/test_ui_v3.html`：对话式问诊测试页同步改为古风。
- `frontend/test_ui.html`：综合测试平台同步改为古风。
- `frontend/kg_visual.html`：知识图谱可视化页改为古风，D3 节点/关系配色统一为朱砂/玉绿/鎏金/墨色。
- `frontend/admin.html`：后台管理系统细节色值进一步统一，移除残留的亮绿/亮黄/亮红。
- `frontend/pages/index/index.wxss`：微信小程序首页改为古风配色与纸纹背景。
- `frontend/pages/diagnosis/diagnosis.wxss`：微信小程序辨证页改为古风配色与纸纹背景。

**设计语言**：
- 背景：宣纸 `#f7f3e9`，卡片 `#fffdf8`
- 文字：墨色 `#2b2b2b`，淡墨 `#5a5a5a`
- 强调：朱砂 `#a53232`，玉绿 `#4a7c59`，鎏金 `#b8860b`
- 字体：`Noto Serif SC`、`Source Han Serif SC`、`SimSun`、`STSong` 等宋体/衬线字
- 装饰：卷轴卡片角饰、纸纹噪点、印章风格徽章

**本地验证**：
- `python -m http.server 8080` 启动，所有 HTML 页面返回 200 ✅
- HTML 解析通过，script 块完整 ✅
- 旧版现代配色（`#e8f5e9`、`#2d5016`、`#52c41a`、`#ff4d4f` 等）已从 HTML/WXSS 中清除 ✅

### 2.9 修复前端连接与页面加载问题
**问题 1：`index.html` 显示 "API未连接"，问问题返回 "连接失败"**
- 根因：`checkAPIStatus` 读取 `/api/health` 返回的 `data.knowledge`，但该字段不存在，JS 抛异常后被 catch 误判为未连接。
- 修复：改为读取 `data.rag_stats` 计算知识库总数，`index.html` 与 `test_ui_v3.html` 同步修复。

**问题 2：`kg_visual.html` 加载失败**
- 根因：页面请求 `../data/kg_graph.json`，文件不存在且路径在静态服务器下解析错误。
- 修复：路径改为 `./data/kg_graph.json`；未找到文件时自动生成示例知识图谱数据（麻黄汤/风寒表实证等节点）。

**问题 3：`admin.html` 字体加载与登录提示**
- 修复：将 Google Fonts 的 `@import` 改为 `<link>` 引入，避免部分浏览器忽略样式；登录表单增加默认令牌提示。

**本地验证**：
- `/api/health` 返回 200，`/api/diagnosis/stream` 返回 SSE 流 ✅
- `http://127.0.0.1:8080/index.html`、`admin.html`、`kg_visual.html` 均返回 200 ✅
- `/api/admin/auth` 默认令牌 `xiaoshennong-admin` 验证通过 ✅

### 2.10 多 Agent 系统接入 Yunwu API 并编写专业 Skill Prompt
**变更文件**：
- 新增 `backend/agent_skills.py`：
  - 封装 `AgentLLM`，底层基于 `llm_client_yunwu.YunwuAIClient`。
  - 提供 `generate`（自由文本）和 `generate_json`（强制 JSON Schema 输出）。
  - 为 7 个 Agent 注册专业 skill：
    - `drug_expert`：中药药性、功效、归经、炮制、剂量、配伍禁忌。
    - `symptom_expert`：症状辨证、部位/性质/程度、关联证型、问诊要点。
    - `formula_expert`：方剂组成、君臣佐使、加减变化、现代应用。
    - `adverse_expert`：不良反应、禁忌人群、药物相互作用、毒性分级。
    - `patient_expert`：患者档案结构化、舌脉信息、体质辨识、随访要点。
    - `cooccurrence_expert`：症状共现网络、支持度/置信度/提升度、时序关系。
    - `cluster_expert`：患者聚类、证型分组、特征向量、临床意义。
  - 每个 skill 包含中文 system prompt、user prompt 模板、输出 JSON schema、字段校验。
- 修改 `backend/multi_agent_system.py`：
  - `AgentCoordinator` 创建共享 `AgentLLM` 实例并注入全部 7 个 Agent。
  - 每个 Agent 的 `generate` 先使用本地/爬虫逻辑生成基础档案，再调用 `_enrich_with_llm` 通过 Yunwu API 结构化增强。
  - LLM 调用失败时自动回退到旧逻辑，保证服务可用性。
  - 新增 `llm_provider`、`llm_cost_ms`、`llm_tokens` 等字段到 thinking log，便于观察 LLM 调用情况。

**本地验证**：
- `python -m py_compile backend/agent_skills.py backend/multi_agent_system.py` ✅
- `POST /api/agents/run` 调用全部 7 个 Agent（drug / symptom / formula / adverse / patient / cooccurrence / cluster）均返回 200，thinking log 5–11 步，输出包含 `llm_enriched: true` ✅
- `GET /api/agents/stats` 正常返回各 Agent 统计 ✅
- 控制台测试出现 GBK 编码乱码为 Git Bash 终端环境问题，Python requests 解析 JSON 正常。

### 2.11 口语化症状别名匹配
**变更文件**：
- `backend/symptom_codes.py`：为高频口语表达补充标准症状别名。
  - `SN-TH-S-004 胃脘痛`：新增 `胃不舒服、胃不适、胃难受、胃有点不舒服、胃胀痛、胃隐痛`
  - `SN-TH-S-005 腹胀`：新增 `胃胀、胃满、肚子鼓鼓`
  - `SN-TH-S-012 食欲不振`：新增 `没胃口、吃不下、不想吃饭、饭量减少`
- `backend/api_server.py`：
  - 引入 `from symptom_codes import find_symptoms_by_text`。
  - 将 `/api/diagnosis/stream`、`enhance_diagnosis_with_kb`、`/api/agents/analyze` 三处症状文本匹配从 `kb.find_symptoms_by_text(...)` 改为 `find_symptoms_by_text(...)`。
  - 原因：`knowledge_base_v3` 当前未加载 `merged_symptoms.json`，其症状索引为空，导致前端结果卡片的 `diagnosis.symptoms` 数组一直为空。

**本地验证**：
- `胃不舒服` → `SN-TH-S-004 胃脘痛` ✅
- `胃难受` → `SN-TH-S-004 胃脘痛` ✅
- `没胃口` → `SN-TH-S-012 食欲不振` ✅
- `肚子疼` → `SN-TH-S-006 腹痛` ✅
- 结果卡片 `diagnosis.symptoms` 正常返回 `[{"id":"SN-TH-S-004","name":"胃脘痛"}]`，不再为空。

---

## 3. 当前阻塞

### 3.1 服务器无法直接访问
- 当前环境 SSH 连接受阻：密码验证阶段返回 `Permission denied` / `Authentication timeout`。
- 可能原因：多次连接后服务器防火墙（fail2ban）把当前 IP 拉黑，或 root 密码已变更。
- GitHub Actions `Deploy to Server` workflow 也因 SSH key secret 配置问题失败。
- **本轮变更未推送**：OOM 优化、后台管理系统、本地运行 bug 修复、API Key 迁移、Agent skill Yunwu 化、全站古风 UI 改造、全量 LLM 调用统一 yunwu.ai、口语化症状别名匹配等修改了多个前后端文件，此前只在本地工作区；用户已指示整理并推送 GitHub。

### 3.2 部署尚未生效
- `main` 分支目前包含前端 TypeError 修复（`1690822`），但服务器可能仍在运行旧版本。
- 新的 OOM 优化需要推送并部署后才能在服务器生效。
- 需要用户在服务器上手动拉取并重启，或修复 GitHub Actions secrets 实现自动部署。

---

## 4. 待用户执行的操作

### A. 推送本地变更到仓库（已由用户指示执行）
在本地项目目录执行：
```bash
cd /c/Users/coins/xiaoshennong
git add backend/api_server.py backend/rag_engine_v2.py backend/llm_client_yunwu.py \
       backend/search_engine.py backend/web_search_agent.py backend/real_crawler.py \
       backend/local_api_v5.py backend/agent_system.py backend/multi_agent_system.py \
       backend/agent_skills.py backend/symptom_codes.py backend/knowledge_base_v3.py \
       frontend/index.html frontend/test_ui.html frontend/test_ui_v3.html \
       frontend/kg_visual.html frontend/admin.html \
       frontend/pages/index/index.wxss frontend/pages/diagnosis/diagnosis.wxss \
       .env.example start.bat start.sh CONTEXT_MEMORY.md PROJECT_STATUS.md
git commit -m "perf(api): 延迟加载重组件降低 OOM；feat(admin): 新增古风后台管理系统；fix(local): 修复本地运行 501/500 错误；fix(alias): 口语化症状别名匹配；security: API Key 迁移到 .env"
git push origin main
```

### B. 立即部署最新修复到服务器
```bash
cd /opt/xiaoshennong
git fetch origin
git reset --hard origin/main
mkdir -p logs

# 停止旧服务
pkill -f "api_server.py" || true
sleep 2

# 启动新服务（OOM 优化后首次请求会稍慢，因为知识库等组件首次加载）
cd backend
nohup /opt/xiaoshennong/venv/bin/python -B api_server.py > /opt/xiaoshennong/logs/api_server.log 2>&1 &
```

### C. 验证修复
- 打开 `http://43.247.135.91/`
- 输入“头痛”或“失眠”
- 应正常显示“识别症状”和“推荐方剂”，不再报 `Cannot read properties of undefined (reading 'symptoms')`。

### D. 验证后台管理系统
部署后访问 `http://43.247.135.91/admin.html`，使用默认令牌 `xiaoshennong-admin` 登录：
- Dashboard 显示症状/证型/方剂/药物/古籍文档/活跃会话统计
- 症状/证型/方剂/药物列表支持搜索、筛选、分页
- 会话管理可查看对话问诊会话
- 系统日志与系统信息正常加载

生产环境请设置环境变量 `ADMIN_TOKEN` 替换默认令牌。

### E. 验证 OOM 优化是否生效
部署后观察服务器内存：
```bash
free -h
ps aux --sort=-%mem | head -10
```
启动完成后（未触发首次辨证前）应看到 Python 进程内存明显下降。

### F. 处理 SSH 连接问题（可选）
在服务器控制台执行：
```bash
fail2ban-client status sshd 2>/dev/null | head -20
grep 'Failed password' /var/log/auth.log 2>/dev/null | tail -10
```
如果确认是 IP 被拉黑，解禁当前 IP：
```bash
fail2ban-client set sshd unbanip <当前IP>
```

### G. 进一步内存排查（如仍 OOM）
若 8G 仍不足，请提供：
```bash
free -h
swapon -s
ps aux --sort=-%mem | head -20
dmesg -T | grep -i 'out of memory\|killed process' | tail -20
tail -n 100 /opt/xiaoshennong/logs/api_server.log 2>/dev/null
```

---

## 5. 关键文件变更

| 文件 | 变更 |
|---|---|
| `backend/api_server.py` | 新增 `/api/diagnosis/stream`；OOM 优化；新增 `/api/admin/*` 后台管理接口；Windows stdout UTF-8 适配；自动导入示例数据限制为 sample 文件；启动时加载 `.env`；强制 LLM 使用 yunwu.ai；使用 `symptom_codes.find_symptoms_by_text` 修复 `diagnosis.symptoms` 为空 |
| `backend/rag_engine_v2.py` | 启动时校验 ChromaDB 嵌入维度，不匹配则自动重建 |
| `backend/llm_client_yunwu.py` | 唯一 LLM 入口；移除 Kimi/DeepSeek/mock 分支与硬编码 key；`get_llm_client` 始终返回 `YunwuAIClient` |
| `backend/search_engine.py` | 移除 Kimi key；LLM 搜索统一使用 Yunwu |
| `backend/web_search_agent.py` | 默认读取 `YUNWU_API_KEY`；默认模型 `gpt-4o-mini` |
| `backend/real_crawler.py` | 移除硬编码 Kimi/Yunwu key，改从环境变量读取 |
| `backend/local_api_v5.py` | 移除硬编码 `WEBSEARCH_API_KEY`，改从 `YUNWU_API_KEY` 读取 |
| `backend/multi_agent_system.py` | 7 个 Agent 共享 `AgentLLM`，生成基础档案后通过 Yunwu API 结构化增强 |
| `backend/agent_skills.py` | 新增：封装 `AgentLLM`，注册 7 个中医专业 skill，含 system prompt、user prompt 模板、JSON schema |
| `backend/symptom_codes.py` | 为胃脘痛、腹胀、食欲不振补充口语化别名 |
| `frontend/index.html` | 主对话界面；`API_BASE` 动态适配；古风宣纸/朱砂/墨绿/鎏金主题 |
| `frontend/test_ui_v3.html` | 对话式问诊测试页；古风主题 |
| `frontend/test_ui.html` | 综合测试平台；古风主题 |
| `frontend/kg_visual.html` | 知识图谱可视化；古风主题，D3 配色统一 |
| `frontend/admin.html` | 后台管理系统；古风主题 |
| `frontend/pages/index/index.wxss` | 微信小程序首页；古风主题 |
| `frontend/pages/diagnosis/diagnosis.wxss` | 微信小程序辨证页；古风主题 |
| `.env.example` | 增加 `ADMIN_TOKEN`、说明 `LLM_PROVIDER=auto` |
| `CONTEXT_MEMORY.md` | 更新会话上下文记忆 |

---

## 6. 注意事项

- `.env` 文件已在 `.gitignore` 中，不会被提交。
- 服务器 root 密码已口头提供，**不要写入任何文件**。
- 自动部署需要 GitHub Secrets：`SERVER_HOST`、`SERVER_USER`、`SERVER_SSH_KEY`（或 `SERVER_PASSWORD`）。

---

## 会话快照 — 2026-07-16 09:45（本地继续推进，已准备推送 GitHub）

### 本次目标
- 让本地小神农项目 100% 可用：后台系统、古风 UI、所有 API 统一走 yunwu.ai。
- 修复 index.html 无法回答、admin.html/kg_visual.html 打不开的问题。
- 优化辨证流程：先联网搜索 → 批判性评估 → 知识库佐证 → 生成详细回答。
- 扩展口语化症状别名匹配，让“胃不舒服”等日常描述能命中标准编号。

### 当前服务状态
- **后端**：`http://localhost:5001`（PID 9996，Flask 开发服务器，nohup 常驻）
- **前端**：`http://localhost:8080`（PID 12552，python http.server，nohup 常驻）
- **访问入口**：
  - 问诊页：`http://localhost:8080/index.html`
  - 后台管理：`http://localhost:8080/admin.html`
  - 知识图谱：`http://localhost:8080/kg_visual.html`
- **后台 Token**：`xiaoshennong-admin`（在 `.env` 中）
- **LLM / 联网搜索**：统一使用 yunwu.ai，`YUNWU_API_KEY` 已配置在 `.env`

### 本次修改的核心文件
1. `backend/rag_engine_v2.py`
   - 修正最后一步返回结果的 `step` 编号：从 `9` 改为 `13`。
   - LLM 生成调用增加 `max_tokens=8000`。
   - 重写 `build_v2_prompt`：
     - 明确“先联网搜索 → 批判性评估 → 知识库佐证 → 未佐证则生成入库建议”的推理顺序。
     - 输出 12 个完整小节：症状分析、病因病机、证型分析、方剂推荐、药物分析（含效果统计）、食疗建议、作息建议、情志调摄、运动导引、穴位按摩/推拿、禁忌提醒、就医建议。
     - 采用古朴典雅中医文风，禁止网络流行语与 emoji，要求每节 3–6 条具体建议。

2. `backend/api_server.py`
   - 修复 `/api/diagnosis/stream` 中 `advice` 被强制截断为 800 字符的问题（去掉 `[:800]`）。
   - 补全并验证 `/api/semantic/search`、`/api/kg/graph`、`/api/admin/*`、`/api/agents/*`、`/api/dialogue/*` 等接口。
   - 引入 `from symptom_codes import find_symptoms_by_text`，替换三处 `kb.find_symptoms_by_text`，修复结果卡片 `diagnosis.symptoms` 为空。

3. `backend/symptom_codes.py`
   - 为 `胃脘痛`、`腹胀`、`食欲不振` 补充口语化别名，覆盖“胃不舒服、胃难受、没胃口”等日常表达。

4. `start.bat` / `start.sh`
   - 去掉硬编码的 `LLM_PROVIDER=mock` 和 `PORT=5000`，改为读取 `.env`。
   - 一键同时启动前端（8080）和后端（5001）。

### 回归测试结果
26 项 API 测试全部通过：
health、diagnosis、diagnosis stream、retrieve、semantic search、knowledge stats、user register、user profile、products、product detail、product recommend、dialogue start、dialogue turn、dialogue status、agents stats、agents run、agents analyze、admin auth、admin stats、admin symptoms/syndromes/formulas/drugs/sessions/system、kg graph。

### 已验证的问诊效果
以“胃不舒服”测试 `/api/diagnosis/stream`：
- `step 1 症状标准化` 命中 `SN-TH-S-004 胃脘痛`。
- 结果卡片 `diagnosis.symptoms` 正常返回 `[{"id":"SN-TH-S-004","name":"胃脘痛"}]`。
- 13 个思考步骤正常返回，无 `undefined`。
- 最终回答 2000+ 字符，覆盖全部 12 个小节，包含具体食疗、作息、情志、运动、穴位、禁忌、就医建议。

### 待继续/可优化项
- 服务已改用 `nohup` 常驻，避免后台任务 30 分钟超时；生产环境仍需 systemd/supervisor 等方案。
- 可将 `SYMPTOM_MAP` 同步导出为 `data/raw/merged_symptoms.json`，让 `knowledge_base_v3` 的索引也包含口语化别名。
- 知识库文档数目前只有 5 条（Chroma），可考虑批量导入更多古籍数据。
- 前端结果卡片的小标题仍带 emoji（📋、💊 等），如需要可进一步换成纯古风图标或 CSS 装饰。
- 服务器 SSH 仍连不上 `43.247.135.91`，部署需要用户在服务器端解禁 IP 或修复 GitHub Actions secrets。

### 关键命令
```bash
# 重新启动（Windows）
start.bat

# 重新启动（Git Bash / WSL）
bash start.sh

# 健康检查
curl http://localhost:5001/api/health

# 测试辨证
curl -X POST http://localhost:5001/api/diagnosis/stream \
  -H "Content-Type: application/json" \
  -d '{"symptoms":"胃不舒服"}'
```


---

## 会话快照 — 2026-07-19 13:05（技术债收尾 + 古籍全量入库）

### 本次目标
- 处理上一会话遗留的「待继续/可优化项」：merged_symptoms 重新导出、古籍批量入库、前端 emoji 古风化。

### 完成事项

#### 1. 重新导出 merged_symptoms.json
- 运行 `python backend/merge_data.py`，重新生成 `data/raw/merged_symptoms.json`（603 症状）、`merged_drugs.json`（117）、`merged_formulas.json`（70）。
- 旧文件生成于 07-12，不含 07-16 新增的口语化别名；新文件已验证含「胃不舒服/胃难受」（SN-TH-S-004）、「胃胀」（SN-TH-S-005）、「没胃口」（SN-TH-S-012）。
- knowledge_base_v3 重启后别名索引自动同步。

#### 2. 古籍条文全量导入 Chroma（125,005 条）
- 新增 `scripts/import_classical_texts.py`：
  - 转换 `data/raw/classical_texts*.json`（列表格式 `{text_id, book, section, text, symptom, keywords}`，与 data_pipeline 既有两种格式均不同，故脚本内置转换器）。
  - 以 `text_id` 为 chunk_id，导入前按批查询已存在 id 跳过，幂等可断点续跑。
  - 进度记录 `logs/classical_import_progress.json`；支持 `--max-files N`。
- 全量导入结果：125 个文件 × 1000 条 = 125,000 条新增，耗时约 8 分钟，无失败。
- 知识库文档数：5 → **125,005**（384 维 all-MiniLM-L6-v2）。
- 注意：导入需先停止后端，避免 Chroma SQLite 并发写冲突。

#### 3. 前端 emoji 古风化（34 处）
- `frontend/index.html`（18 处）与 `frontend/test_ui_v3.html`（16 处）：
  - 新增 `.seal-badge` 印章 CSS（朱砂底、白字、圆角、内描边）。
  - 卡片标题 🔍🤖📊🔧 → 印章「检/协/析/试」。
  - 结果区标题 📋💊📍🍵🧘💆 → 印章「辨/方/穴/食/引/按」（穴=鎏金、食引按=玉绿）。
  - 头像 🌿→「神」（朱砂粗体）、👤→「我」、🧠→「思」。
  - 警告框 ⚠️ → 鎏金印章「慎」。
  - test_ui_v3.html 模式按钮 💬⚡ → 纯文字；⭐→「主」、🔬→「证」。
- 保留：思考步骤内 ✓/⚠/●/✗ 纯文本状态符号（已在 styled 元素内，非彩色 emoji）。
- 未处理：`test_ui.html`（24 处）与 `kg_visual.html`（3 处）仍有 emoji，属内部测试页，后续可按同方案处理。

#### 4. 回归验证（11 项全过，脚本 `scripts/regression_test.py`）
- `GET /api/health`：`total_documents=125005` ✅
- `POST /api/retrieve`「咳嗽/头痛」：返回《难经》等古籍条文 ✅
- `POST /api/diagnosis/stream`「胃不舒服」：13 个思考步骤，命中 SN-TH-S-004，`data.advice` 2432 字符（12 小节完整）✅
  - 注意：最终回答在 result 事件 `data.advice`（顶层），`data.diagnosis` 内只有症状/方剂/穴位等结构化数组。
- 后台接口需请求头 `X-Admin-Token: xiaoshennong-admin`：`/api/admin/auth`、`/api/admin/stats`、`/api/admin/symptoms` ✅
- 前端 4 个页面（index/admin/test_ui_v3/kg_visual）均 200，index.html 含 14 处 seal-badge ✅

### 当前服务状态
- 后端 `http://localhost:5001`（nohup，日志 `logs/api_server.log`）
- 前端 `http://localhost:8080`（nohup，日志 `logs/frontend.log`）

### 待继续/可优化项
- **本次变更未提交 git**（含 merged_*.json、scripts/2 个新脚本、2 个前端文件、2 个文档），待用户指示后 commit/push。
- 服务器部署仍阻塞（SSH fail2ban/密码），新导入的 12.5 万条知识库要同步到服务器需另做数据迁移（data/chroma_db_v2 目录较大，建议打包传输或服务器端重跑导入脚本）。
- `test_ui.html`（24 处）与 `kg_visual.html`（3 处）emoji 可按本次方案继续清理。
- 微信小程序、区块链存证、疗效反馈闭环、医馆 SaaS 等路线图项未动。

### 关键命令
```bash
# 古籍导入（先停后端）
python scripts/import_classical_texts.py --max-files 5   # 小批次
python scripts/import_classical_texts.py                 # 全量

# 回归测试（需后端运行）
python scripts/regression_test.py
```


---

## 会话快照 — 2026-07-19 15:50（语义搜索修复 + 账号/病历/医馆/订单体系落地）

### 本次目标
经讨论确定四大方向并全部落地：
1. 真医生式问诊（先问资料再辨证）
2. 语义搜索 bug 修复（根因：英文嵌入模型中文退化）
3. 用户注册/医馆入驻/电子病历/独立编号取证
4. 医馆管理后台 + 药方审核 + 订单（邮寄/自取/代煎）

### 关键架构决策（讨论结论）
- **语义搜索走无嵌入主路**：嵌入模型不是必需品；用别名表+词典+jieba+SQLite 元数据打分替代，LLM 改写仅兜底且缓存，token 消耗主路为零。
- **合规红线**：AI 只出"建议"，入驻医馆执业医师审核通过才生成正式处方；平台不碰药。
- **医馆限权开通**：注册即可登录后台熟悉流程，审核/接单权限由平台核验资质后解锁。
- **商城分层**：一期只做药食同源养生品自营；中药材原材料（药品管理范畴，需药品经营许可证）留待二期"医馆货架"由有资质医馆销售。
- **手机号锚点**：Web 账密+短信绑定；小程序端一期用验证码登录，手机号一键授权需企业主体小程序（约 3 分/次）。

### 完成事项（M1-M5，回归 33/33 全过）

#### M1 语义搜索修复
- 实证根因：`all-MiniLM-L6-v2` 对中文退化（sim(咳嗽,咳嗽咳痰)=0.538 < sim(咳嗽,腰痛)=0.594，排序倒置）。
- 新增 `backend/db.py`（SQLite 持久化层+编号发号器）、`backend/lexical_retriever.py`（词法检索）、`scripts/import_classical_to_sqlite.py`（125,000 条入库）。
- `/api/retrieve`、`/api/semantic/search` 切换到词法主路（零结果回退向量），响应带 `engine` 字段。
- LLM 改写修正：只改写成症状/证型（改写药名会取不到候选）；无效改写不缓存。
- 评测：咳嗽相关度 5/5，不同查询结果互不重叠，口语查询（胃不舒服→胃脘痛）全部命中。

#### M2 账号认证
- `backend/sms_service.py`（可插拔，开发模式返回 dev_code；60s 重发限制；10 分钟有效；5 次试错锁定）。
- `backend/auth_service.py`（注册/登录/验证码登录/重置/me/登出；werkzeug 密码哈希；32 字节 token 7 天会话；require_user/require_clinic 装饰器；手机号脱敏）。
- 旧 `/api/user/register|profile`（内存版）标注 deprecated 保留兼容。

#### M3 电子病历 + 真医生式问诊
- `backend/emr_service.py`：profile 档案（懒创建，结构化字段 JSON 存 personal_history）+ visit 就诊记录。
- `dialogue_engine.py`：新增 PROFILE/HISTORY 阶段；年龄/性别/过敏/用药从输入捕获（含 pending 问题整句捕获）；信息完整度评分（资料40+症状20+互动20+过敏10+用药10）替代固定 3 轮；"直接辨证"快速通道；`create_session(user_id)` 病历预载。
- 辨证查询携带年龄/性别/既往史/过敏史/在用药物；辨证完成自动写 visit 病历（EMR 编号）。
- 接口：`GET /api/user/emr`、`GET|PUT /api/user/emr/profile`。

#### M4 医馆入驻 + 药方审核 + 处方订单
- `backend/clinic_service.py`：入驻申请（pending 即开通）→ 平台 verify（CV 编号）→ 审核队列（approve 带加减/reject 填理由）→ 订单状态机（created→accepted→preparing→decocting→shipped/awaiting_pickup→completed，order_events 全留痕）。
- `/api/rx/apply` 双来源：对话模式取服务端会话快照（可信）；快速辨证模式客户端回传 symptoms+advice（快照标注 source=quick）。
- 商城订单服务端按 products_db 重算金额（防篡改）。
- 编号：U/EMR/MC/CA/RX/ORD/CV-YYYYMMDD-序号，全部预留 hash 字段。

#### M5 前端
- `frontend/clinic.html`（新，1161 行）：登录/入驻、状态徽章、Dashboard、药方审核（病历快照+AI 建议全文+加减/驳回，pending 锁定态）、订单流转、医馆资料。
- `frontend/index.html`（1486→2694 行，纯增量）：页头「登录/注册」「医馆入驻」；登录/注册/忘记密码弹窗（dev_code 提示+知情同意）；个人中心（病历编辑/处方下单/订单留痕）；结果卡片「转医馆审核开方」→ 医馆选择弹窗；商城 section（合规横幅+商品网格+中药材占位卡）。
- 全站零彩色 emoji。

### 测试数据（dev 库，可留作演示）
- 用户 13800138000/abc12345（有病历、已审核处方、订单）；医馆 13700137000/clinic123（仁心堂，已核验）；回归脚本每次跑会新增随机手机号用户与医馆。

### 待继续/可优化项
- **本次变更未提交 git**（新模块 8 个、前端 2 个、脚本 3 个、文档 4 个），待用户指示后 commit/push。
- 服务器部署仍阻塞（SSH）；上线前需：jieba 安装、SQLite 初始化（自动）、短信企业报备、ADMIN_TOKEN 更换。
- 微信小程序端改造（登录对接 login_sms；企业主体后接 getPhoneNumber）。
- `test_ui.html`（24 处）与 `kg_visual.html`（3 处）emoji 未清理。
- 嵌入模型可作为词法检索增强（bge-small-zh），非必需。
- LLM 客户端启动日志会打印部分 API Key（llm_client_yunwu.py），建议后续抹除。

### 关键命令
```bash
python scripts/regression_test.py           # 全量 33 项（含 LLM 辨证，约 1-2 分钟）
python scripts/regression_test.py --quick   # 跳过 LLM 链路
python scripts/import_classical_to_sqlite.py  # 古籍入 SQLite（幂等）
```


---

## 会话快照 — 2026-07-19 17:20（「本草长卷」主页 + 全站动效统一 + 后台完善）

### 本次目标
1. 高大上古风主页（苹果动效+古风，slogan：古有神农尝百草，今有小神农辩百症）
2. 全站页面统一苹果动效+古风（动效逻辑参照 github.com/emilkowalski/skills 的 apple-design）
3. 前后台可用性打磨

### 动效规约（DESIGN.md 十条铁律摘要）
- 按压即时反馈 scale(0.97)/100ms；临界阻尼 `cubic-bezier(0.22,1,0.36,1)` **禁回弹**；时长 100/150/300/600ms 四档
- 只动 transform/opacity（弹窗加 blur materialize）；弹窗从触发点长出、进出同路（XSNModal）
- 半透明宣纸材质吸顶栏（backdrop-filter blur 20px）；滚动叙事用 [data-reveal]+IntersectionObserver
- reduced-motion 全降级为 200ms 透明度（主题包内置，全站继承）
- 本土化：中文大标题加宽字距 0.2em（不从 Apple 负字距）；零彩色 emoji（汉字印章）

### 完成事项（P1-P5，回归 38/38 全过）

#### P1 设计系统
- `frontend/assets/xsn-theme.css`（8KB：token+组件+规范弹窗+降级规则）、`frontend/assets/xsn-motion.js`（8.8KB：reveal/counter/draw/视差/XSNModal）、`frontend/DESIGN.md`（规约文档）。

#### P2 home.html 主页（32KB 零外部图片）
- 吸顶材质 nav（滚动出现渐变淡出边）、Hero 三层 SVG 山水视差（鼠标+滚动双源）、竖排「神农尝百草，一日而遇七十毒」、印章 450ms 临界阻尼落定、双 CTA stagger 入场
- 粘性滚动品牌故事三段（300vh track+sticky，上古→千年→今日）、四能力卡（问/典/历/证）、数字带计数（125005/282/28/724 时辰守候）、SVG 墨线描边问诊流程四节点、卷轴医馆入驻、免责+备案占位页脚
- OG 标签、SVG favicon、响应式（竖排/云雾层移动端隐藏）、总大小 32KB

#### P3 全站统一（7 页）
- index.html：theme/motion 引入（主题先于内联样式加载避免覆盖）、6 个弹窗全部改造为 XSNModal（带降级回退）、nav 材质化、section 切换 200ms 淡入、按钮按压反馈、title 去 v5.0、favicon
- clinic/admin/test_ui_v3：theme+motion 引入、登录卡 reveal、tab/视图切换淡入、按压反馈
- kg_visual/test_ui：theme 引入 + emoji 清理（5 处 + 约 50 处，含 🔴🟠🟢 过滤逻辑改 Unicode 转义防功能回归、商品 emoji 字段改汉字 icon）
- 全部页面统一 favicon 与 title 格式「小神农中医AI · xxx」

#### P4 平台后台
- 新接口：`GET /api/admin/users`（分页+脱敏+聚合）、`GET /api/admin/orders`（过滤+分页）、`GET /api/admin/clinics/<id>/verifications`；`/api/admin/stats` 扩展 users/clinics/orders/prescriptions
- admin.html 三视图：医馆核验（状态过滤+核验/冻结+CV 记录弹窗）、用户管理（分页）、订单总览（类型/状态过滤+分页）；Dashboard 四卡（待核验/待审核鎏金提示可点击跳转）

#### P5 打磨
- 删除 llm_client_yunwu.py 启动日志 API Key 前缀打印（实测新日志 0 命中）
- .env.example 补 SMS_* 配置说明；DEPLOY.md 补 CORS 生产收紧建议 + Key 轮换提醒
- 回归脚本扩至 38 项（新增 P4 后台用例）全过

### 访问入口
- 主页 `http://localhost:8080/home.html`；问诊 `index.html`；医馆 `clinic.html`；平台后台 `admin.html`

### 待继续/可优化项
- **本次全部变更未提交 git**（frontend 9 个文件+assets 2 个+backend 3 个+脚本 1 个+文档 4 个），待用户指示。
- 主页改名换位（home.html→index.html、对话页→chat.html）待主页浏览器实测定型后做；视差/粘性段建议浏览器里过一眼手感。
- 小程序端、真实短信、在线支付、区块链存证、服务器部署（SSH 阻塞）同前。
- home.html 的 `.xsn-seal-deep` 深红印章是页内扩展类，多页面需要时可上移到主题包。

### 关键命令
```bash
python scripts/regression_test.py           # 38 项全量
python scripts/regression_test.py --quick   # 跳过 LLM
```


---

## 会话快照 — 2026-07-19 18:30（主站接入真医生式问诊）

### 问题
用户反馈主站聊天打"头疼"直接出答案，没有问诊过程。

### 根因
index.html 的 sendMessage 走 `/api/diagnosis/stream`（一次性快速辨证），从未经过 M3 升级的对话问诊引擎（`/api/dialogue/*`）。**与 agent_skills.py 无关**（那是 7 个后台数据 Agent 的提示词）。

### 修复（index.html，2754→2977 行）
- 聊天区加模式切换：**对话问诊（默认）** | 快速辨证（原 SSE 流式不动）
- 对话模式客户端：`/api/dialogue/start`（带 token 预载病历）→ 逐轮 `/api/dialogue/turn`；阶段印章标签（问·基本情况/问·症状细节/问·过敏与用药/辨·鉴别分析/断·辨证论治）、suggested_questions 可点胶囊（≤3 个）、鎏金进度条（transform scaleX）、思考步骤与打字并行渲染
- 辨证出卡后「转医馆审核开方」：对话模式传 **session_id**（服务端可信快照），快速模式传 symptoms+advice（原逻辑）
- 登录用户 visit_emr_id 时结果卡下方提示「已存入病历（EMR 编号）」
- 会话失效自动重新 start 重试一次；欢迎语改为坐诊式开场

### 实测对话流（urllib 断言全过）
start(greeting) → "头疼"(**profile，问年龄性别**) → "35岁，男"(clarifying) → "疼了三天，胀痛，直接辨证"(ready，出诊断 2819 字)

### 回归
`regression_test.py --quick` 29/29 全过；快速辨证/登录/商城/语义搜索/Agent 零破坏。

### 遗留
- 匿名开局后中途登录：该匿名会话开方申请会被后端拒（规则如此），重新发送即带 token 恢复。
- 对话模式 thinking_steps 为并行渲染（不 await），如需串行在 showThinkingSteps 前加 await。


---

## 会话快照 — 2026-07-19 19:20（问诊交互逻辑修正：回答选项而非选择题）

### 用户反馈
追问胶囊把"医生该问的问题"做成可选按钮——患者不该替医生选问题，且每人病情不同不应是选择题。

### 修正（对话引擎 + index.html）
- **最终交互模型：零按钮**。用户进一步指出"怕冷/怕热"选项本身会诱导主诉（"都不怕"的情况被选项抹掉）——故将上一轮的 quick_replies 方案整体移除。
- 后端：`dialogue_engine.py` 移除 quick_replies 计算与返回字段及选项解析器；`api_server.py` 响应不再含 quick_replies；`suggested_questions` 保留为纯调试字段。
- 前端：index.html 移除胶囊渲染、点击委托、相关 CSS。问诊=纯自由输入。
- 保留：输入区「失眠/头痛」等 quick-tag 快捷输入（既有功能，等于替用户打字发起主诉，非回答医生问题的选项）。
- 实测：API 响应已无 quick_replies 字段；回归 29/29 全过。

### 追加（同日）：quick-tag 也移除 + 占位文案改为教学式
- 用户要求连输入区快捷输入一并去掉，占位符不应是症状示例（"最近失眠多梦口干口苦"会诱导用户照着写）。
- index.html：移除 quick-symptoms 标签排、sendQuick 函数、相关 CSS；textarea 占位文案改为教学式四要素：「请说清四点：哪里不舒服、什么样的感觉（胀痛/刺痛/隐痛等）、持续多久了、什么情况会加重或缓解」。
- 设计原则最终版：**问诊区零按钮、零症状示例；只教方法，不给答案**。
