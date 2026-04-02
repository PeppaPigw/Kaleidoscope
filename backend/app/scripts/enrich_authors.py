"""Standalone author enrichment script — enrich all authors without S2 data.

Usage:
    cd backend && python -m app.scripts.enrich_authors

Options (edit constants below):
    BATCH_SIZE   — concurrent S2 requests per batch (default 5)
    SLEEP_SECS   — pause between batches (default 4 s; stay under 100 req/5 min)
    FORCE        — re-enrich even authors that already have semantic_scholar_id
"""

import asyncio

import structlog

structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(20))
logger = structlog.get_logger(__name__)

BATCH_SIZE = 5
SLEEP_SECS = 4
FORCE = False


async def enrich_authors() -> None:
    from sqlalchemy import select
    from app.models.author import Author
    from app.dependencies import async_session_factory
    from app.services.enrichment.author_enrichment import AuthorEnrichmentService

    print("=" * 60)
    print("  Kaleidoscope — Author Enricher (Semantic Scholar)")
    print("=" * 60)

    async with async_session_factory() as session:
        q = select(Author.id, Author.display_name).where(Author.deleted_at.is_(None))
        if not FORCE:
            q = q.where(Author.semantic_scholar_id.is_(None))
        result = await session.execute(q.order_by(Author.display_name))
        rows = result.all()

    print(f"\n📋 Authors to enrich: {len(rows)}")
    if not rows:
        print("Nothing to do.")
        return

    counters = {"ok": 0, "no_match": 0, "error": 0, "not_found": 0}

    async def _one(author_id: str, name: str) -> None:
        try:
            async with async_session_factory() as db:
                svc = AuthorEnrichmentService(db)
                res = await svc.enrich(author_id)
                await svc.close()
            status = res.get("status", "error")
            counters[status if status in counters else "error"] += 1
            if status == "ok":
                print(
                    f"  ✓ {name[:50]:<50} → S2:{res.get('s2_id')}  [{res.get('match_reason')}]"
                )
            elif status == "no_match":
                print(
                    f"  ~ {name[:50]:<50}   no match  (top: {res.get('top_candidate', '—')})"
                )
            elif status == "not_found":
                print(f"  ? {name[:50]:<50}   not in DB")
            else:
                print(f"  ✗ {name[:50]:<50}   error: {res.get('error', '?')[:60]}")
        except Exception as e:
            counters["error"] += 1
            print(f"  ✗ {name[:50]:<50}   exception: {e}")

    print()
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        await asyncio.gather(
            *[_one(str(r.id), r.display_name) for r in batch], return_exceptions=True
        )
        if i + BATCH_SIZE < len(rows):
            await asyncio.sleep(SLEEP_SECS)

    print("\n" + "=" * 60)
    print("  ✅ Done!")
    print(f"  Enriched:  {counters['ok']}")
    print(f"  No match:  {counters['no_match']}")
    print(f"  Errors:    {counters['error']}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(enrich_authors())
