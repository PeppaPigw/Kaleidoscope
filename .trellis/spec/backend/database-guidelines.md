# Database Guidelines

> PostgreSQL, Neo4j, Qdrant, and Meilisearch conventions for Kaleidoscope.

---

## PostgreSQL (Primary Relational Store)

### ORM & Migrations

- **ORM**: SQLAlchemy 2.0+ (async mode with `asyncpg`)
- **Migrations**: Alembic with auto-generation
- Always review auto-generated migrations before applying

```bash
# Create migration
alembic revision --autogenerate -m "add_paper_versions_table"

# Apply
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Schema Design Principles

1. **Provenance on every AI-derived field**:
   ```python
   # Every field extracted by AI gets a provenance JSONB companion
   summary = Column(Text)
   summary_provenance = Column(JSONB)
   # provenance = {"source": "gpt-4o", "timestamp": "...", "confidence": 0.92}
   ```

2. **JSONB for semi-structured data**:
   ```python
   # Raw metadata from different sources
   raw_metadata = Column(JSONB)  # Original API response
   # Structured but variable fields
   keywords = Column(JSONB)  # ["quantum computing", "error correction"]
   ```

3. **Soft deletes** — never hard delete papers:
   ```python
   deleted_at = Column(DateTime, nullable=True, index=True)
   ```

4. **Timestamps on everything**:
   ```python
   created_at = Column(DateTime, server_default=func.now())
   updated_at = Column(DateTime, onupdate=func.now())
   ```

### Core Tables

```sql
-- Central paper entity
papers (
    id UUID PK,
    doi TEXT UNIQUE,              -- Canonical identifier
    arxiv_id TEXT,
    pmid TEXT,
    title TEXT NOT NULL,
    abstract TEXT,
    published_at DATE,
    paper_type TEXT,              -- article, review, preprint, etc.
    oa_status TEXT,               -- gold, green, bronze, closed
    pdf_path TEXT,                -- MinIO object key
    remote_urls JSONB,           -- [{url, source, type}]
    raw_metadata JSONB,          -- Original source data
    parser_version TEXT,         -- For reprocessing tracking
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ
)

-- Author (disambiguated)
authors (
    id UUID PK,
    openalex_id TEXT UNIQUE,
    orcid TEXT,
    display_name TEXT NOT NULL,
    aliases JSONB,               -- Alternative names
    h_index INT,
    institution_id UUID FK → institutions
)

-- Paper-Author link (ordered)
paper_authors (
    paper_id UUID FK,
    author_id UUID FK,
    position INT,                -- Author order
    is_corresponding BOOLEAN
)

-- Journal / Conference
venues (
    id UUID PK,
    name TEXT NOT NULL,
    type TEXT,                   -- journal, conference, preprint_server
    issn TEXT,
    sjr_quartile TEXT,
    ccf_rank TEXT,
    impact_factor FLOAT
)

-- Structured experiment results
experiments (
    id UUID PK,
    paper_id UUID FK,
    dataset_name TEXT,
    method_name TEXT,
    metric_name TEXT,
    metric_value FLOAT,
    is_primary BOOLEAN,
    context JSONB                 -- Additional context
)
```

### Query Patterns

- **Always use async sessions**:
  ```python
  async with get_session() as session:
      result = await session.execute(select(Paper).where(Paper.doi == doi))
  ```

- **Batch operations** for ingestion:
  ```python
  # Use insert().on_conflict_do_update() for upserts
  stmt = insert(Paper).values(papers_data)
  stmt = stmt.on_conflict_do_update(
      index_elements=['doi'],
      set_={...}
  )
  ```

- **Never N+1** — always eager load relations or use explicit joins

---

## Neo4j (Citation & Knowledge Graph)

### Node Labels

| Label | Properties | Source |
|-------|-----------|--------|
| `Paper` | `paper_id`, `doi`, `title`, `year` | Synced from PostgreSQL |
| `Author` | `author_id`, `name` | Synced from PostgreSQL |
| `Institution` | `institution_id`, `name` | Synced from PostgreSQL |
| `Topic` | `topic_id`, `name` | OpenAlex concepts / BERTopic |
| `Dataset` | `name`, `domain` | Extracted from papers |
| `Method` | `name`, `category` | Extracted from papers |

### Relationship Types

| Type | From → To | Properties |
|------|-----------|-----------|
| `CITES` | Paper → Paper | `context` (citation sentence) |
| `SIMILAR_TO` | Paper → Paper | `score`, `method` (embedding/co-citation) |
| `AUTHORED_BY` | Paper → Author | `position` |
| `AFFILIATED_WITH` | Author → Institution | `start_year`, `end_year` |
| `ABOUT` | Paper → Topic | `relevance` |
| `USES_METHOD` | Paper → Method | |
| `USES_DATASET` | Paper → Dataset | |
| `SUPPORTS` | Paper → Paper | On claim level |
| `CONTRADICTS` | Paper → Paper | On claim level |
| `EXTENDS` | Paper → Paper | |

### Sync Strategy

PostgreSQL is source of truth. Neo4j is synced via:
1. **On write**: Celery task triggered after paper insert/update
2. **Batch rebuild**: Weekly full re-sync for consistency

---

## Qdrant (Vector Embeddings)

### Collections

| Collection | Model | Dimension | Content |
|-----------|-------|-----------|---------|
| `paper_embeddings` | SPECTER2 | 768 | Title + abstract |
| `chunk_embeddings` | BGE-M3 | 1024 | Full-text paragraph chunks |
| `claim_embeddings` | BGE-M3 | 1024 | Extracted claims |
| `figure_embeddings` | CLIP | 512 | Figure images |

### Payload Fields

Always store `paper_id`, `source`, `created_at` in point payloads for filtering.

---

## Meilisearch (Full-Text Keyword Search)

### Index: `papers`

- **Searchable**: `title`, `abstract`, `keywords`, `author_names`
- **Filterable**: `year`, `venue`, `paper_type`, `oa_status`, `collection_ids`
- **Sortable**: `year`, `citation_count`, `created_at`

### Sync

On every paper insert/update, a Celery task updates the Meilisearch index.

---

## Common Mistakes to Avoid

1. **Don't query Neo4j for data that PostgreSQL has** — use Neo4j only for graph traversals
2. **Don't store large text in Neo4j** — only IDs and lightweight properties
3. **Don't forget to update search indexes** when papers change — always trigger index tasks
4. **Don't use raw SQL** unless for performance-critical queries — use SQLAlchemy ORM
5. **Don't skip provenance** — every AI-generated field must track its source
