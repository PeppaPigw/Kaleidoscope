"""Celery tasks for paper chunk embedding.

Pipeline:
  load paper markdown → parse sections → delete old chunks → insert new chunks
  → batch embed via LLMClient → store vectors → mark job completed.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

import structlog

from app.worker import celery_app

logger = structlog.get_logger(__name__)

EMBED_BATCH_SIZE = 16  # GLM-Embedding-2 max batch size on BLSC (400 above 16)


def _run_async(coro):
    """Run async code from sync Celery task context — same pattern as ingest_tasks.py."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


async def embed_paper_async(paper_id: str, priority: int = 0) -> dict:
    """
    Core async embedding pipeline — can be called from uvicorn background tasks
    or wrapped by the Celery task below.

    Pipeline:
    1. Claim job (create or mark running) — skips if already completed/running
    2. Load paper text
    3. Parse sections (H1-corrected markdown chunker)
    4. Delete old chunks (idempotency)
    5. Insert new PaperChunk rows
    6. Batch embed via LLMClient
    7. Store vectors
    8. Mark job completed
    """
    from sqlalchemy import select, delete

    from app.dependencies import async_session_factory
    from app.clients.llm_client import LLMClient
    from app.models.paper_qa import PaperChunk, PaperEmbeddingJob
    from app.models.paper import Paper
    from app.services.extraction.markdown_section_parser import parse_markdown_sections

    paper_uuid = uuid.UUID(paper_id)

    async with async_session_factory() as session:
        # ── 1. Claim or create job ────────────────────────────────
        result = await session.execute(
            select(PaperEmbeddingJob).where(PaperEmbeddingJob.paper_id == paper_uuid)
        )
        job = result.scalar_one_or_none()

        if job and job.status in ("running", "completed"):
            return {"status": job.status, "skipped": True}

        if not job:
            job = PaperEmbeddingJob(
                paper_id=paper_uuid, status="running", priority=priority
            )
            session.add(job)
        else:
            job.status = "running"
            job.started_at = datetime.now(timezone.utc)
            job.error_message = None

        await session.flush()

        # ── 2. Load paper ─────────────────────────────────────────
        paper = (
            await session.execute(select(Paper).where(Paper.id == paper_uuid))
        ).scalar_one_or_none()
        if not paper:
            job.status = "failed"
            job.error_message = "Paper not found"
            await session.commit()
            return {"status": "failed", "error": "Paper not found"}

        markdown = _get_best_markdown(paper)
        if not markdown:
            job.status = "failed"
            job.error_message = "No text content available for embedding"
            await session.commit()
            return {"status": "failed", "error": "No text content"}

        # ── 3. Parse sections ─────────────────────────────────────
        sections = parse_markdown_sections(markdown)
        indexable = [s for s in sections if not s.is_references]
        if not indexable:
            job.status = "failed"
            job.error_message = "No indexable sections found"
            await session.commit()
            return {"status": "failed", "error": "No indexable sections"}

        # ── 4. Delete old chunks ──────────────────────────────────
        await session.execute(
            delete(PaperChunk).where(PaperChunk.paper_id == paper_uuid)
        )
        await session.flush()

        # ── 5. Insert chunks (no vectors yet) ────────────────────
        chunk_objs: list[PaperChunk] = []
        for section in indexable:
            chunk = PaperChunk(
                paper_id=paper_uuid,
                section_title=section.title,
                normalized_section_title=section.normalized_title,
                section_level=section.level,
                content=section.content,
                order_index=section.order_index,
                is_appendix=section.is_appendix,
                is_references=section.is_references,
                token_estimate=section.token_estimate,
            )
            session.add(chunk)
            chunk_objs.append(chunk)
        await session.flush()

        # ── 6. Batch embed ────────────────────────────────────────
        llm = LLMClient()
        texts = [c.content for c in chunk_objs]
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), EMBED_BATCH_SIZE):
            embeddings = await llm.embed(texts[i : i + EMBED_BATCH_SIZE])
            all_embeddings.extend(embeddings)
        await llm.close()

        # ── 7. Store vectors ──────────────────────────────────────
        for chunk, embedding in zip(chunk_objs, all_embeddings):
            chunk.embedding = embedding

        # ── 8. Complete ───────────────────────────────────────────
        job.status = "completed"
        job.chunk_count = len(chunk_objs)
        job.finished_at = datetime.now(timezone.utc)
        await session.commit()

        logger.info(
            "paper_embedding_completed", paper_id=paper_id, chunks=len(chunk_objs)
        )
        return {"status": "completed", "chunks": len(chunk_objs)}


@celery_app.task(
    bind=True,
    name="embedding.process_paper",
    max_retries=3,
    default_retry_delay=60,
)
def process_paper_embedding(self, paper_id: str, priority: int = 0):
    """Celery wrapper around embed_paper_async — for optional separate worker use."""
    try:
        return _run_async(embed_paper_async(paper_id, priority=priority))
    except Exception as exc:
        logger.error("paper_embedding_failed", paper_id=paper_id, error=str(exc))

        async def _mark_failed():
            from sqlalchemy import select
            from app.dependencies import async_session_factory
            from app.models.paper_qa import PaperEmbeddingJob

            paper_uuid = uuid.UUID(paper_id)
            async with async_session_factory() as session:
                result = await session.execute(
                    select(PaperEmbeddingJob).where(
                        PaperEmbeddingJob.paper_id == paper_uuid
                    )
                )
                job = result.scalar_one_or_none()
                if job:
                    job.status = "failed"
                    job.error_message = str(exc)[:500]
                    await session.commit()

        _run_async(_mark_failed())
        try:
            raise self.retry(exc=exc)
        except Exception:
            pass
        return {"status": "failed", "error": str(exc)}


def _get_best_markdown(paper) -> str | None:
    """Return the best available full text for embedding."""
    if getattr(paper, "full_text_markdown", None):
        return paper.full_text_markdown

    # Fallback: try sections → reconstruct as markdown
    sections = getattr(paper, "sections", None)
    if sections:
        parts: list[str] = []
        for s in sections:
            heading = s.get("heading") or s.get("title") or ""
            text = s.get("text") or s.get("content") or ""
            if heading:
                parts.append(f"# {heading}\n\n{text}")
            elif text:
                parts.append(text)
        if parts:
            return "\n\n".join(parts)

    # Last resort: abstract only
    abstract = getattr(paper, "abstract", None)
    if abstract:
        return f"# Abstract\n\n{abstract}"

    return None


# ── Periodic sweep ───────────────────────────────────────────────────────────


@celery_app.task(bind=True, name="embedding.sweep_unembedded_papers")
def sweep_unembedded_papers(self):
    """
    Periodic task: scan all papers and queue embedding for any that are missing
    a completed PaperEmbeddingJob.

    Criteria for queuing:
    - Paper has full_text_markdown (or abstract as fallback)
    - No PaperEmbeddingJob exists, OR job.status == 'failed'

    Papers with pending/running/completed jobs are skipped.
    Queued at low priority (0) to avoid blocking user-triggered (priority 10) jobs.
    """

    async def _sweep():
        from sqlalchemy import select, not_, exists

        from app.dependencies import async_session_factory
        from app.models.paper import Paper
        from app.models.paper_qa import PaperEmbeddingJob
        from app.config import settings

        batch_size = settings.paper_qa_sweep_batch_size

        async with async_session_factory() as session:
            # Papers that have no embedding job at all
            no_job_stmt = (
                select(Paper.id)
                .where(
                    not_(
                        exists(
                            select(PaperEmbeddingJob.id).where(
                                PaperEmbeddingJob.paper_id == Paper.id
                            )
                        )
                    )
                )
                .limit(batch_size)
            )

            # Papers whose last job failed
            failed_job_stmt = (
                select(Paper.id)
                .join(
                    PaperEmbeddingJob,
                    PaperEmbeddingJob.paper_id == Paper.id,
                )
                .where(PaperEmbeddingJob.status == "failed")
                .limit(batch_size)
            )

            no_job_result = await session.execute(no_job_stmt)
            failed_result = await session.execute(failed_job_stmt)

            paper_ids_no_job = [str(row[0]) for row in no_job_result.fetchall()]
            paper_ids_failed = [str(row[0]) for row in failed_result.fetchall()]

            # De-duplicate (a paper can't be in both sets, but be safe)
            all_ids = list(dict.fromkeys(paper_ids_no_job + paper_ids_failed))
            all_ids = all_ids[:batch_size]

            queued = 0
            for pid in all_ids:
                await embed_paper_async(pid, priority=0)
                queued += 1

            logger.info(
                "embedding_sweep_done",
                no_job=len(paper_ids_no_job),
                failed=len(paper_ids_failed),
                queued=queued,
            )
            return {"queued": queued}

    return _run_async(_sweep())
