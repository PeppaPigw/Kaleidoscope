"""
Backfill deep_analysis for all papers missing it.
Usage: python -m app.scripts.analyse_all_papers [--force] [--concurrency N]
"""

import argparse
import asyncio
import time

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.dependencies import async_session_factory
from app.models.author import PaperAuthor
from app.models.paper import Paper
from app.services.analysis.paper_analyst import PaperAnalystService


async def main(force: bool = False, concurrency: int = 5) -> None:
    start = time.monotonic()

    from sqlalchemy import or_

    async with async_session_factory() as session:
        q = select(Paper.id, Paper.title).where(Paper.deleted_at.is_(None))
        if not force:
            # Include papers with no analysis OR previously failed analysis
            q = q.where(
                or_(
                    Paper.deep_analysis.is_(None),
                    Paper.deep_analysis["status"].astext == "error",
                )
            )
        q = q.order_by(Paper.created_at.desc())
        rows = (await session.execute(q)).all()

    total = len(rows)
    if total == 0:
        print("All papers successfully analysed. Use --force to re-run all.")
        return

    print(f"Papers to analyse: {total}  (concurrency={concurrency})")
    print("-" * 60)

    done = skipped = errors = 0
    sem = asyncio.Semaphore(concurrency)

    async def _one(paper_id, title: str) -> None:
        nonlocal done, skipped, errors
        async with sem:
            try:
                async with async_session_factory() as db:
                    r = await db.execute(
                        select(Paper)
                        .where(Paper.id == paper_id)
                        .options(
                            selectinload(Paper.authors).selectinload(PaperAuthor.author)
                        )
                    )
                    paper = r.scalar_one_or_none()
                    if paper is None:
                        skipped += 1
                        return
                    already_ok = (
                        paper.deep_analysis is not None
                        and paper.deep_analysis.get("status") == "ok"
                    )
                    if already_ok and not force:
                        skipped += 1
                        return
                    svc = PaperAnalystService(db)
                    result = await svc.analyse_and_persist(paper, db)
                    await db.commit()
                    await svc.close()

                status = result.get("status", "?")
                out_chars = len(result.get("analysis", ""))
                if status == "ok":
                    done += 1
                    print(
                        f"  ✓ [{done+errors}/{total}] {title[:70]}  ({out_chars} chars)"
                    )
                else:
                    errors += 1
                    print(
                        f"  ✗ [{done+errors}/{total}] {title[:70]}  ERR: {result.get('error','?')[:80]}"
                    )
            except Exception as e:
                errors += 1
                print(f"  ✗ EXCEPTION {str(paper_id)[:8]}… {str(e)[:100]}")

    await asyncio.gather(*[_one(r.id, r.title) for r in rows], return_exceptions=True)

    elapsed = time.monotonic() - start
    print("-" * 60)
    print(f"Done in {elapsed:.0f}s  ✓ {done}  ✗ {errors}  skipped {skipped}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--force", action="store_true", help="Re-analyse already-analysed papers"
    )
    parser.add_argument("--concurrency", type=int, default=5)
    args = parser.parse_args()
    asyncio.run(main(force=args.force, concurrency=args.concurrency))
