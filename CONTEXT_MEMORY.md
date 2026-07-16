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
