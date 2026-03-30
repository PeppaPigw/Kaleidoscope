<p align="center">
  <img src="./assests/processed/kaleidoscope-icon-rounded.png" alt="Kaleidoscope" height="120" />
</p>

<h1 align="center">Kaleidoscope</h1>
<p align="center">
  <em>Academic Paper Intelligence Platform</em>
</p>

<p align="center">
  <a href="./README.zh-CN.md">🇨🇳 中文文档</a> &nbsp;|&nbsp; <strong>🇬🇧 English</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12-blue?logo=python&logoColor=white" alt="Python 3.12" />
  <img src="https://img.shields.io/badge/nuxt-3.19-00DC82?logo=nuxt.js&logoColor=white" alt="Nuxt 3" />
  <img src="https://img.shields.io/badge/fastapi-0.115-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License" />
</p>

---

## Overview

Kaleidoscope is a **full-stack research platform** for discovering, ingesting, reading, and analyzing academic papers. It features a **Markdown-first** storage approach — papers are converted from HTML/PDF to Markdown via MinerU, eliminating the need for PDF storage while enabling rich in-browser reading.

### Key Features

- 📡 **ArXiv Ingestion** — Batch-fetch papers across categories, auto-convert to Markdown
- 📖 **Markdown Reader** — Read papers in-browser with table of contents, font controls, and section navigation
- 📊 **Analytics Dashboard** — Library insights: timeline, categories, top authors, keyword cloud, citation network
- 🔍 **Multi-modal Search** — Keyword, semantic, and claim-first search across your library
- 🧠 **AI-Powered Analysis** — Evidence lab, cross-paper comparison, contradiction detection
- 🌐 **Bilingual UI** — Full English/Chinese internationalization
- 🔗 **Original Links** — One-click access to arXiv abstract, PDF, and ar5iv HTML

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (Nuxt 3)                   │
│  Vue 3 · TypeScript · Lucide Icons · GSAP Animations    │
└─────────────────────┬───────────────────────────────────┘
                      │ REST API
┌─────────────────────▼───────────────────────────────────┐
│                   Backend (FastAPI)                      │
│  SQLAlchemy · Celery · Pydantic · Structlog             │
├─────────────┬───────────┬───────────┬───────────────────┤
│ PostgreSQL  │   Redis   │ Meilisearch│    Qdrant        │
│  (primary)  │  (cache)  │ (fulltext) │  (embeddings)    │
├─────────────┴───────────┴───────────┴───────────────────┤
│  Neo4j (graph)  ·  MinIO (objects)  ·  GROBID (PDF)     │
└─────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
Kaleidoscope/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── api/v1/             # REST endpoints (20+ routers)
│   │   ├── clients/            # External API clients (arXiv, MinerU, OpenAlex…)
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── services/           # Business logic (parsing, search, analysis…)
│   │   ├── tasks/              # Celery async tasks
│   │   ├── scripts/            # CLI scripts (seeder, feeds)
│   │   ├── graph_db/           # Neo4j driver & queries
│   │   └── utils/              # Shared utilities
│   ├── alembic/                # Database migrations
│   ├── docker/                 # Docker Compose for infrastructure
│   ├── tests/                  # Pytest test suite
│   └── pyproject.toml          # Python dependencies & tooling
│
├── frontend/                   # Nuxt 3 frontend
│   ├── app/
│   │   ├── pages/              # Route pages (dashboard, reader, analysis…)
│   │   ├── components/         # Vue components (14 feature domains)
│   │   ├── composables/        # Shared composables (useApi, useTranslation)
│   │   ├── layouts/            # App layouts
│   │   └── assets/             # CSS design system
│   ├── nuxt.config.ts
│   └── package.json
│
├── docs/                       # Project documentation
│
├── docker-compose.yml          # → backend/docker/docker-compose.yml
├── Makefile                    # Development shortcuts
└── README.md
```

---

## Quick Start

### Prerequisites

- **Python 3.12+** and **pip**
- **Node.js 20+** and **pnpm**
- **Docker** and **Docker Compose**

### 1. Clone & Setup

```bash
git clone <repo-url> Kaleidoscope
cd Kaleidoscope
```

### 2. Start Infrastructure

```bash
docker compose up -d
# Starts: PostgreSQL, Redis, Meilisearch, Qdrant, Neo4j, MinIO, GROBID
```

### 3. Backend

```bash
cd backend
cp .env.example .env        # Edit with your API keys
pip install -e ".[dev]"     # Install with dev dependencies
alembic upgrade head        # Run migrations
uvicorn app.main:create_app --factory --reload --port 8000
```

### 4. Frontend

```bash
cd frontend
pnpm install
pnpm dev                    # http://localhost:3000
```

### 5. Seed Initial Data (Optional)

```bash
cd backend
python -m app.scripts.seed_arxiv     # Fetch 50 arXiv papers via MinerU
python -m app.scripts.seed_feeds     # Load 65 RSS feed sources
```

---

## Makefile Commands

| Command        | Description                             |
| -------------- | --------------------------------------- |
| `make dev`     | Start backend + frontend in parallel    |
| `make infra`   | Docker compose up (all services)        |
| `make seed`    | Run arXiv seeder (50 papers)            |
| `make migrate` | Run Alembic migrations                  |
| `make lint`    | Lint backend (ruff) + frontend (eslint) |
| `make test`    | Run all tests                           |
| `make clean`   | Remove caches and build artifacts       |

---

## API Endpoints

All endpoints are under `/api/v1/`. Key groups:

| Group        | Prefix                 | Description                     |
| ------------ | ---------------------- | ------------------------------- |
| Papers       | `/papers`              | CRUD, search, content retrieval |
| Content      | `/papers/{id}/content` | Markdown reader data            |
| Analytics    | `/analytics`           | Library statistics & insights   |
| Collections  | `/collections`         | Paper organization              |
| Search       | `/search`              | Multi-modal search              |
| Knowledge    | `/knowledge`           | Note graph                      |
| Feeds        | `/feeds`               | RSS management                  |
| Intelligence | `/intelligence`        | AI-powered insights             |

Interactive docs available at `http://localhost:8000/docs` when backend is running.

---

## Tech Stack

| Layer      | Technology                                    |
| ---------- | --------------------------------------------- |
| Frontend   | Nuxt 3, Vue 3, TypeScript, Lucide Icons, GSAP |
| Backend    | FastAPI, SQLAlchemy 2, Celery, Pydantic v2    |
| Database   | PostgreSQL 16, Redis 7                        |
| Search     | Meilisearch, Qdrant (vector)                  |
| Graph      | Neo4j 5                                       |
| Storage    | MinIO (S3-compatible)                         |
| PDF Parser | GROBID, MinerU API                            |
| AI         | LLM integration (configurable endpoint)       |

---

## Contributing

1. Fork the repo
2. Create your feature branch (`git checkout -b feat/amazing-feature`)
3. Commit with conventional commits (`feat:`, `fix:`, `docs:`)
4. Push and create a Pull Request

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
