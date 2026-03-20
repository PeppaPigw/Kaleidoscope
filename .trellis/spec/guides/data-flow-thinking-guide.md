# Data Flow Thinking Guide

> Pre-implementation checklist for features that touch the Kaleidoscope data pipeline.

---

## Overview

Kaleidoscope has a complex data flow: external APIs → ingestion → multi-store (PostgreSQL + Neo4j + Qdrant + Meilisearch) → API → frontend. This guide helps you think through all the layers before coding.

---

## Pre-Implementation Checklist

### 1. Where Does the Data Come From?

- [ ] Which external APIs provide this data? (CrossRef, OpenAlex, S2, etc.)
- [ ] Is it from PDF parsing (GROBID)?
- [ ] Is it LLM-extracted? → Must include provenance + confidence
- [ ] Is it user-generated? → Must handle privacy/permissions

### 2. Where Does the Data Live?

- [ ] **PostgreSQL** — Is this relational data? Does it need transactions?
- [ ] **Neo4j** — Is this a graph relationship? (citation, co-authorship, similarity)
- [ ] **Qdrant** — Does this need vector search? What embedding model?
- [ ] **Meilisearch** — Does this need full-text keyword search?
- [ ] **MinIO** — Is this a file? (PDF, figure, supplementary)
- [ ] **Redis** — Is this a cache? What's the TTL? What invalidates it?

### 3. How Are Stores Synced?

- [ ] If data changes in PostgreSQL, which other stores need updating?
- [ ] Is the sync real-time (trigger), or batched (Celery task)?
- [ ] What happens if sync fails? (idempotent retry? manual repair?)

### 4. How Does It Surface to the User?

- [ ] Which API endpoint serves this data?
- [ ] What's the response schema? Does it match an existing type?
- [ ] Which frontend component displays it?
- [ ] Is there a loading/error/empty state?

### 5. Quality & Provenance

- [ ] If AI-generated: source model, timestamp, confidence tracked?
- [ ] Is there a way for users to correct/override?
- [ ] Is it distinguishable from publisher-sourced data in the UI?

---

## Common Pitfalls

| Pitfall | Prevention |
|---------|-----------|
| Adding a PostgreSQL field but forgetting Meilisearch index update | Always update the index sync task |
| Adding a Neo4j relationship type but not updating the graph API | Update both `graph_db/queries.py` and `api/v1/graph.py` |
| Adding an LLM extraction field without provenance | Every AI field needs `{source, confidence, timestamp}` |
| Adding a new search filter without backend support | API filter → Meilisearch filterable attribute → frontend filter UI |
| Adding vector search without considering stale embeddings | Reindex task for updated papers |

---

## Decision Tree: Which Database?

```
Is it a relationship between entities?
├── Yes → Neo4j
│   └── Also store foreign keys in PostgreSQL for backup
└── No
    ├── Is it searchable text?
    │   ├── Keyword search → Meilisearch
    │   └── Semantic search → Qdrant (embed + index)
    ├── Is it a file?
    │   └── MinIO → store path in PostgreSQL
    └── Is it structured data?
        └── PostgreSQL
            └── Semi-structured → JSONB column
```
