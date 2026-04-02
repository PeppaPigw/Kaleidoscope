"""Reparsing script — re-process papers whose full_text_markdown is too short
(abstract-only from ar5iv HTML) using the PDF + VLM model via MinerU.

Usage:
    cd backend && python -m app.scripts.reparse_papers

This script finds papers where:
  - has_full_text = true but markdown is suspiciously short (<5000 chars)
    OR parser_version != 'mineru-pdf'
  - Resubmits to MinerU using the arXiv PDF URL + VLM model
  - Updates full_text_markdown and marks parser_version='mineru-pdf'
"""

import asyncio
from datetime import datetime, timezone

import structlog

from app.config import settings
from app.dependencies import async_session_factory

structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(20))
logger = structlog.get_logger(__name__)

ABSTRACT_THRESHOLD = 5000  # chars — below this is suspect


async def reparse_papers(dry_run: bool = False, limit: int = 100) -> None:
    from sqlalchemy import select
    from app.models.paper import Paper
    from app.clients.mineru_client import MinerUClient, MinerUModel
    from app.clients.oss_client import OssClient

    print("=" * 60)
    print("  Kaleidoscope — Paper Reparser (PDF mode)")
    print("=" * 60)

    # ── Find papers needing reparse ───────────────────────────
    async with async_session_factory() as session:
        result = await session.execute(
            select(Paper).where(
                Paper.deleted_at.is_(None),
                Paper.arxiv_id.is_not(None),
                # Either no full text, or suspiciously short, or wrong parser
                (
                    (Paper.has_full_text == False)  # noqa: E712
                    | (Paper.parser_version != "mineru-pdf")
                ),
            ).limit(limit)
        )
        papers = result.scalars().all()

    print(f"\n📋 Found {len(papers)} papers to reprocess\n")
    if dry_run:
        for p in papers:
            print(f"  [{p.arxiv_id}] status={p.ingestion_status} "
                  f"md_len={len(p.full_text_markdown or '')} "
                  f"parser={p.parser_version}")
        return

    try:
        mineru = MinerUClient()
    except ValueError as e:
        print(f"✗ MinerU not configured: {e}")
        return

    oss = OssClient()
    done = 0
    failed = 0

    for i, paper in enumerate(papers):
        pdf_url = f"https://arxiv.org/pdf/{paper.arxiv_id}.pdf"
        print(f"\n[{i+1}/{len(papers)}] 📄 {paper.title[:70] if paper.title else paper.arxiv_id}...")
        print(f"     PDF: {pdf_url}")
        print(f"     ⏳ Submitting to MinerU VLM...")

        try:
            result = await mineru.extract(
                url=pdf_url,
                model_version=MinerUModel.PDF_VLM,
                is_html=False,
                max_wait_seconds=480,
                poll_interval=10.0,
                paper_slug=paper.arxiv_id,
                oss_client=oss,
            )
        except Exception as e:
            err_msg = str(e) or repr(e)
            print(f"     ✗ Exception: {type(e).__name__}: {err_msg}")
            failed += 1
            continue

        if not result.success:
            print(f"     ✗ MinerU failed: {result.error}")
            failed += 1
            continue

        markdown = result.markdown or ""
        print(f"     ✓ Got {len(markdown):,} chars, "
              f"{len(result.image_urls)} images")

        # Update in a fresh short session
        async with async_session_factory() as upd:
            res = await upd.execute(select(Paper).where(Paper.id == paper.id))
            p_obj = res.scalar_one_or_none()
            if p_obj:
                p_obj.full_text_markdown = markdown
                p_obj.has_full_text = True
                p_obj.ingestion_status = "parsed"
                p_obj.parser_version = "mineru-pdf"
                p_obj.markdown_provenance = {
                    "source": "mineru",
                    "model_version": "vlm",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "markdown_length": len(markdown),
                    "input_url": pdf_url,
                    "images_uploaded": len(result.image_urls),
                }
                if result.layout:
                    p_obj.parsed_figures = result.layout
                await upd.commit()
                done += 1
                print(f"     💾 Saved to DB")

    print("\n" + "=" * 60)
    print(f"  ✅ Done!")
    print(f"  Reparsed: {done}")
    print(f"  Failed:   {failed}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(reparse_papers())
