"""Reparsing script — concurrent MinerU backfill for legacy arXiv papers.

Usage:
    cd backend && python -m app.scripts.reparse_papers --dry-run --limit 50

Targets arXiv papers that are not yet MinerU-ready.
Processing is prioritized by oldest local records first so the legacy backlog
is drained before newer arrivals.

Selection criteria:
  - parser_version is missing or from a legacy parser
  - or ingestion_status has not reached parsed/indexed/index_partial

Submits all to MinerU concurrently, waits, then persists markdown back into DB.
Concurrency capped by settings.mineru_concurrency.
"""

import argparse
import asyncio
from datetime import UTC, datetime

import structlog

from app.config import settings
from app.dependencies import async_session_factory

structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(20))
logger = structlog.get_logger(__name__)

_SEM: asyncio.Semaphore | None = None
_DB_SEM: asyncio.Semaphore | None = None


def _sem() -> asyncio.Semaphore:
    global _SEM
    if _SEM is None:
        _SEM = asyncio.Semaphore(settings.mineru_concurrency)
    return _SEM


def _db_sem() -> asyncio.Semaphore:
    global _DB_SEM
    if _DB_SEM is None:
        _DB_SEM = asyncio.Semaphore(15)
    return _DB_SEM


async def _reparse_one(
    paper_id,
    arxiv_id: str,
    title: str,
    oss,
    counters: dict,
    lock: asyncio.Lock,
    stagger_index: int = 0,
) -> None:
    from sqlalchemy import select

    from app.clients.mineru_client import MinerUClient, MinerUModel
    from app.models.paper import Paper
    from app.services.parsing.mineru_service import sanitize_mineru_markdown

    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

    try:
        client = MinerUClient()
    except ValueError as e:
        print(f"  ✗ [{arxiv_id}] MinerU not configured: {e}")
        return

    try:
        if stagger_index:
            await asyncio.sleep(stagger_index * 2)

        async with _sem():
            print(f"  ⏳ [{arxiv_id}] Submitting → waiting 3 min...")
            result = await client.extract(
                url=pdf_url,
                model_version=MinerUModel.PDF_VLM,
                is_html=False,
                max_wait_seconds=900,
                poll_interval=15.0,
                initial_wait_seconds=180.0,
                paper_slug=arxiv_id,
                oss_client=oss,
            )
    except Exception as e:
        print(f"  ✗ [{arxiv_id}] Exception: {e}")
        return
    finally:
        await client.close()

    if not result.success:
        print(f"  ✗ [{arxiv_id}] MinerU failed: {result.error}")
        async with lock:
            counters["failed"] += 1
        return

    markdown = sanitize_mineru_markdown(result.markdown)
    print(f"  ✓ [{arxiv_id}] {len(markdown):,} chars, {len(result.image_urls)} images")

    try:
        async with _db_sem(), async_session_factory() as upd:
            res = await upd.execute(select(Paper).where(Paper.id == paper_id))
            p_obj = res.scalar_one_or_none()
            if p_obj:
                p_obj.full_text_markdown = markdown
                p_obj.has_full_text = True
                p_obj.ingestion_status = "parsed"
                p_obj.parser_version = "mineru"
                p_obj.markdown_provenance = {
                    "source": "mineru",
                    "model_version": "vlm",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "markdown_length": len(markdown),
                    "input_url": pdf_url,
                    "images_uploaded": len(result.image_urls),
                }
                await upd.commit()
                async with lock:
                    counters["done"] += 1
                print(f"  💾 [{arxiv_id}] Saved")
    except Exception as e:
        print(f"  ✗ [{arxiv_id}] DB update failed: {e}")
        async with lock:
            counters["failed"] += 1


async def reparse_papers(dry_run: bool = False, limit: int = 200) -> None:
    from sqlalchemy import and_, not_, or_, select

    from app.clients.oss_client import OssClient
    from app.models.paper import Paper

    mineru_ready = and_(
        or_(
            Paper.parser_version == "mineru",
            Paper.parser_version.like("mineru-%"),
        ),
        Paper.ingestion_status.in_(("parsed", "indexed", "index_partial")),
    )

    print("=" * 60)
    print("  Kaleidoscope — Paper Reparser (concurrent, PDF+VLM)")
    print("=" * 60)

    async with async_session_factory() as session:
        result = await session.execute(
            select(Paper.id, Paper.arxiv_id, Paper.title)
            .where(
                Paper.deleted_at.is_(None),
                Paper.arxiv_id.is_not(None),
                not_(mineru_ready),
            )
            .order_by(Paper.created_at.asc())
            .limit(limit)
        )
        rows = result.all()

    print(f"\n📋 Found {len(rows)} papers to reprocess")
    if dry_run:
        for row in rows:
            print(f"  [{row.arxiv_id}] {(row.title or '')[:60]}")
        return

    if not rows:
        print("Nothing to do.")
        return

    print(
        f"🚀 Processing {len(rows)} papers concurrently "
        f"(concurrency={settings.mineru_concurrency})...\n"
    )

    oss = OssClient()
    counters = {"done": 0, "failed": 0}
    lock = asyncio.Lock()

    await asyncio.gather(
        *[
            _reparse_one(
                row.id,
                row.arxiv_id,
                row.title or "",
                oss,
                counters,
                lock,
                stagger_index=i,
            )
            for i, row in enumerate(rows)
        ],
        return_exceptions=True,
    )

    print("\n" + "=" * 60)
    print("  ✅ Done!")
    print(f"  Reparsed: {counters['done']}")
    print(f"  Failed:   {counters['failed']}")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=200)
    args = parser.parse_args()
    asyncio.run(reparse_papers(dry_run=args.dry_run, limit=args.limit))
