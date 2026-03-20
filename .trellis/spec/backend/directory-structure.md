# Backend Directory Structure

> How the Kaleidoscope backend codebase is organized.

---

## Overview

The backend follows a **modular monolith** pattern — a single deployable with clear module boundaries that can be split into microservices later if needed.

---

## Directory Layout

```
backend/
├── app/
│   ├── main.py                    # ✅ FastAPI app factory, middleware, CORS, exception handlers
│   ├── config.py                  # ✅ Settings via pydantic-settings (.env)
│   ├── dependencies.py            # ✅ Async DB session factory (get_db)
│   ├── exceptions.py              # ✅ Custom exception hierarchy
│   ├── worker.py                  # ✅ Celery app configuration
│   ├── seed_feeds.py              # ✅ RSS feed seed script (62 sources from source.md)
│   │
│   ├── models/                    # ✅ SQLAlchemy ORM models
│   │   ├── __init__.py            # ✅ Re-exports all models for Alembic
│   │   ├── base.py                # ✅ Base + UUIDPrimaryKeyMixin + TimestampMixin
│   │   ├── paper.py               # ✅ Paper, PaperVersion, PaperReference
│   │   ├── author.py              # ✅ Author, PaperAuthor, Institution
│   │   ├── venue.py               # ✅ Venue (journals/conferences with rankings)
│   │   └── feed.py                # ✅ RSSFeed (ETag/Last-Modified tracking)
│   │   # Future (P1+):
│   │   # ├── dataset.py           # Dataset, Method, Metric
│   │   # ├── claim.py             # Claim, Evidence
│   │   # ├── collection.py        # Collection, Tag, ReadingStatus
│   │   # └── user.py              # User, Role, Permission
│   │
│   ├── schemas/                   # ✅ Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── paper.py               # ✅ Import/response/list schemas
│   │   ├── search.py              # ✅ Search request/response/hit
│   │   └── feed.py                # ✅ RSS feed CRUD schemas
│   │   # Future: collection.py, author.py, graph.py
│   │
│   ├── api/                       # ✅ FastAPI routers (thin layer)
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── papers.py          # ✅ /api/v1/papers (import, list, detail, delete)
│   │       ├── search.py          # ✅ /api/v1/search (keyword/semantic/hybrid)
│   │       └── feeds.py           # ✅ /api/v1/feeds (CRUD + poll trigger)
│   │       # Future:
│   │       # ├── collections.py   # /api/v1/collections
│   │       # ├── graph.py         # /api/v1/graph
│   │       # ├── authors.py       # /api/v1/authors
│   │       # └── agent.py         # /api/v1/agent (MCP-compatible)
│   │
│   ├── services/                  # Business logic (core layer)
│   │   ├── __init__.py
│   │   ├── ingestion/             # ✅ Paper ingestion pipeline
│   │   │   ├── __init__.py
│   │   │   ├── rss_poller.py      # ✅ RSS feed polling (ETag/Last-Modified)
│   │   │   ├── deduplicator.py    # ✅ DOI/arXiv/title-based dedup (≥90%)
│   │   │   ├── metadata_enricher.py # ✅ CrossRef→OpenAlex→S2 cascade
│   │   │   └── pdf_downloader.py  # ✅ 6-step PDF acquisition cascade
│   │   ├── parsing/               # ✅ Document parsing
│   │   │   ├── __init__.py
│   │   │   └── grobid_client.py   # ✅ GROBID TEI XML parsing
│   │   │   # Future: pdf_figures.py, reference_linker.py, ocr.py
│   │   ├── search/                # ✅ Search & retrieval
│   │   │   ├── __init__.py
│   │   │   ├── keyword_search.py  # ✅ Meilisearch full-text search
│   │   │   ├── vector_search.py   # ✅ Qdrant SPECTER2 vector search
│   │   │   └── hybrid_search.py   # ✅ RRF fusion (k=60)
│   │   │   # Future: graph_search.py
│   │   ├── extraction/            # 🔲 LLM-powered extraction (P1)
│   │   │   └── __init__.py
│   │   └── graph/                 # 🔲 Graph operations (P1)
│   │       └── __init__.py
│   │   # Future: recommendation.py, collection_service.py, export_service.py
│   │
│   ├── tasks/                     # ✅ Celery async tasks
│   │   ├── __init__.py
│   │   └── ingest_tasks.py        # ✅ poll_rss_feeds, ingest_paper, acquire_pdf,
│   │                              #    parse_pdf_task, index_paper_task
│   │   # Future: extract_tasks.py, notification_tasks.py
│   │
│   ├── clients/                   # ✅ External API clients
│   │   ├── __init__.py
│   │   ├── crossref.py            # ✅ DOI lookup + title search
│   │   ├── openalex.py            # ✅ Works/authors/citations
│   │   ├── semantic_scholar.py    # ✅ Papers/citations/OA PDF
│   │   ├── unpaywall.py           # ✅ OA PDF discovery
│   │   └── arxiv.py               # ✅ Atom XML parsing + PDF URL
│   │   # Future: papers_with_code.py, llm_client.py
│   │
│   ├── graph_db/                  # 🔲 Neo4j operations (P1)
│   │   └── __init__.py
│   │   # Future: driver.py, queries.py, sync.py
│   │
│   └── utils/                     # ✅ Shared utilities
│       ├── __init__.py
│       ├── doi.py                 # ✅ DOI normalization, arXiv/PMID extraction
│       ├── text.py                # ✅ Title normalization, fuzzy matching
│       └── rate_limiter.py        # ✅ Async token-bucket rate limiter
│       # Future: provenance.py
│
├── alembic/                       # ✅ Database migrations
│   ├── env.py                     # ✅ Async-compatible migration runner
│   ├── script.py.mako             # ✅ Migration template
│   └── versions/                  # ✅ Auto-generated migration files
│       └── 625357ed3fc8_initial_p0_schema.py
│
├── tests/
│   └── conftest.py                # 🔲 Shared fixtures (P0.5)
│   # Future: test_ingestion/, test_parsing/, test_search/, test_api/
│
├── docker/
│   └── docker-compose.yml         # ✅ PostgreSQL, Redis, Meilisearch, Qdrant,
│                                  #    Neo4j, MinIO, GROBID
│   # Future: Dockerfile (for production deployment)
│
├── pyproject.toml                 # ✅ Dependencies + [tool.setuptools] + ruff config
├── alembic.ini                    # ✅ Alembic configuration
├── .env.example                   # ✅ Template for all env vars
└── README.md                      # ✅ Quickstart guide + architecture
```

---

## Module Boundaries

### Rules

1. **Routers** (`api/`) — Thin layer. Only request validation, call service, return response. No business logic.
2. **Services** (`services/`) — All business logic lives here. Services can call other services.
3. **Models** (`models/`) — SQLAlchemy models. No business logic, only data definition.
4. **Schemas** (`schemas/`) — Pydantic models for API input/output. Separate from ORM models.
5. **Tasks** (`tasks/`) — Celery tasks. Thin wrappers around service calls. Handle retries and error reporting.
6. **Clients** (`clients/`) — External API wrappers. Handle rate limiting, retries, response parsing.

### Dependency Direction

```
api/ → services/ → models/
                  → clients/
                  → graph_db/
tasks/ → services/
```

**Never**: `models/` → `services/`, `clients/` → `services/`, `api/` → `tasks/` directly

---

## Naming Conventions

| Entity | Convention | Example |
|--------|-----------|---------|
| Files | `snake_case.py` | `pdf_downloader.py` |
| Classes | `PascalCase` | `PaperService` |
| Functions | `snake_case` | `fetch_by_doi()` |
| Constants | `UPPER_SNAKE` | `MAX_RETRIES` |
| DB tables | `snake_case`, plural | `papers`, `paper_versions` |
| DB columns | `snake_case` | `published_at`, `citation_count` |
| API paths | `kebab-case` | `/api/v1/papers/{id}/related-work` |

---

## Key Patterns

### Service Pattern

```python
# services/ingestion/rss_poller.py
class RSSPollerService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis

    async def poll_feed(self, feed_url: str) -> list[Paper]:
        """Poll a single RSS feed and return new papers."""
        ...
```

### Client Pattern

```python
# clients/crossref.py
class CrossRefClient:
    BASE_URL = "https://api.crossref.org"
    
    def __init__(self, email: str, rate_limiter: RateLimiter):
        self.email = email
        self.rate_limiter = rate_limiter

    async def get_work(self, doi: str) -> CrossRefWork:
        """Fetch metadata for a DOI."""
        ...
```
