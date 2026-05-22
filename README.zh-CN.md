<p align="center">
  <img src="./assests/processed/kaleidoscope-icon-rounded.png" alt="Kaleidoscope" height="120" />
</p>

<h1 align="center">Kaleidoscope</h1>
<p align="center">
  <em>学术论文智能分析平台 · 认知偏差检测引擎</em>
</p>

<p align="center">
  <strong>🇨🇳 中文文档</strong> &nbsp;|&nbsp; <a href="./README.md">🇬🇧 English</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12-blue?logo=python&logoColor=white" alt="Python 3.12" />
  <img src="https://img.shields.io/badge/nuxt-3.19-00DC82?logo=nuxt.js&logoColor=white" alt="Nuxt 3" />
  <img src="https://img.shields.io/badge/fastapi-0.115-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/工具数-2075+-purple" alt="2075+ Tools" />
  <img src="https://img.shields.io/badge/MCP-兼容-blueviolet" alt="MCP Compatible" />
  <img src="https://img.shields.io/badge/license-KNCL%20v1.0-orange" alt="KNCL v1.0 License" />
</p>

---

## 概述

Kaleidoscope 是一个**全栈学术研究平台**，用于发现、抓取、阅读和分析学术论文。它将 **Markdown 优先**的存储策略与强大的**认知分析引擎**相结合——超过 2,075 个专业 AI 工具，可检测学术论述中的认知偏差、逻辑谬误、修辞扭曲和推理缺陷。

### 核心功能

- 📡 **ArXiv 批量采集** — 跨类别批量获取论文，自动转换为 Markdown
- 📖 **Markdown 阅读器** — 在浏览器中阅读论文，支持目录导航、字体调节、章节跳转
- 📊 **数据分析仪表盘** — 文库洞察：时间线、分类分布、活跃作者、关键词云、引用网络
- 🔍 **多模态搜索** — 关键词搜索、语义搜索、声明优先搜索
- 🧠 **认知分析引擎** — 2,075+ AI 驱动的深度推理分析工具
- 🤖 **自主研究代理** — 多步骤研究工作流与工具编排
- 🔌 **MCP 服务器** — Model Context Protocol 集成，支持外部 AI 代理访问
- 📦 **Python SDK** — 编程式访问所有平台能力
- 🌐 **中英双语界面** — 完整的国际化支持
- 🔗 **原文链接** — 一键跳转 arXiv 摘要页、PDF、ar5iv HTML

---

## 认知分析引擎

核心差异化能力 — 2,075+ 检测工具，按领域组织的完整认知分析分类体系：

| 领域 | 示例 | 数量 |
|------|------|------|
| 认知偏差 | 锚定效应、可得性启发、确认偏差、达克效应 | 200+ |
| 逻辑谬误 | 人身攻击、稻草人、虚假两难、滑坡谬误 | 150+ |
| 因果推理 | 事后归因、反向因果、虚假相关、单因谬误 | 100+ |
| 认知尺度 | 生态谬误、合成/分割谬误、范围忽视 | 80+ |
| 社会动力学 | 群体思维、多元无知、声誉级联、从众压力 | 100+ |
| 制度性 | 引用卡特尔、唯证书论、监管俘获、同行评审剧场 | 80+ |
| 沟通 | 海狮式提问、语气管控、术语门槛、战略模糊 | 80+ |
| 叙事 | 起源神话、幸存者偏差、目的论思维、后见之明 | 80+ |
| 决策 | 过早闭合、分析瘫痪、承诺升级 | 80+ |
| 方法论 | P值操纵、德州神枪手、路灯效应、物化谬误 | 80+ |
| 时间性 | 现在主义、基线漂移、近因错觉、历史终结幻觉 | 60+ |
| 情绪 | 情感注入、道德愤怒替代、共情鸿沟 | 60+ |
| 权力与身份 | 认知不公、制造同意、部落认识论 | 100+ |
| 技术 | 算法不透明、过滤气泡、自动化偏差、数字遗忘 | 60+ |
| 元认知 | 盲点偏差、解释深度错觉、校准忽视 | 60+ |
| + 更多 | 生态、美德、注意力、测量、集体… | 600+ |

每个工具接受领域特定参数，返回结构化 JSON，包含检测结果、严重程度评级和可操作建议。

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      前端 (Nuxt 3)                           │
│   Vue 3 · TypeScript · Lucide Icons · GSAP 动画             │
└─────────────────────┬───────────────────────────────────────┘
                      │ REST API
┌─────────────────────▼───────────────────────────────────────┐
│                    后端 (FastAPI)                             │
│   SQLAlchemy · Celery · Pydantic · Structlog                 │
├──────────────────────────────────────────────────────────────┤
│  代理层                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ 工具调度器    │  │ 研究运行时    │  │ MCP 服务器       │   │
│  │ (2075 工具)  │  │ (自主执行)    │  │ (2075+ 工具)    │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
├─────────────┬───────────┬───────────┬───────────────────────┤
│ PostgreSQL  │   Redis   │ Meilisearch│    Qdrant            │
│  (主数据库)  │  (缓存)    │ (全文搜索)  │  (向量嵌入)        │
├─────────────┴───────────┴───────────┴───────────────────────┤
│  Neo4j (图数据库)  ·  MinIO (对象存储)  ·  GROBID (PDF)      │
└─────────────────────────────────────────────────────────────┘
```

---

## 项目结构

```
Kaleidoscope/
├── backend/
│   ├── app/
│   │   ├── api/v1/             # REST 接口 (20+ 路由)
│   │   ├── clients/            # 外部 API 客户端 (arXiv, MinerU, OpenAlex, LLM)
│   │   ├── models/             # SQLAlchemy ORM 模型
│   │   ├── schemas/            # Pydantic 请求/响应模式
│   │   ├── services/           # 2075+ 认知分析服务
│   │   │   ├── agent/          # 工具调度器 & 代理编排
│   │   │   ├── extraction/     # QA 引擎、摘要器
│   │   │   ├── search/         # 向量 & 混合搜索
│   │   │   └── graph/          # 引用图谱分析
│   │   ├── tasks/              # Celery 异步任务
│   │   ├── mcp_server.py       # MCP 协议服务器
│   │   └── graph_db/           # Neo4j 驱动 & 查询
│   ├── kaleidoscope_sdk/       # Python SDK 客户端
│   ├── alembic/                # 数据库迁移
│   └── pyproject.toml          # Python 依赖 & 工具配置
│
├── frontend/                   # Nuxt 3 前端
│   ├── components/             # Vue 组件
│   ├── pages/                  # 路由页面
│   ├── composables/            # 组合式函数
│   ├── i18n/                   # 国际化 (en/zh)
│   └── nuxt.config.ts
│
└── docker-compose.yml          # 一键启动全部服务
```

---

## 快速开始

### 环境要求

- Python 3.12+, Node.js 20+, Docker & Docker Compose
- PostgreSQL 16, Redis 7, Qdrant, Meilisearch, Neo4j 5, MinIO

### 安装

```bash
# 克隆仓库
git clone https://github.com/PeppaPigw/Kaleidoscope.git
cd Kaleidoscope

# 启动基础设施
docker compose up -d

# 后端
cd backend
cp .env.example .env        # 编辑配置
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload

# 前端
cd ../frontend
npm install
npm run dev
```

### MCP 服务器

```bash
# 启动 MCP 服务器供外部 AI 代理使用
cd backend
python -m app.mcp_server
```

### Python SDK

```python
from kaleidoscope_sdk import KaleidoscopeClient

client = KaleidoscopeClient(base_url="http://localhost:8000")

# 使用认知分析工具
result = client.tool("anchoring_effect_detect", {
    "claim": "初始估计严重影响了最终判断",
    "domain": "behavioral_economics"
})
```

---

## API 概览

| 模块     | 路径                   | 说明                          |
| -------- | ---------------------- | ----------------------------- |
| 论文     | `/papers`              | CRUD、批量导入、Markdown 阅读 |
| 分析     | `/analysis`            | AI 摘要、QA、证据评估         |
| 代理     | `/agent`               | 自主研究代理 (2075+ 工具)     |
| 搜索     | `/search`              | 多模态搜索                    |
| OpenAlex | `/openalex`            | 外部论文搜索 + 引用关系图     |
| 知识     | `/knowledge`           | 笔记图谱                      |
| 订阅源   | `/feeds`               | RSS 管理                      |
| 智能分析 | `/intelligence`        | AI 驱动的深度洞察             |
| MCP      | `stdio / SSE`          | Model Context Protocol 接口   |

后端运行后，访问 `http://localhost:8000/docs` 查看交互式 API 文档。

---

## 技术栈

| 层级     | 技术                                          |
| -------- | --------------------------------------------- |
| 前端     | Nuxt 3, Vue 3, TypeScript, Lucide Icons, GSAP |
| 后端     | FastAPI, SQLAlchemy 2, Celery, Pydantic v2    |
| 数据库   | PostgreSQL 16, Redis 7                        |
| 搜索引擎 | Meilisearch, Qdrant (向量搜索)                |
| 图数据库 | Neo4j 5                                       |
| 对象存储 | MinIO (S3 兼容)                               |
| PDF 解析 | GROBID, MinerU API                            |
| AI       | LLM 集成 (可配置端点), MCP 协议               |
| SDK      | kaleidoscope_sdk (Python)                     |

---

## 参与贡献

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feat/amazing-feature`)
3. 使用约定式提交 (`feat:`, `fix:`, `docs:`)
4. 推送并创建 Pull Request

---

## 许可协议

本项目采用 Kaleidoscope Non-Commercial License (KNCL) v1.0。
商业使用需要单独获得书面许可或商业授权。详见 [LICENSE](LICENSE)。
