# Kaleidoscope Backend

Academic Paper Intelligence Platform — Python/FastAPI backend.

## Quick Start

### 1. Start infrastructure services

```bash
cd docker
docker compose up -d
```

This starts: PostgreSQL, Redis, Meilisearch, Qdrant, Neo4j, MinIO, GROBID

### 2. Install dependencies

```bash
# Using uv (recommended)
uv sync

# Or pip
pip install -e ".[dev]"
```

### 3. Run database migrations

```bash
# Initialize alembic (first time only)
alembic revision --autogenerate -m "initial"
alembic upgrade head

# Seed RSS feeds
python -m app.seed_feeds
```

### 4. Start the API server

```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Start the Celery worker

```bash
celery -A app.worker worker --loglevel=info -Q ingestion,parsing,indexing
```

### 6. Start the Celery beat scheduler (for periodic RSS polling)

```bash
celery -A app.worker beat --loglevel=info
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Service Health**: http://localhost:8000/health/services

## Architecture

```
app/
├── main.py           # FastAPI app factory
├── config.py         # Settings (pydantic-settings)
├── models/           # SQLAlchemy ORM models
├── schemas/          # Pydantic request/response schemas
├── api/v1/           # FastAPI routers (thin layer)
├── services/         # Business logic
│   ├── ingestion/    # RSS polling, dedup, enrichment, PDF download
│   ├── parsing/      # GROBID PDF parsing
│   └── search/       # Keyword, vector, hybrid search
├── tasks/            # Celery async tasks
├── clients/          # External API clients (CrossRef, OpenAlex, S2, etc.)
└── utils/            # DOI, text, rate limiting utilities
```

## Key APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/papers/import` | POST | Import paper by DOI/arXiv ID |
| `/api/v1/papers/batch-import` | POST | Batch import |
| `/api/v1/papers` | GET | List papers (paginated) |
| `/api/v1/papers/{id}` | GET | Paper details |
| `/api/v1/search?q=...&mode=hybrid` | GET | Hybrid search |
| `/api/v1/feeds` | GET/POST | Manage RSS feeds |
| `/api/v1/feeds/poll` | POST | Trigger RSS polling |
