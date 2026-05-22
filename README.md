<p align="center">
  <img src="./assests/processed/kaleidoscope-icon-rounded.png" alt="Kaleidoscope" height="120" />
</p>

<h1 align="center">Kaleidoscope</h1>
<p align="center">
  <em>Academic Paper Intelligence Platform with Epistemic Analysis Engine</em>
</p>

<p align="center">
  <a href="./README.zh-CN.md">🇨🇳 中文文档</a> &nbsp;|&nbsp; <strong>🇬🇧 English</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12-blue?logo=python&logoColor=white" alt="Python 3.12" />
  <img src="https://img.shields.io/badge/nuxt-3.19-00DC82?logo=nuxt.js&logoColor=white" alt="Nuxt 3" />
  <img src="https://img.shields.io/badge/fastapi-0.115-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/tools-2075+-purple" alt="2075+ Tools" />
  <img src="https://img.shields.io/badge/MCP-compatible-blueviolet" alt="MCP Compatible" />
  <img src="https://img.shields.io/badge/license-KNCL%20v1.0-orange" alt="KNCL v1.0 License" />
</p>

---

## Overview

Kaleidoscope is a **full-stack research platform** for discovering, ingesting, reading, and analyzing academic papers. It combines a **Markdown-first** storage approach with a powerful **Epistemic Analysis Engine** — over 2,075 specialized AI tools that detect cognitive biases, logical fallacies, rhetorical distortions, and reasoning failures in academic claims.

### Key Features

- 📡 **ArXiv Ingestion** — Batch-fetch papers across categories, auto-convert to Markdown
- 📖 **Markdown Reader** — Read papers in-browser with table of contents, font controls, and section navigation
- 📊 **Analytics Dashboard** — Library insights: timeline, categories, top authors, keyword cloud, citation network
- 🔍 **Multi-modal Search** — Keyword, semantic, and claim-first search across your library
- 🧠 **Epistemic Analysis Engine** — 2,075+ AI-powered tools for deep reasoning analysis
- 🤖 **Autonomous Research Agent** — Multi-step research workflows with tool orchestration
- 🔌 **MCP Server** — Model Context Protocol integration for external AI agent access
- 📦 **Python SDK** — Programmatic access to all platform capabilities
- 🌐 **Bilingual UI** — Full English/Chinese internationalization
- 🔗 **Original Links** — One-click access to arXiv abstract, PDF, and ar5iv HTML

---

## Epistemic Analysis Engine

The core differentiator — a comprehensive taxonomy of 2,075+ detection tools organized across domains:

| Domain | Examples | Count |
|--------|----------|-------|
| Cognitive Biases | Anchoring, availability heuristic, confirmation bias, Dunning-Kruger | 200+ |
| Logical Fallacies | Ad hominem, straw man, false dilemma, slippery slope | 150+ |
| Causal Reasoning | Post hoc, reverse causation, spurious correlation, single cause | 100+ |
| Epistemic Scale | Ecological fallacy, composition/division, scope neglect | 80+ |
| Social Dynamics | Groupthink, pluralistic ignorance, reputation cascade, conformity | 100+ |
| Institutional | Citation cartel, credentialism, regulatory capture, peer review theater | 80+ |
| Communication | Sealioning, tone policing, jargon gatekeeping, strategic ambiguity | 80+ |
| Narrative | Origin myth, survivorship bias, teleological thinking, hindsight | 80+ |
| Decision Making | Premature closure, analysis paralysis, commitment escalation | 80+ |
| Methodology | P-hacking, Texas sharpshooter, streetlight effect, reification | 80+ |
| Temporal | Presentism, shifting baseline, recency illusion, end-of-history | 60+ |
| Emotion | Affect infusion, moral outrage substitution, empathy gap | 60+ |
| Power & Identity | Epistemic injustice, manufactured consent, tribal epistemology | 100+ |
| Technology | Algorithm opacity, filter bubble, automation bias, digital amnesia | 60+ |
| Meta-cognition | Blind spot bias, illusion of explanatory depth, calibration neglect | 60+ |
| + more | Ecology, virtue, attention, measurement, collective… | 600+ |

Each tool accepts domain-specific parameters and returns structured JSON with detection results, severity ratings, and actionable recommendations.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Nuxt 3)                       │
│   Vue 3 · TypeScript · Lucide Icons · GSAP Animations       │
└─────────────────────┬───────────────────────────────────────┘
                      │ REST API
┌─────────────────────▼───────────────────────────────────────┐
│                    Backend (FastAPI)                          │
│   SQLAlchemy · Celery · Pydantic · Structlog                 │
├──────────────────────────────────────────────────────────────┤
│  Agent Layer                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Tool         │  │ Research     │  │ MCP Server       │   │
│  │ Dispatcher   │  │ Runtime      │  │ (2075+ tools)    │   │
│  │ (2075 tools) │  │ (autonomous) │  │                  │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
├─────────────┬───────────┬───────────┬───────────────────────┤
│ PostgreSQL  │   Redis   │ Meilisearch│    Qdrant            │
│  (primary)  │  (cache)  │ (fulltext) │  (embeddings)        │
├─────────────┴───────────┴───────────┴───────────────────────┤
│  Neo4j (graph)  ·  MinIO (objects)  ·  GROBID (PDF)         │
└─────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
Kaleidoscope/
├── backend/
│   ├── app/
│   │   ├── api/v1/             # REST endpoints (20+ routers)
│   │   ├── clients/            # External API clients (arXiv, MinerU, OpenAlex, LLM)
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── services/           # 2075+ epistemic analysis services
│   │   │   ├── agent/          # Tool dispatcher & agent orchestration
│   │   │   ├── extraction/     # QA engine, summarizer
│   │   │   ├── search/         # Vector & hybrid search
│   │   │   ├── graph/          # Citation graph analysis
│   │   │   └── *.py            # Individual detection services
│   │   ├── mcp_server.py       # MCP protocol server (all tools exposed)
│   │   ├── tasks/              # Celery async tasks
│   │   ├── graph_db/           # Neo4j driver & queries
│   │   └── utils/              # Shared utilities
│   ├── kaleidoscope_sdk/       # Python SDK client
│   ├── alembic/                # Database migrations
│   ├── docker/                 # Docker Compose for infrastructure
│   └── pyproject.toml          # Python dependencies & tooling
│
├── frontend/                   # Nuxt 3 frontend
│   ├── components/             # Vue components
│   ├── pages/                  # File-based routing
│   ├── composables/            # Shared logic
│   ├── i18n/                   # en-US / zh-CN translations
│   └── nuxt.config.ts
│
└── docker-compose.yml          # Full-stack orchestration
```

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ / pnpm
- Python 3.12+ / uv (or pip)

### 1. Infrastructure

```bash
cd backend/docker
docker compose up -d   # PostgreSQL, Redis, Qdrant, Meilisearch, Neo4j, MinIO
```

### 2. Backend

```bash
cd backend
cp .env.example .env   # Configure API keys and DB URLs
uv sync                # Install dependencies
alembic upgrade head   # Run migrations
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
pnpm install
pnpm dev               # http://localhost:3000
```

### 4. MCP Server (for AI agent integration)

```bash
cd backend
python -m app.mcp_server   # Exposes 2075+ tools via MCP protocol
```

---

## SDK Usage

```python
from kaleidoscope_sdk import KaleidoscopeClient

client = KaleidoscopeClient(base_url="http://localhost:8000")

# Detect confirmation bias in a claim
result = await client.call_tool(
    "confirmation_bias_detect",
    claim="Studies consistently show X",
    evidence_pattern="Only favorable studies cited",
    domain="medicine"
)

# Run autonomous research
run = await client.research(
    query="What is the evidence for X?",
    depth="deep"
)
```

---

## API Endpoints

| Module       | Prefix                 | Description                              |
| ------------ | ---------------------- | ---------------------------------------- |
| Papers       | `/papers`              | CRUD, batch import, Markdown conversion  |
| Collections  | `/collections`         | Paper organization                       |
| Search       | `/search`              | Multi-modal search                       |
| Agent        | `/agent`               | Autonomous research agent                |
| Intelligence | `/intelligence`        | AI-powered insights                      |
| OpenAlex     | `/openalex`            | External search + citation graph builder |
| Knowledge    | `/knowledge`           | Note graph                               |
| Feeds        | `/feeds`               | RSS management                           |

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
| AI/LLM     | Configurable endpoint (OpenAI-compatible)     |
| Protocol   | MCP (Model Context Protocol)                  |

---

## Contributing

1. Fork the repo
2. Create your feature branch (`git checkout -b feat/amazing-feature`)
3. Commit with conventional commits (`feat:`, `fix:`, `docs:`)
4. Push and create a Pull Request

---

## License

This project is licensed under the Kaleidoscope Non-Commercial License
(KNCL) v1.0. Commercial use requires separate written permission or a
commercial license. See [LICENSE](LICENSE) for details.
