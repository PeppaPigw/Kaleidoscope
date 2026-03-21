"""Celery tasks for graph sync operations."""

import structlog

from app.worker import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="graph.sync_paper", bind=True, max_retries=2)
def sync_paper_to_graph(self, paper_id: str) -> dict:
    """
    Sync a paper and its references to the Neo4j citation graph.

    This task is queued after parse_fulltext_task completes,
    or triggered manually via the graph API.
    """
    import asyncio
    from sqlalchemy import select

    async def _sync():
        from app.dependencies import async_session_factory
        from app.models.paper import Paper
        from app.services.graph.citation_graph import CitationGraphService

        async with async_session_factory() as session:
            result = await session.execute(
                select(Paper).where(Paper.id == paper_id)
            )
            paper = result.scalar_one_or_none()
            if not paper:
                logger.warning("graph_sync_paper_not_found", paper_id=paper_id)
                return {"error": "Paper not found"}

            svc = CitationGraphService(session)
            return await svc.sync_paper(paper)

    try:
        loop = asyncio.new_event_loop()
        return loop.run_until_complete(_sync())
    finally:
        loop.close()


@celery_app.task(name="graph.sync_batch", bind=True)
def sync_batch_to_graph(self, limit: int = 1000) -> dict:
    """Batch-sync all papers to Neo4j."""
    import asyncio

    async def _sync():
        from app.dependencies import async_session_factory
        from app.services.graph.citation_graph import CitationGraphService

        async with async_session_factory() as session:
            svc = CitationGraphService(session)
            synced = await svc.sync_all_papers(limit=limit)
            return {"synced": synced}

    try:
        loop = asyncio.new_event_loop()
        return loop.run_until_complete(_sync())
    finally:
        loop.close()
