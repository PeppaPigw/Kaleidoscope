# Quality Guidelines

> Code quality standards for Kaleidoscope backend.

---

## Tooling

| Tool | Purpose | Command |
|------|---------|---------|
| **Ruff** | Linting + formatting | `ruff check .` / `ruff format .` |
| **mypy** | Static type checking | `mypy app/` |
| **pytest** | Testing | `pytest tests/ -v` |
| **pytest-cov** | Coverage | `pytest --cov=app --cov-report=html` |

---

## Code Standards

### Type Hints — Required Everywhere

```python
# ✅ Good
async def get_paper(doi: str) -> Paper | None:
    ...

# ❌ Bad
async def get_paper(doi):
    ...
```

### Async by Default

All I/O operations must be async:
```python
# ✅ Database, HTTP, file I/O
async with httpx.AsyncClient() as client:
    response = await client.get(url)

# ❌ Never use synchronous I/O in async context
requests.get(url)  # Blocks the event loop!
```

### Docstrings on All Public Functions

```python
async def search_papers(
    query: str,
    mode: SearchMode = SearchMode.HYBRID,
) -> SearchResult:
    """Search papers using keyword, semantic, or hybrid mode.
    
    Args:
        query: Search query (natural language or keywords)
        mode: Search mode — KEYWORD, SEMANTIC, or HYBRID
        
    Returns:
        SearchResult with ranked papers and provenance metadata
    """
```

---

## Testing

### Coverage Target: ≥ 80%

### Test Structure
```
tests/
├── conftest.py              # Shared fixtures (DB, clients, test data)
├── test_ingestion/
│   ├── test_rss_poller.py
│   └── test_deduplicator.py
├── test_parsing/
│   └── test_grobid_client.py
├── test_search/
│   ├── test_keyword.py
│   └── test_hybrid.py
└── test_api/
    ├── test_papers.py
    └── test_search.py
```

### Fixture Pattern
```python
@pytest.fixture
async def sample_paper(db_session):
    paper = Paper(doi="10.1234/test", title="Test Paper")
    db_session.add(paper)
    await db_session.commit()
    return paper
```

---

## Forbidden Patterns

| Pattern | Why | Alternative |
|---------|-----|------------|
| `import *` | Pollutes namespace | Explicit imports |
| `print()` for debugging | Lost in production | Use `structlog` |
| Synchronous I/O in async | Blocks event loop | Use `httpx`, `asyncpg` |
| Hardcoded API keys | Security risk | Use `.env` via `pydantic-settings` |
| Raw string SQL | SQL injection risk | Use SQLAlchemy ORM |
| `except Exception: pass` | Swallows errors | Handle specific exceptions |
