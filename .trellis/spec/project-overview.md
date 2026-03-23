# Kaleidoscope — Project Overview

> Literature dataset analysis and management platform.

---

## Vision

Kaleidoscope is a **literature-centric knowledge platform** that aggregates, structures, and intelligently analyzes academic papers from 65+ sources. It serves both human researchers and downstream AI agents.

**Key differentiators**:
1. Multi-source ingestion with full-text processing (not just metadata)
2. Hybrid search: keyword + semantic + citation graph
3. Deep paper analysis: claims, methods, experiments extraction
4. Agent-ready API (MCP Server) — upstream knowledge platform for AI workflows

---

## Reference Documents

| Document | Location | Description |
|----------|----------|-------------|
| Feature Requirements | `Memo/FeasibilityAnalysis.md` | 240 features across 25 modules with feasibility ratings |
| Data Sources | `source.md` | 65 RSS feeds, full-text acquisition strategies per publisher |
| Project Notes | `1temp.md` | Reference projects, UI tools, API notes |

---

## Technology Stack (Decided)

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Primary Language** | Python 3.12+ | ML/NLP ecosystem, GROBID integration, scientific computing |
| **Web Framework** | FastAPI | Async, OpenAPI auto-docs, Pydantic validation |
| **Relational DB** | PostgreSQL 16 + JSONB | Structured data + semi-structured metadata |
| **Graph DB** | Neo4j Community | Citation graph, co-authorship, knowledge graph |
| **Vector DB** | Qdrant | High-performance vector search, self-hosted |
| **Full-text Search** | Meilisearch | Lightweight, CJK support, typo-tolerant |
| **Task Queue** | Celery + Redis | Async ingestion, batch processing, scheduling |
| **Object Storage** | MinIO (dev) / S3 (prod) | PDF storage, figures, supplementary materials |
| **Cache** | Redis | Query cache, rate limiting, session |
| **PDF Parsing** | GROBID (Docker) | Structure-aware academic PDF parsing |
| **LLM** | GPT-4o / Claude API | Summarization, extraction, QA |
| **Embedding** | SPECTER2 / BGE-M3 | Academic-domain embeddings |
| **Frontend** | Next.js + React | SSR, routing, modern UI |
| **Visualization** | Cytoscape.js + ECharts | Graph viz + charts |

---

## External APIs (Free Tier)

| API | Purpose | Rate Limit | Auth |
|-----|---------|-----------|------|
| CrossRef | DOI metadata, references | 50 req/s (polite pool) | None (email header) |
| OpenAlex | Papers, authors, institutions, concepts | 100k/day | None |
| Semantic Scholar | Citations, embeddings, OA PDF | 100 req/5min (free) | API Key (free) |
| Unpaywall | Open access PDF locations | 100k/day | Email |
| Papers With Code | Code/dataset links | Reasonable | None |
| arXiv API | Paper metadata, versions | 3s interval | None |
| PubMed E-utilities | Biomedical literature | 3 req/s (key: 10 req/s) | API Key (free) |
| Springer Nature | OA full-text XML | 5k/day | API Key (free) |
| Elsevier (TDM) | Full-text XML (institutional) | Varies | API Key + institution |

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                     │
│  Reader │ Search │ Collections │ Graph Viz │ Dashboard      │
└──────────────────────┬─────────────────────────────────────┘
                       │ REST / WebSocket
┌──────────────────────┴─────────────────────────────────────┐
│                   API Layer (FastAPI)                       │
│  Paper API │ Search API │ Graph API │ Agent API (MCP)      │
└──────┬──────────┬───────────┬──────────┬───────────────────┘
       │          │           │          │
┌──────┴──┐ ┌────┴────┐ ┌───┴───┐ ┌───┴────┐
│ Postgres│ │Meilisearch│ │ Neo4j │ │ Qdrant │
│ (data)  │ │ (search)  │ │(graph)│ │(vector)│
└─────────┘ └──────────┘ └───────┘ └────────┘
       ▲
┌──────┴─────────────────────────────────────┐
│           Processing Pipeline              │
│  RSS Poller → Download → GROBID → LLM     │
│  Celery + Redis                            │
└──────────────────┬─────────────────────────┘
                   │
            ┌──────┴──────┐
            │ MinIO / S3  │
            │ (PDF store) │
            └─────────────┘
```

---

## Development Phases

### Phase 0 — Foundation ✅ Complete (2026-03-20)
- [x] Project scaffolding (monorepo structure)
- [x] Database schemas (PostgreSQL + Alembic migrations)
- [x] GROBID Docker setup
- [x] Docker Compose (7 services: PostgreSQL, Redis, Meilisearch, Qdrant, Neo4j, MinIO, GROBID)
- [x] Configuration management (pydantic-settings + .env)
- [x] Exception hierarchy & error handling

### Phase 1 — Core (P0 Features) ✅ Complete (2026-03-21)
- [x] Multi-source paper ingestion (#1-8): RSS poller, deduplicator, metadata enricher
- [x] PDF download & parsing (#9-16): 6-step cascade + GROBID client
- [x] Keyword + semantic search (#17-20): Meilisearch + Qdrant + RRF hybrid
- [x] ORM models: Paper, Author, Venue, RSSFeed, PaperReference, PaperVersion
- [x] External API clients: CrossRef, OpenAlex, Semantic Scholar, Unpaywall, arXiv
- [x] Celery async tasks: poll, ingest, acquire PDF, parse, index
- [x] FastAPI API routers: papers, search, feeds + health checks
- [x] 62 RSS feed seed data
- [x] Full-text content persistence (PDF, TeX, XML)
- [x] GROBID parsing integration (content-type routing)
- [x] End-to-end PMID, URL, title imports
- [x] Commit-before-queue race condition fix
- [x] Sequential task chain: ingest → acquire → parse → index
- [ ] Basic reading view (#33-36) — frontend, deferred to P2
- [ ] Unit tests (≥ 80% coverage target)

### Phase 2 — Experience (P1 Features) ✅ Complete (2026-03-21)
- [x] Collections, tags, reading status (#49-56) — models, schemas, service, API
- [x] LLM-powered summaries & QA (#37-40) — client, chunker, summarizer, extractor, QA engine
- [x] Citation graph & recommendations (#65-72) — Neo4j driver, queries, graph service, recommendation
- [x] Agent Tool API (#97-104) — 13 tools, dispatcher, REST API endpoints
- [x] Citation export (BibTeX, RIS, CSL-JSON)
- [x] Smart collections (saved filter queries)
- [x] User-scoped workflow state (per-user reading status, collections, tags)
- [x] Graph sync wired into ingestion pipeline
- [x] 3-signal recommendation (graph + embedding similarity via RRF)
- [x] Idempotent reference materialization
- [x] Process-level search service singletons
- [x] Database migration for P1+P2 models (a1b2c3d4e5f6)
- [ ] Integration testing with live services

### Phase 3 — Intelligence (P2 Features) ✅ Complete (2026-03-21)
- [x] Advanced filtering (#25-32) — faceted navigation, multi-field queries, custom scoring
- [x] Trend analysis (#73-80) — BERTopic clustering, hot topics, emerging entities
- [x] Writing support (#189-200) — related work generation, gap analysis, rebuttal
- [x] Monitoring & automation (#201-212) — alerts, digests, event-action pipelines
- [x] Deep paper analysis (#81-88) — innovation analysis, method extraction, validity
- [x] Local PDF intelligence (#41-48) — batch import, dedup, library management

### Phase 4 — Deep Analysis (P3 Features) ✅ Complete (2026-03-21)
- [x] Claim extraction (#129-140) — atomic claim + evidence extraction with LLM, evidence assessment
- [x] Cross-paper reasoning (#165-176) — multi-doc synthesis, timeline, essential/bridge papers
- [x] Figure/table intelligence (#153-164) — classify, extract, cross-paper result aggregation
- [x] Personal knowledge (#213-224) — reading log, annotations, glossary, flashcards with SM-2

