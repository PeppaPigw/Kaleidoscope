<p align="center">
  <img src="./assests/processed/kaleidoscope-icon-rounded.png" alt="Kaleidoscope" height="120" />
</p>

<h1 align="center">Kaleidoscope</h1>
<p align="center">
  <em>学术论文智能分析平台</em>
</p>

<p align="center">
  <strong>🇨🇳 中文文档</strong> &nbsp;|&nbsp; <a href="./README.md">🇬🇧 English</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12-blue?logo=python&logoColor=white" alt="Python 3.12" />
  <img src="https://img.shields.io/badge/nuxt-3.19-00DC82?logo=nuxt.js&logoColor=white" alt="Nuxt 3" />
  <img src="https://img.shields.io/badge/fastapi-0.115-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/license-KNCL%20v1.0-orange" alt="KNCL v1.0 License" />
</p>

---

## 概述

Kaleidoscope 是一个**全栈学术研究平台**，用于发现、抓取、阅读和分析学术论文。采用 **Markdown 优先** 的存储策略——通过 MinerU 将论文从 HTML/PDF 转换为 Markdown，无需存储 PDF 即可实现丰富的浏览器内阅读体验。

### 核心功能

- 📡 **ArXiv 批量采集** — 跨类别批量获取论文，自动转换为 Markdown
- 📖 **Markdown 阅读器** — 在浏览器中阅读论文，支持目录导航、字体调节、章节跳转
- 📊 **数据分析仪表盘** — 文库洞察：时间线、分类分布、活跃作者、关键词云、引用网络
- 🔍 **多模态搜索** — 关键词搜索、语义搜索、声明优先搜索
- 🧠 **AI 深度分析** — 证据实验室、跨论文比较、矛盾检测
- 🌐 **中英双语界面** — 完整的国际化支持
- 🔗 **原文链接** — 一键跳转 arXiv 摘要页、PDF、ar5iv HTML

---

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                   前端 (Nuxt 3)                          │
│  Vue 3 · TypeScript · Lucide Icons · GSAP 动画           │
└─────────────────────┬───────────────────────────────────┘
                      │ REST API
┌─────────────────────▼───────────────────────────────────┐
│                   后端 (FastAPI)                          │
│  SQLAlchemy · Celery · Pydantic · Structlog              │
├─────────────┬───────────┬───────────┬───────────────────┤
│ PostgreSQL  │   Redis   │ Meilisearch│    Qdrant         │
│  (主数据库)  │  (缓存)    │ (全文搜索)  │  (向量嵌入)       │
├─────────────┴───────────┴───────────┴───────────────────┤
│  Neo4j (图数据库)  ·  MinIO (对象存储)  ·  GROBID (PDF)    │
└─────────────────────────────────────────────────────────┘
```

---

## 项目结构

```
Kaleidoscope/
├── backend/                    # Python FastAPI 后端
│   ├── app/
│   │   ├── api/v1/             # REST 接口 (20+ 路由)
│   │   ├── clients/            # 外部 API 客户端 (arXiv, MinerU, OpenAlex…)
│   │   ├── models/             # SQLAlchemy ORM 模型
│   │   ├── schemas/            # Pydantic 请求/响应模式
│   │   ├── services/           # 业务逻辑 (解析、搜索、分析…)
│   │   ├── tasks/              # Celery 异步任务
│   │   ├── scripts/            # CLI 脚本 (数据种子)
│   │   ├── graph_db/           # Neo4j 驱动 & 查询
│   │   └── utils/              # 通用工具函数
│   ├── alembic/                # 数据库迁移
│   ├── docker/                 # Docker Compose 基础设施
│   ├── tests/                  # Pytest 测试套件
│   └── pyproject.toml          # Python 依赖 & 工具配置
│
├── frontend/                   # Nuxt 3 前端
│   ├── app/
│   │   ├── pages/              # 路由页面 (仪表盘、阅读器、分析…)
│   │   ├── components/         # Vue 组件 (14 个功能域)
│   │   ├── composables/        # 共享组合式函数 (useApi, useTranslation)
│   │   ├── layouts/            # 应用布局
│   │   └── assets/             # CSS 设计系统
│   ├── nuxt.config.ts
│   └── package.json
│
├── docs/                       # 项目文档
│   ├── design/                 # UI/UX 设计规格 (5 轮迭代)
│   └── memo/                   # 可行性分析、功能规格
│
├── docker-compose.yml          # → backend/docker/docker-compose.yml
├── Makefile                    # 开发快捷命令
└── README.md
```

---

## 快速开始

### 环境要求

- **Python 3.12+** 和 **pip**
- **Node.js 20+** 和 **pnpm**
- **Docker** 和 **Docker Compose**

### 1. 克隆项目

```bash
git clone <repo-url> Kaleidoscope
cd Kaleidoscope
```

### 2. 启动基础设施

```bash
docker compose up -d
# 启动: PostgreSQL · Redis · Meilisearch · Qdrant · Neo4j · MinIO · GROBID
```

### 3. 配置后端环境变量

```bash
cd backend
cp .env.example .env
```

在 `.env` 中填写以下最低配置（与 Docker 默认值对应）：

```env
DATABASE_URL=postgresql+asyncpg://kaleidoscope:kaleidoscope@localhost:5432/kaleidoscope
REDIS_URL=redis://localhost:6379/0
MEILI_URL=http://localhost:7700
MEILI_MASTER_KEY=kaleidoscope-meili-key
QDRANT_URL=http://localhost:6333

# AI 功能所需
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
```

### 4. 启动后端

```bash
# 安装依赖（首次运行）
pip install -e ".[dev]"

# 执行数据库迁移
alembic upgrade head

# 启动开发服务器  →  http://localhost:8000
uvicorn app.main:create_app --factory --reload --port 8000
```

### 5. 启动前端

```bash
cd ../frontend
pnpm install        # 首次运行
pnpm dev            # http://localhost:3000
```

### 6.（快捷方式）并行启动前后端

完成步骤 1–3 的初始化后，之后每次只需：

```bash
make dev            # 同时启动后端和前端
```

### 7. 初始数据填充（可选）

```bash
cd backend
python -m app.scripts.seed_arxiv     # 通过 MinerU 抓取 50 篇 arXiv 论文
python -m app.scripts.seed_feeds     # 加载 65 个 RSS 订阅源
```

---

## Makefile 命令

| 命令           | 说明                                    |
| -------------- | --------------------------------------- |
| `make dev`     | 同时启动后端和前端                      |
| `make infra`   | 启动 Docker 基础设施 (所有服务)         |
| `make setup`   | 完整项目初始化 (基础设施 + 依赖 + 迁移) |
| `make seed`    | 运行 arXiv 种子脚本 (50 篇论文)         |
| `make migrate` | 执行 Alembic 数据库迁移                 |
| `make lint`    | 代码检查: 后端 (ruff) + 前端 (eslint)   |
| `make test`    | 运行所有测试                            |
| `make clean`   | 清理缓存和构建产物                      |

运行 `make help` 查看所有可用命令。

---

## API 接口

所有接口挂载在 `/api/v1/` 下，主要分组：

| 分组       | 前缀                   | 说明                           |
| ---------- | ---------------------- | ------------------------------ |
| 论文       | `/papers`              | 增删改查、搜索、内容获取       |
| 内容       | `/papers/{id}/content` | Markdown 阅读器数据            |
| 数据分析   | `/analytics`           | 文库统计与洞察                 |
| 合集       | `/collections`         | 论文组织管理                   |
| 搜索       | `/search`              | 多模态搜索                     |
| OpenAlex   | `/openalex`            | 外部论文搜索 + 引用关系图构建  |
| 知识       | `/knowledge`           | 笔记图谱                       |
| 订阅源     | `/feeds`               | RSS 管理                       |
| 智能分析   | `/intelligence`        | AI 驱动的深度洞察              |

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
| AI       | LLM 集成 (可配置端点)                         |

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
