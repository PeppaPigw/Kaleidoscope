# API Guidelines

> Conventions for FastAPI endpoints in Kaleidoscope.

---

## API Structure

### Versioning

All API routes are versioned: `/api/v1/...`

### Route Organization

| Prefix | Router | Description |
|--------|--------|-------------|
| `/api/v1/papers` | `papers.py` | Paper CRUD, import, metadata |
| `/api/v1/search` | `search.py` | Keyword, semantic, hybrid search |
| `/api/v1/collections` | `collections.py` | Collections, tags, reading status |
| `/api/v1/graph` | `graph.py` | Citation graph, co-authorship, analytics |
| `/api/v1/authors` | `authors.py` | Author profiles, stats |
| `/api/v1/agent` | `agent.py` | MCP-compatible tools for AI agents |
| `/api/v1/export` | `export.py` | BibTeX, RIS, CSL-JSON export |

### Request/Response Patterns

```python
# Always use Pydantic schemas (never return ORM models directly)

# Request
class PaperImportRequest(BaseModel):
    identifier: str          # DOI, arXiv ID, URL, etc.
    identifier_type: Literal["doi", "arxiv", "pmid", "url", "title"]

# Response (always wrap in envelope for consistency)
class PaperResponse(BaseModel):
    id: UUID
    doi: str | None
    title: str
    abstract: str | None
    provenance: dict[str, ProvenanceInfo]  # Track AI vs publisher data

# List responses include pagination
class PaperListResponse(BaseModel):
    items: list[PaperResponse]
    total: int
    page: int
    per_page: int
```

### Pagination

Use cursor-based pagination for large datasets, offset-based for simple lists:

```python
@router.get("/papers")
async def list_papers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    order: Literal["asc", "desc"] = Query("desc"),
):
    ...
```

### Error Responses

```python
# Use HTTPException with structured detail
raise HTTPException(
    status_code=404,
    detail={"code": "PAPER_NOT_FOUND", "message": f"Paper {doi} not found"}
)
```

---

## Agent API (MCP Server)

The `/api/v1/agent` endpoints expose Kaleidoscope as a tool provider for AI agents via the Model Context Protocol:

| Tool | Description |
|------|-------------|
| `search_papers` | Hybrid search with natural language |
| `get_paper` | Get paper details by ID/DOI |
| `get_citations` | Forward/backward citation traversal |
| `get_similar` | Similar paper recommendations |
| `ask_papers` | RAG-based QA over paper collection |
| `get_trends` | Topic/keyword trend analysis |

All agent responses include `sources` with paper IDs and paragraph-level citations.

---

## Common Mistakes

1. **Don't put business logic in routers** — routers only validate input, call service, return output
2. **Don't return ORM models** — always map to Pydantic schemas
3. **Don't forget provenance** — every AI-derived field in responses must indicate its source
4. **Don't skip validation** — use Pydantic `Field(...)` with constraints
