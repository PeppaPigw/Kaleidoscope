"""Seed script — fetch 50 arXiv papers, convert to Markdown via MinerU, store in DB.

Usage:
    cd backend && python -m app.scripts.seed_arxiv

Strategy:
    1. Query arXiv API for recent papers across ML/AI categories
    2. For each paper, create a Paper row with metadata
    3. Use MinerU HTML model on ar5iv URLs to get markdown (no PDF storage)
    4. Store `full_text_markdown` directly in the paper row
    5. Store original arXiv links in `remote_urls` for user navigation
"""

import asyncio
from datetime import datetime, timezone

import structlog

logger = structlog.get_logger(__name__)

# arXiv categories to sample from
ARXIV_CATEGORIES = [
    "cs.AI",   # Artificial Intelligence
    "cs.LG",   # Machine Learning
    "cs.CL",   # Computation and Language (NLP)
    "cs.CV",   # Computer Vision
    "cs.IR",   # Information Retrieval
]

# 10 papers per category = 50 total
PAPERS_PER_CATEGORY = 10


async def fetch_arxiv_papers(category: str, max_results: int) -> list[dict]:
    """Fetch recent papers from arXiv API for a given category."""
    import httpx

    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"cat:{category}",
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": max_results,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
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


async def convert_via_mineru(arxiv_id: str, html_url: str) -> str | None:
    """Convert an ar5iv HTML page to Markdown via MinerU API."""
    from app.clients.mineru_client import MinerUClient

    try:
        client = MinerUClient()
    except ValueError as e:
        logger.warning("mineru_not_configured", error=str(e))
        return None

    try:
        result = await client.extract(
            url=html_url,
            is_html=True,
            max_wait_seconds=300,
            poll_interval=5.0,
        )
        if result.success:
            return result.markdown
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


async def seed_papers():
    """Main seeding function."""
    from app.dependencies import async_session_factory
    from app.models.paper import Paper
    from app.models.author import Author, PaperAuthor
    from sqlalchemy import select

    print("=" * 60)
    print("  Kaleidoscope — ArXiv Paper Seeder")
    print("  Fetching 50 papers across 5 categories")
    print("=" * 60)

    all_papers: list[dict] = []
    seen_ids: set[str] = set()

    # Step 1: Fetch from arXiv across categories
    for cat in ARXIV_CATEGORIES:
        print(f"\n📡 Fetching from arXiv: {cat}...")
        try:
            # arXiv rate limit: 1 req per 3 sec
            await asyncio.sleep(3)
            papers = await fetch_arxiv_papers(cat, PAPERS_PER_CATEGORY)
            for p in papers:
                if p["arxiv_id"] not in seen_ids:
                    seen_ids.add(p["arxiv_id"])
                    all_papers.append(p)
            print(f"   ✓ Got {len(papers)} papers")
        except Exception as e:
            print(f"   ✗ Error: {e}")

    print(f"\n📊 Total unique papers: {len(all_papers)}")

    # Step 2: Store in DB and convert via MinerU
    async with async_session_factory() as session:
        created = 0
        converted = 0
        skipped = 0

        for i, paper_data in enumerate(all_papers):
            arxiv_id = paper_data["arxiv_id"]
            doi = paper_data.get("doi")

            # Check for existing by arxiv_id OR doi
            existing = await session.execute(
                select(Paper).where(
                    Paper.deleted_at.is_(None),
                    (Paper.arxiv_id == arxiv_id)
                    | (Paper.doi == doi) if doi else (Paper.arxiv_id == arxiv_id),
                )
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue

            # Use savepoint so a single failure doesn't poison the session
            try:
                async with session.begin_nested():
                    # Parse published date
                    pub_date = None
                    if paper_data["published"]:
                        try:
                            pub_date = datetime.fromisoformat(
                                paper_data["published"].replace("Z", "+00:00")
                            ).date()
                        except ValueError:
                            pass

                    # Create paper record
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
                            {
                                "url": paper_data["pdf_url"],
                                "source": "arxiv",
                                "type": "pdf",
                            },
                            {
                                "url": paper_data["html_url"],
                                "source": "ar5iv",
                                "type": "html",
                            },
                        ],
                    )
                    session.add(paper)
                    await session.flush()
                    created += 1

                    # Create author records
                    for idx, author_name in enumerate(paper_data.get("authors", [])):
                        auth_result = await session.execute(
                            select(Author).where(
                                Author.display_name == author_name
                            ).limit(1)
                        )
                        author = auth_result.scalar_one_or_none()
                        if not author:
                            author = Author(display_name=author_name)
                            session.add(author)
                            await session.flush()

                        pa = PaperAuthor(
                            paper_id=paper.id,
                            author_id=author.id,
                            position=idx,
                        )
                        session.add(pa)

            except Exception as e:
                print(f"     ✗ DB error for {arxiv_id}: {e}")
                skipped += 1
                continue

            prog = f"[{i + 1}/{len(all_papers)}]"
            print(f"\n{prog} 📄 {paper_data['title'][:70]}...")

            # Convert via MinerU (with rate limiting)
            print(f"     ⏳ Converting via MinerU...")
            markdown = await convert_via_mineru(
                arxiv_id, paper_data["html_url"]
            )

            if markdown:
                paper.full_text_markdown = markdown
                paper.has_full_text = True
                paper.ingestion_status = "parsed"
                paper.parser_version = "mineru"
                paper.markdown_provenance = {
                    "source": "mineru",
                    "model_version": "MinerU-HTML",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "markdown_length": len(markdown),
                    "input_url": paper_data["html_url"],
                }
                converted += 1
                print(f"     ✓ Converted ({len(markdown):,} chars)")
            else:
                paper.ingestion_status = "enriched"
                print(f"     ⚠ Conversion failed, metadata only")

            # Commit every 5 papers
            if (i + 1) % 5 == 0:
                await session.commit()
                print(f"     💾 Committed batch")

        # Final commit
        await session.commit()

    print("\n" + "=" * 60)
    print(f"  ✅ Done!")
    print(f"  Created:   {created}")
    print(f"  Converted: {converted}")
    print(f"  Skipped:   {skipped} (already in DB)")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed_papers())
