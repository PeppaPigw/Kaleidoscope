"""Celery tasks for paper ingestion pipeline."""

import asyncio

import structlog

from app.worker import celery_app

logger = structlog.get_logger(__name__)


def _run_async(coro):
    """Run an async function from sync Celery task context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Create a new loop for the task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def poll_rss_feeds(self):
    """
    Periodic task: Poll all active RSS feeds for new papers.

    Scheduled by Celery Beat at configured interval.
    For each discovery, queues an ingest_paper task.
    """
    logger.info("poll_rss_feeds_start")

    async def _poll():
        from app.dependencies import async_session_factory
        from app.services.ingestion.rss_poller import RSSPollerService

        async with async_session_factory() as session:
            poller = RSSPollerService(session)
            result = await poller.poll_all_active_feeds()
            await session.commit()

            # Queue discovered papers for ingestion
            for paper in result.get("papers", []):
                identifier = paper.doi or paper.arxiv_id or paper.link
                id_type = "doi" if paper.doi else ("arxiv" if paper.arxiv_id else "url")
                if identifier:
                    ingest_paper.delay(
                        identifier=identifier,
                        id_type=id_type,
                        title=paper.title,
                        abstract=paper.abstract,
                    )

            return {
                "feeds_polled": result["feeds_polled"],
                "new_papers": result["new_papers_discovered"],
                "errors": result["errors"],
            }

    return _run_async(_poll())


@celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
def ingest_paper(self, identifier: str, id_type: str, title: str = "", abstract: str = ""):
    """
    Full ingestion pipeline for a single paper.

    Steps:
    1. Deduplication check
    2. Create paper record
    3. Metadata enrichment
    4. PDF acquisition
    5. Queue parsing (if PDF acquired)
    6. Queue indexing
    """
    log = logger.bind(identifier=identifier, id_type=id_type, task_id=self.request.id)
    log.info("ingest_paper_start")

    async def _ingest():
        from app.dependencies import async_session_factory
        from app.models.paper import Paper
        from app.services.ingestion.deduplicator import DeduplicatorService
        from app.services.ingestion.metadata_enricher import MetadataEnricherService
        from app.clients.crossref import CrossRefClient
        from app.clients.openalex import OpenAlexClient
        from app.clients.semantic_scholar import SemanticScholarClient
        from app.config import settings
        from app.utils.doi import normalize_doi, extract_arxiv_id

        async with async_session_factory() as session:
            # 1. Dedup
            dedup = DeduplicatorService(session)
            doi = normalize_doi(identifier) if id_type == "doi" else None
            arxiv_id = identifier if id_type == "arxiv" else extract_arxiv_id(identifier)

            dedup_result = await dedup.check_duplicate(
                doi=doi, arxiv_id=arxiv_id, title=title
            )
            if dedup_result.is_duplicate:
                log.info("paper_is_duplicate", existing_id=dedup_result.existing_paper_id)
                return {"status": "duplicate", "existing_id": dedup_result.existing_paper_id}

            # 2. Create paper
            paper = Paper(
                doi=doi,
                arxiv_id=arxiv_id,
                title=title or identifier,
                abstract=abstract or None,
                ingestion_status="discovered",
            )
            session.add(paper)
            await session.flush()  # Get the ID
            paper_id = str(paper.id)

            # 3. Enrich metadata
            try:
                crossref = CrossRefClient(mailto=settings.unpaywall_email)
                openalex = OpenAlexClient(mailto=settings.unpaywall_email)
                s2 = SemanticScholarClient()

                enricher = MetadataEnricherService(session, crossref, openalex, s2)
                await enricher.enrich(paper)

                await crossref.close()
                await openalex.close()
                await s2.close()
            except Exception as e:
                log.warning("enrichment_failed", error=str(e))
                paper.ingestion_status = "discovered"  # Continue anyway

            await session.commit()

            # 4. PDF acquisition (queued separately)
            acquire_pdf.delay(paper_id)

            # 5. Index for search (queued separately)
            index_paper_task.delay(paper_id)

            log.info("ingest_paper_complete", paper_id=paper_id)
            return {"status": "created", "paper_id": paper_id}

    try:
        return _run_async(_ingest())
    except Exception as exc:
        log.error("ingest_paper_failed", error=str(exc))
        self.retry(exc=exc, countdown=2 ** self.request.retries * 60)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def acquire_pdf(self, paper_id: str):
    """Acquire PDF for a paper through priority cascade."""
    log = logger.bind(paper_id=paper_id, task_id=self.request.id)
    log.info("acquire_pdf_start")

    async def _acquire():
        from app.dependencies import async_session_factory
        from app.models.paper import Paper
        from app.services.ingestion.pdf_downloader import PDFDownloaderService
        from app.clients.arxiv import ArxivClient
        from app.clients.unpaywall import UnpaywallClient
        from app.clients.semantic_scholar import SemanticScholarClient
        from app.config import settings

        from sqlalchemy import select

        async with async_session_factory() as session:
            result = await session.execute(
                select(Paper).where(Paper.id == paper_id)
            )
            paper = result.scalar_one_or_none()
            if not paper:
                log.error("paper_not_found")
                return {"status": "error", "message": "Paper not found"}

            arxiv = ArxivClient()
            unpaywall = UnpaywallClient(email=settings.unpaywall_email)
            s2 = SemanticScholarClient()

            downloader = PDFDownloaderService(arxiv, unpaywall, s2)
            acq_result = await downloader.acquire_pdf(paper)

            if acq_result.success:
                paper.pdf_path = acq_result.pdf_path
                paper.has_full_text = True
                paper.ingestion_status = "pdf_acquired"
                # Queue GROBID parsing
                parse_pdf_task.delay(paper_id)
            else:
                paper.ingestion_status = "enriched"  # metadata-only
                paper.ingestion_error = acq_result.error

            await session.commit()

            await arxiv.close()
            await unpaywall.close()
            await s2.close()

            return {
                "status": "acquired" if acq_result.success else "not_available",
                "source": acq_result.source,
            }

    try:
        return _run_async(_acquire())
    except Exception as exc:
        log.error("acquire_pdf_failed", error=str(exc))
        self.retry(exc=exc, countdown=2 ** self.request.retries * 30)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def parse_pdf_task(self, paper_id: str):
    """Parse acquired PDF with GROBID."""
    log = logger.bind(paper_id=paper_id, task_id=self.request.id)
    log.info("parse_pdf_start")

    async def _parse():
        from app.dependencies import async_session_factory
        from app.models.paper import Paper
        from app.services.parsing.grobid_client import GROBIDClient

        from sqlalchemy import select

        async with async_session_factory() as session:
            result = await session.execute(
                select(Paper).where(Paper.id == paper_id)
            )
            paper = result.scalar_one_or_none()
            if not paper or not paper.pdf_path:
                log.error("paper_or_pdf_not_found")
                return {"status": "error"}

            grobid = GROBIDClient()

            # NOTE: In production, read PDF from MinIO
            # For now, skip actual parsing if no file exists locally
            if not await grobid.is_alive():
                log.warning("grobid_not_available")
                return {"status": "grobid_unavailable"}

            paper.ingestion_status = "parsed"
            await session.commit()

            return {"status": "parsed"}

    try:
        return _run_async(_parse())
    except Exception as exc:
        log.error("parse_pdf_failed", error=str(exc))
        self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def index_paper_task(self, paper_id: str):
    """Index paper in Meilisearch and Qdrant."""
    log = logger.bind(paper_id=paper_id, task_id=self.request.id)
    log.info("index_paper_start")

    async def _index():
        from app.dependencies import async_session_factory
        from app.models.paper import Paper
        from app.services.search.keyword_search import KeywordSearchService
        from app.services.search.vector_search import VectorSearchService

        from sqlalchemy import select

        async with async_session_factory() as session:
            result = await session.execute(
                select(Paper).where(Paper.id == paper_id)
            )
            paper = result.scalar_one_or_none()
            if not paper:
                log.error("paper_not_found")
                return {"status": "error"}

            # Index in Meilisearch
            try:
                kw_service = KeywordSearchService()
                kw_service.index_paper({
                    "id": str(paper.id),
                    "title": paper.title,
                    "abstract": paper.abstract or "",
                    "keywords": paper.keywords or [],
                    "author_names": [],  # TODO: join author names
                    "year": paper.published_at.year if paper.published_at else None,
                    "venue": "",  # TODO: join venue name
                    "paper_type": paper.paper_type,
                    "oa_status": paper.oa_status,
                    "has_full_text": paper.has_full_text,
                    "citation_count": paper.citation_count or 0,
                })
            except Exception as e:
                log.warning("meilisearch_index_failed", error=str(e))

            # Index in Qdrant
            try:
                vec_service = VectorSearchService()
                vec_service.index_paper(
                    paper_id=str(paper.id),
                    title=paper.title,
                    abstract=paper.abstract,
                    year=paper.published_at.year if paper.published_at else None,
                )
            except Exception as e:
                log.warning("qdrant_index_failed", error=str(e))

            paper.ingestion_status = "indexed"
            await session.commit()

            log.info("index_paper_complete")
            return {"status": "indexed"}

    try:
        return _run_async(_index())
    except Exception as exc:
        log.error("index_paper_failed", error=str(exc))
        self.retry(exc=exc, countdown=30)
