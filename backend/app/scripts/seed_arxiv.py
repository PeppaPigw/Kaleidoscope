"""Seed script — fetch 100 arXiv papers, convert to Markdown via MinerU, store in DB.

Usage:
    cd backend && python -m app.scripts.seed_arxiv

Strategy:
    1. Query arXiv API for recent papers across ML/AI categories
    2. For each paper, create a Paper row with metadata
    3. Use MinerU VLM model on arXiv PDF URL to get full-text markdown
       (ar5iv HTML is JS-rendered so only yields the abstract page)
    4. Upload extracted images to OSS, rewrite markdown src URLs
    5. Store `full_text_markdown` in the paper row
    6. Store original arXiv links in `remote_urls` for user navigation
"""

import asyncio
from datetime import datetime, timezone

import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

# arXiv categories to sample from
ARXIV_CATEGORIES = [
    "cs.AI",  # Artificial Intelligence
    "cs.LG",  # Machine Learning
    "cs.CL",  # Computation and Language (NLP)
    "cs.CV",  # Computer Vision
    "cs.IR",  # Information Retrieval
]

# 20 papers per category = 100 total
PAPERS_PER_CATEGORY = 20


async def fetch_arxiv_papers(category: str, max_results: int) -> list[dict]:
    """Fetch recent papers from arXiv API for a given category."""
    import httpx

    url = "https://export.arxiv.org/api/query"
    params = {
        "search_query": f"cat:{category}",
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": max_results,
    }

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()

    return _parse_arxiv_feed(resp.text)


def _parse_arxiv_feed(xml_text: str) -> list[dict]:
    """Parse arXiv Atom XML feed into list of paper dicts."""
    import re
    from lxml import etree

    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }
    root = etree.fromstring(xml_text.encode())
    entries = root.findall("atom:entry", ns)
    papers = []

    for entry in entries:
        entry_id = entry.findtext("atom:id", default="", namespaces=ns)
        arxiv_match = re.search(r"abs/(.+?)(?:v\d+)?$", entry_id)
        arxiv_id = arxiv_match.group(1) if arxiv_match else ""
        if not arxiv_id:
            continue

        title = (
            entry.findtext("atom:title", default="", namespaces=ns)
            .strip()
            .replace("\n", " ")
        )
        abstract = entry.findtext("atom:summary", default="", namespaces=ns).strip()

        authors = []
        for a in entry.findall("atom:author", ns):
            name = a.findtext("atom:name", default="", namespaces=ns)
            if name:
                authors.append(name)

        categories = [
            c.get("term", "")
            for c in entry.findall("atom:category", ns)
            if c.get("term")
        ]

        published = entry.findtext("atom:published", default="", namespaces=ns)
        doi = entry.findtext("arxiv:doi", default=None, namespaces=ns)

        papers.append(
            {
                "arxiv_id": arxiv_id,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "categories": categories,
                "published": published,
                "doi": doi,
                "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                "abs_url": f"https://arxiv.org/abs/{arxiv_id}",
                "html_url": f"https://ar5iv.labs.arxiv.org/html/{arxiv_id}",
            }
        )

    return papers


# ── Shared concurrency controls (module-level singletons) ────────────────
_MINERU_SEM: asyncio.Semaphore | None = None
_DB_WRITE_SEM: asyncio.Semaphore | None = None


def _mineru_sem() -> asyncio.Semaphore:
    global _MINERU_SEM
    if _MINERU_SEM is None:
        _MINERU_SEM = asyncio.Semaphore(settings.mineru_concurrency)
    return _MINERU_SEM


def _db_write_sem() -> asyncio.Semaphore:
    """Limit concurrent DB writes to stay within connection pool (max 30)."""
    global _DB_WRITE_SEM
    if _DB_WRITE_SEM is None:
        _DB_WRITE_SEM = asyncio.Semaphore(15)
    return _DB_WRITE_SEM


async def convert_via_mineru(
    arxiv_id: str,
    pdf_url: str,
    oss_client,
):
    """Convert an arXiv PDF via MinerU VLM model. Returns MinerUResult or None.

    We use the PDF URL (not ar5iv HTML) because ar5iv pages are JavaScript-rendered
    and MinerU's HTML fetcher only retrieves the static shell (~2 KB, abstract only).
    The VLM model processes the actual PDF and returns full-text markdown.
    """
    from app.clients.mineru_client import MinerUClient, MinerUModel

    try:
        client = MinerUClient()
    except ValueError as e:
        logger.warning("mineru_not_configured", error=str(e))
        return None

    try:
        async with _mineru_sem():
            result = await client.extract(
                url=pdf_url,
                model_version=MinerUModel.PDF_VLM,  # vlm model for PDF
                is_html=False,
                max_wait_seconds=900,  # 15 min total (3 min initial + polling)
                poll_interval=15.0,
                initial_wait_seconds=180.0,  # wait 3 min before first poll
                paper_slug=arxiv_id,
                oss_client=oss_client,
            )
        if result.success:
            return result
        logger.warning(
            "mineru_convert_failed",
            arxiv_id=arxiv_id,
            error=result.error,
        )
        return None
    except Exception as e:
        logger.warning(
            "mineru_convert_error",
            arxiv_id=arxiv_id,
            error=str(e)[:200],
        )
        return None
    finally:
        await client.close()


async def clear_existing_papers():
    """Delete all existing papers and authors from the database."""
    from app.dependencies import async_session_factory
    from sqlalchemy import text

    print("\n🗑️  Clearing existing data...")
    async with async_session_factory() as session:
        # Delete in dependency order to avoid FK violations
        for table in [
            "paper_authors",
            "paper_references",
            "paper_versions",
            "paper_topics",
            "paper_tags",
            "collection_papers",
            "ragflow_document_mappings",
            "reading_logs",
            "annotations",
            "claims",
            "knowledge_cards",
            "glossary_terms",
            "user_corrections",
            "user_reading_status",
            "metadata_provenance",
            "alerts",
            "reading_path_cache",
            "reproduction_attempts",
            "papers",
            "authors",
        ]:
            try:
                result = await session.execute(text(f"DELETE FROM {table}"))
                if result.rowcount:
                    print(f"   ✓ Deleted {result.rowcount} rows from {table}")
            except Exception as e:
                print(f"   ⚠ {table}: {e}")
        await session.commit()
    print("   ✅ Database cleared\n")


async def _insert_paper(session, paper_data: dict):
    """Insert one paper + authors. Returns Paper ORM object, or None if skipped."""
    from app.models.paper import Paper
    from app.models.author import Author, PaperAuthor
    from sqlalchemy import select

    arxiv_id = paper_data["arxiv_id"]
    doi = paper_data.get("doi")

    existing = await session.execute(
        select(Paper).where(
            Paper.deleted_at.is_(None),
            (
                (Paper.arxiv_id == arxiv_id) | (Paper.doi == doi)
                if doi
                else (Paper.arxiv_id == arxiv_id)
            ),
        )
    )
    if existing.scalar_one_or_none():
        return None

    try:
        async with session.begin_nested():
            pub_date = None
            if paper_data["published"]:
                try:
                    pub_date = datetime.fromisoformat(
                        paper_data["published"].replace("Z", "+00:00")
                    ).date()
                except ValueError:
                    pass

            paper = Paper(
                arxiv_id=arxiv_id,
                doi=doi,
                title=paper_data["title"],
                abstract=paper_data["abstract"],
                published_at=pub_date,
                paper_type="preprint",
                language="en",
                keywords=paper_data.get("categories"),
                source_type="remote",
                ingestion_status="discovered",
                remote_urls=[
                    {
                        "url": paper_data["abs_url"],
                        "source": "arxiv",
                        "type": "abstract",
                    },
                    {"url": paper_data["pdf_url"], "source": "arxiv", "type": "pdf"},
                    {"url": paper_data["html_url"], "source": "ar5iv", "type": "html"},
                ],
            )
            session.add(paper)
            await session.flush()

            for idx, author_name in enumerate(paper_data.get("authors", [])):
                auth_result = await session.execute(
                    select(Author).where(Author.display_name == author_name).limit(1)
                )
                author = auth_result.scalar_one_or_none()
                if not author:
                    author = Author(display_name=author_name)
                    session.add(author)
                    await session.flush()
                session.add(
                    PaperAuthor(paper_id=paper.id, author_id=author.id, position=idx)
                )

        await session.commit()
        return paper
    except Exception as e:
        print(f"  ✗ DB error [{arxiv_id}]: {e}")
        return None


async def _process_paper(
    paper,
    paper_data: dict,
    oss,
    analyst,
    counters: dict,
    lock: asyncio.Lock,
    stagger_index: int = 0,
):
    """MinerU + OSS + LLM analysis + DB update for one paper (runs concurrently).

    stagger_index: small sleep before submit to spread load (2s × index).
    Entire body is wrapped in try/except so one failure never cancels siblings.
    """
    from app.dependencies import async_session_factory
    from app.models.paper import Paper
    from sqlalchemy import select

    arxiv_id = paper_data["arxiv_id"]

    try:
        # Stagger submissions: 2 s × index → 72 tasks spread over ~2.4 min
        if stagger_index:
            await asyncio.sleep(stagger_index * 2)

        print(f"  ⏳ [{arxiv_id}] MinerU submit → waiting 3 min...")
        mineru_result = await convert_via_mineru(arxiv_id, paper_data["pdf_url"], oss)

        update_kw: dict = {}
        if mineru_result:
            markdown = mineru_result.markdown or ""
            update_kw = {
                "full_text_markdown": markdown,
                "has_full_text": True,
                "ingestion_status": "parsed",
                "parser_version": "mineru",
                "markdown_provenance": {
                    "source": "mineru",
                    "model_version": "vlm",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "markdown_length": len(markdown),
                    "input_url": paper_data["pdf_url"],
                    "images_uploaded": len(mineru_result.image_urls),
                },
            }
            async with lock:
                counters["converted"] += 1
            print(
                f"  ✓ [{arxiv_id}] Converted ({len(markdown):,} chars, "
                f"{len(mineru_result.image_urls)} images)"
            )

            # LLM analysis
            try:
                analysis = await analyst.analyse(paper)
                update_kw["deep_analysis"] = analysis
                update_kw["deep_analysis_at"] = datetime.now(timezone.utc)
                if analysis.get("status") == "ok":
                    async with lock:
                        counters["analysed"] += 1
                    print(
                        f"  ✓ [{arxiv_id}] Analysis done ({len(analysis.get('analysis', '')):,} chars)"
                    )
                else:
                    print(
                        f"  ⚠ [{arxiv_id}] Analysis: {analysis.get('error', '?')[:80]}"
                    )
            except Exception as e:
                print(f"  ⚠ [{arxiv_id}] Analysis failed: {e}")
        else:
            update_kw["ingestion_status"] = "enriched"
            print(f"  ⚠ [{arxiv_id}] MinerU failed, metadata only")

        # Persist — DB write semaphore prevents pool exhaustion
        if update_kw:
            async with _db_write_sem():
                async with async_session_factory() as upd:
                    res = await upd.execute(select(Paper).where(Paper.id == paper.id))
                    p_obj = res.scalar_one_or_none()
                    if p_obj:
                        for k, v in update_kw.items():
                            setattr(p_obj, k, v)
                        await upd.commit()

    except Exception as exc:
        print(f"  ✗ [{arxiv_id}] unhandled: {type(exc).__name__}: {exc}")


async def seed_papers():
    """Main seeding function — concurrent MinerU + LLM processing."""
    from app.dependencies import async_session_factory
    from app.services.analysis.paper_analyst import PaperAnalystService
    from app.clients.oss_client import OssClient

    print("=" * 60)
    print("  Kaleidoscope — ArXiv Paper Seeder (concurrent)")
    total_target = PAPERS_PER_CATEGORY * len(ARXIV_CATEGORIES)
    print(f"  Fetching {total_target} papers across {len(ARXIV_CATEGORIES)} categories")
    print("=" * 60)

    await clear_existing_papers()

    # ── Phase 1: Fetch metadata from arXiv ──────────────────────────
    all_papers: list[dict] = []
    seen_ids: set[str] = set()
    for cat in ARXIV_CATEGORIES:
        print(f"📡 Fetching {cat}...")
        try:
            await asyncio.sleep(3)  # arXiv rate limit
            papers = await fetch_arxiv_papers(cat, PAPERS_PER_CATEGORY)
            for p in papers:
                if p["arxiv_id"] not in seen_ids:
                    seen_ids.add(p["arxiv_id"])
                    all_papers.append(p)
            print(f"   ✓ {len(papers)} papers")
        except Exception as e:
            print(f"   ✗ {e}")

    print(f"\n📊 Total unique papers: {len(all_papers)}")

    # ── Phase 2: Insert all metadata into DB (serial — author dedup) ─
    print("\n💾 Inserting paper records...")
    papers_to_process: list[tuple] = []  # (paper_obj, paper_data)
    skipped = 0

    async with async_session_factory() as session:
        for paper_data in all_papers:
            paper = await _insert_paper(session, paper_data)
            if paper:
                papers_to_process.append((paper, paper_data))
            else:
                skipped += 1

    print(f"   ✓ Inserted {len(papers_to_process)}, skipped {skipped}")

    if not papers_to_process:
        print("Nothing to process.")
        return

    # ── Phase 3: Concurrent MinerU + LLM ────────────────────────────
    print(
        f"\n🚀 Processing {len(papers_to_process)} papers concurrently "
        f"(MinerU concurrency={settings.mineru_concurrency})...\n"
    )

    oss = OssClient()
    analyst = PaperAnalystService()
    counters = {"converted": 0, "analysed": 0}
    lock = asyncio.Lock()

    await asyncio.gather(
        *[
            _process_paper(
                paper, paper_data, oss, analyst, counters, lock, stagger_index=i
            )
            for i, (paper, paper_data) in enumerate(papers_to_process)
        ],
        return_exceptions=True,
    )

    await analyst.close()

    print("\n" + "=" * 60)
    print("  ✅ Done!")
    print(f"  Inserted:  {len(papers_to_process)}")
    print(f"  Converted: {counters['converted']}")
    print(f"  Analysed:  {counters['analysed']}")
    print(f"  Skipped:   {skipped} (already in DB)")
    print("=" * 60)

    # ── Phase 4: Auto-enrich authors from Semantic Scholar ──────────
    await _enrich_all_authors()


async def _enrich_all_authors(batch_size: int = 5) -> None:
    """
    Enrich all authors in the library that have not yet been enriched.

    Processes authors in small concurrent batches to respect S2 rate limits
    (100 req / 5 min on the free tier — each author uses 1–3 requests).
    """
    from sqlalchemy import select
    from app.models.author import Author
    from app.dependencies import async_session_factory
    from app.services.enrichment.author_enrichment import AuthorEnrichmentService

    print("\n🔬 Phase 4 — Enriching authors from Semantic Scholar...")

    async with async_session_factory() as session:
        result = await session.execute(
            select(Author.id, Author.display_name)
            .where(
                Author.deleted_at.is_(None),
                Author.semantic_scholar_id.is_(None),
            )
            .order_by(Author.display_name)
        )
        rows = result.all()

    print(f"   Found {len(rows)} un-enriched authors")
    if not rows:
        return

    counters = {"ok": 0, "no_match": 0, "error": 0}

    async def _enrich_one(author_id: str, name: str) -> None:
        try:
            async with async_session_factory() as db:
                svc = AuthorEnrichmentService(db)
                result = await svc.enrich(author_id)
                await svc.close()
            status = result.get("status", "error")
            if status == "ok":
                counters["ok"] += 1
                print(
                    f"   ✓ {name} → S2:{result.get('s2_id')} ({result.get('match_reason')})"
                )
            elif status == "no_match":
                counters["no_match"] += 1
            else:
                counters["error"] += 1
        except Exception as e:
            counters["error"] += 1
            logger.warning("author_enrich_failed", name=name, error=str(e)[:120])

    # Process in small batches with a short sleep between batches to stay
    # well under S2's 100 req / 5 min free-tier limit.
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        await asyncio.gather(
            *[_enrich_one(str(r.id), r.display_name) for r in batch],
            return_exceptions=True,
        )
        if i + batch_size < len(rows):
            await asyncio.sleep(4)  # ~4 s between batches ≈ 75 req/min

    print(
        f"\n   Enriched: {counters['ok']}  No match: {counters['no_match']}  Errors: {counters['error']}"
    )


if __name__ == "__main__":
    asyncio.run(seed_papers())
