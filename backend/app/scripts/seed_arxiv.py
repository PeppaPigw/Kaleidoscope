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
    "cs.AI",   # Artificial Intelligence
    "cs.LG",   # Machine Learning
    "cs.CL",   # Computation and Language (NLP)
    "cs.CV",   # Computer Vision
    "cs.IR",   # Information Retrieval
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
        abstract = (
            entry.findtext("atom:summary", default="", namespaces=ns)
            .strip()
        )

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

        published = entry.findtext(
            "atom:published", default="", namespaces=ns
        )
        doi = entry.findtext("arxiv:doi", default=None, namespaces=ns)

        papers.append({
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
        })

    return papers


# ── Shared concurrency controls (module-level singletons) ────────────────
_MINERU_SEM: asyncio.Semaphore | None = None


def _mineru_sem() -> asyncio.Semaphore:
    global _MINERU_SEM
    if _MINERU_SEM is None:
        _MINERU_SEM = asyncio.Semaphore(settings.mineru_concurrency)
    return _MINERU_SEM


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
            "paper_authors", "paper_references", "paper_versions",
            "paper_topics", "paper_tags", "collection_papers",
            "ragflow_document_mappings", "reading_logs", "annotations",
            "claims", "knowledge_cards", "glossary_terms",
            "user_corrections", "user_reading_status", "metadata_provenance",
            "alerts", "reading_path_cache", "reproduction_attempts",
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
            (Paper.arxiv_id == arxiv_id)
            | (Paper.doi == doi) if doi else (Paper.arxiv_id == arxiv_id),
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
                    {"url": paper_data["abs_url"], "source": "arxiv", "type": "abstract"},
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
                session.add(PaperAuthor(paper_id=paper.id, author_id=author.id, position=idx))

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
):
    """MinerU + OSS + LLM analysis + DB update for one paper (runs concurrently)."""
    from app.dependencies import async_session_factory
    from app.models.paper import Paper
    from sqlalchemy import select

    arxiv_id = paper_data["arxiv_id"]
    title_short = paper_data["title"][:60]

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
        if mineru_result.layout:
            update_kw["parsed_figures"] = mineru_result.layout

        async with lock:
            counters["converted"] += 1
        print(f"  ✓ [{arxiv_id}] Converted ({len(markdown):,} chars, "
              f"{len(mineru_result.image_urls)} images)")

        # LLM analysis — uses converted markdown
        try:
            analysis = await analyst.analyse(paper)
            update_kw["deep_analysis"] = analysis
            update_kw["deep_analysis_at"] = datetime.now(timezone.utc)
            if analysis.get("status") == "ok":
                async with lock:
                    counters["analysed"] += 1
                print(f"  ✓ [{arxiv_id}] Analysis done ({len(analysis.get('analysis', '')):,} chars)")
            else:
                print(f"  ⚠ [{arxiv_id}] Analysis: {analysis.get('error', '?')[:80]}")
        except Exception as e:
            print(f"  ⚠ [{arxiv_id}] Analysis failed: {e}")
    else:
        update_kw["ingestion_status"] = "enriched"
        print(f"  ⚠ [{arxiv_id}] MinerU failed, metadata only")

    # Persist in its own short-lived session
    if update_kw:
        async with async_session_factory() as upd:
            res = await upd.execute(select(Paper).where(Paper.id == paper.id))
            p_obj = res.scalar_one_or_none()
            if p_obj:
                for k, v in update_kw.items():
                    setattr(p_obj, k, v)
                await upd.commit()


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
            await asyncio.sleep(3)   # arXiv rate limit
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
    papers_to_process: list[tuple] = []   # (paper_obj, paper_data)
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
    print(f"\n🚀 Processing {len(papers_to_process)} papers concurrently "
          f"(MinerU concurrency={settings.mineru_concurrency})...\n")

    oss = OssClient()
    analyst = PaperAnalystService()
    counters = {"converted": 0, "analysed": 0}
    lock = asyncio.Lock()

    await asyncio.gather(*[
        _process_paper(paper, paper_data, oss, analyst, counters, lock)
        for paper, paper_data in papers_to_process
    ])

    await analyst.close()

    print("\n" + "=" * 60)
    print("  ✅ Done!")
    print(f"  Inserted:  {len(papers_to_process)}")
    print(f"  Converted: {counters['converted']}")
    print(f"  Analysed:  {counters['analysed']}")
    print(f"  Skipped:   {skipped} (already in DB)")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed_papers())
