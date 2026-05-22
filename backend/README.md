# Kaleidoscope Backend

Academic Paper Intelligence Platform — Python/FastAPI backend with 2,075+ epistemic analysis tools.

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
alembic upgrade head

# Seed RSS feeds
python -m app.scripts.seed_feeds

# Seed 50 arXiv papers via MinerU
python -m app.scripts.seed_arxiv
```

### 4. Start the API server

```bash
uvicorn app.main:create_app --factory --reload --port 8000
```

### 5. Start the Celery worker

```bash
celery -A app.worker worker --loglevel=info -Q ingestion,parsing,indexing
```

### 6. Start the MCP server (optional)

```bash
python -m app.mcp_server
```

Exposes all 2,075+ epistemic analysis tools via Model Context Protocol for external AI agents.

## API Documentation

Once running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Architecture

```
app/
├── main.py              # FastAPI app factory
├── config.py            # Settings (pydantic-settings)
├── mcp_server.py        # MCP protocol server (2075+ tools)
├── models/              # SQLAlchemy ORM models
├── schemas/             # Pydantic request/response schemas
├── api/v1/              # FastAPI routers
├── services/            # 2075+ epistemic analysis services
│   ├── agent/           # Tool dispatcher & orchestration
│   │   └── tool_dispatcher.py  # Central tool registry (2075 tools)
│   ├── extraction/      # QA engine, summarizer
│   ├── search/          # Keyword, vector, hybrid search
│   ├── graph/           # Citation graph analysis
│   └── *.py             # Individual detection services
├── tasks/               # Celery async tasks
├── clients/             # External API clients (arXiv, MinerU, LLM…)
├── graph_db/            # Neo4j driver & queries
└── utils/               # Shared utilities
```

## Key APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/papers/import` | POST | Import paper by DOI/arXiv ID |
| `/api/v1/papers/batch-import` | POST | Batch import |
| `/api/v1/papers` | GET | List papers (paginated) |
| `/api/v1/papers/{id}` | GET | Paper details |
| `/api/v1/search?q=...&mode=hybrid` | GET | Hybrid search |
| `/api/v1/agent/run` | POST | Execute research agent |
| `/api/v1/agent/tools` | GET | List available tools |
| `/api/v1/feeds` | GET/POST | Manage RSS feeds |

## Python SDK

```python
from kaleidoscope_sdk import KaleidoscopeClient

client = KaleidoscopeClient(base_url="http://localhost:8000")
result = client.tool("confirmation_bias_detect", {
    "claim": "Only evidence supporting the hypothesis was cited",
    "domain": "research_methodology"
})
```

## License

KNCL v1.0 — see [LICENSE](../LICENSE).
