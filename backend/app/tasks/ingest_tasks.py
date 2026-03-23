"""Celery tasks for paper ingestion pipeline.

Task chain: ingest_paper → acquire_fulltext → parse_fulltext → index_paper

Each task commits its state to the DB BEFORE queuing the next task,
ensuring the downstream task always sees the updated row.
"""

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
    1. Normalize identifier (DOI, arXiv, PMID, URL → DOI, title → CrossRef search)
    2. Deduplication check (including soft-deleted records)
    3. Create paper record
    4. Metadata enrichment
    5. Commit, then queue acquire_fulltext (which chains → parse → index)

    Note: Only acquire_fulltext is queued here. Parsing and indexing are
    chained downstream after each preceding step commits its results.
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
        from app.utils.doi import (
            normalize_doi, extract_arxiv_id, extract_pmid,
            normalize_arxiv_id, extract_doi_from_url,
        )

        async with async_session_factory() as session:
            # ── 1. Normalize identifier ──────────────────────────
            doi = None
            arxiv_id = None
            pmid = None

            if id_type == "doi":
                doi = normalize_doi(identifier)
            elif id_type == "arxiv":
                arxiv_id = normalize_arxiv_id(
                    extract_arxiv_id(identifier) or identifier
                )
            elif id_type == "pmid":
                pmid = extract_pmid(identifier)
                if not pmid:
                    log.warning("invalid_pmid", raw=identifier)
                    return {"status": "error", "message": f"Invalid PMID: {identifier}"}
            elif id_type == "url":
                # Try DOI extraction from publisher URL
                doi = extract_doi_from_url(identifier)
                if not doi:
                    # Try plain DOI normalization (handles doi.org URLs)
                    doi = normalize_doi(identifier)
                if not doi:
                    arxiv_id = extract_arxiv_id(identifier)
                    if arxiv_id:
                        arxiv_id = normalize_arxiv_id(arxiv_id)
                if not doi and not arxiv_id:
                    log.warning("url_no_identifier_found", url=identifier)
                    # Continue anyway — enricher's title search may resolve it
            elif id_type == "title":
                # Title-only import: enricher will search CrossRef
                pass
            else:
                # Default: try DOI first, then arXiv
                doi = normalize_doi(identifier)
                if not doi:
                    arxiv_id = extract_arxiv_id(identifier)
                    if arxiv_id:
                        arxiv_id = normalize_arxiv_id(arxiv_id)

            # ── 2. Dedup (including soft-deleted) ────────────────
            dedup = DeduplicatorService(session)
            dedup_result = await dedup.check_duplicate(
                doi=doi, arxiv_id=arxiv_id, title=title
            )
            if dedup_result.is_duplicate:
                if dedup_result.match_type == "soft_deleted":
                    # Restore the soft-deleted paper
                    log.info("restoring_soft_deleted_paper",
                             existing_id=dedup_result.existing_paper_id)
                    from sqlalchemy import update
                    await session.execute(
                        update(Paper)
                        .where(Paper.id == dedup_result.existing_paper_id)
                        .values(deleted_at=None, ingestion_status="discovered")
                    )
                    await session.commit()
                    paper_id = dedup_result.existing_paper_id
                    # Re-process: commit done, now safe to queue
                    acquire_fulltext.delay(paper_id)
                    return {"status": "restored", "paper_id": paper_id}
                else:
                    log.info("paper_is_duplicate", existing_id=dedup_result.existing_paper_id)
                    return {"status": "duplicate", "existing_id": dedup_result.existing_paper_id}

            # ── 3. Create paper ──────────────────────────────────
            paper = Paper(
                doi=doi,
                arxiv_id=arxiv_id,
                pmid=pmid,
                title=title or identifier,
                abstract=abstract or None,
                ingestion_status="discovered",
            )
            session.add(paper)
            await session.flush()  # Get the ID
            paper_id = str(paper.id)

            # ── 4. Enrich metadata ───────────────────────────────
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

            # ── 5. Commit FIRST, then queue downstream ───────────
            await session.commit()

            # Only acquire_fulltext is queued here.
            # It will chain: acquire → parse → index
            acquire_fulltext.delay(paper_id)

            log.info("ingest_paper_complete", paper_id=paper_id)
            return {"status": "created", "paper_id": paper_id}

    try:
        return _run_async(_ingest())
    except Exception as exc:
        log.error("ingest_paper_failed", error=str(exc))
        self.retry(exc=exc, countdown=2 ** self.request.retries * 60)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def acquire_fulltext(self, paper_id: str):
    """
    Acquire full-text for a paper through priority cascade.

    On success: commits pdf_path + has_full_text, then queues parse_fulltext_task.
    On failure: commits metadata-only status, then queues index_paper_task
                (so at least metadata gets indexed).
    """
    log = logger.bind(paper_id=paper_id, task_id=self.request.id)
    log.info("acquire_fulltext_start")

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
                paper.pdf_path = acq_result.storage_path
                paper.has_full_text = True
                paper.ingestion_status = "pdf_acquired"
                # Store content_type for parse task to branch on
                paper.raw_metadata = paper.raw_metadata or {}
                paper.raw_metadata["fulltext_content_type"] = acq_result.content_type
                paper.raw_metadata["fulltext_source"] = acq_result.source
            else:
                paper.ingestion_status = "enriched"  # metadata-only
                paper.ingestion_error = acq_result.error

            # ── Commit FIRST, then queue next task ───────────────
            await session.commit()

            await arxiv.close()
            await unpaywall.close()
            await s2.close()

            if acq_result.success:
                # Chain: parse will queue index after it finishes
                parse_fulltext_task.delay(paper_id, acq_result.content_type)
            else:
                # No full-text via traditional path — try MinerU if we have a URL
                mineru_url = None
                mineru_is_html = False

                if paper.remote_urls:
                    stored = next(
                        (u for u in paper.remote_urls if u.get("url")),
                        None,
                    )
                    if stored:
                        mineru_url = stored["url"]
                        mineru_is_html = stored.get("type") == "html"
                elif paper.arxiv_id:
                    # Canonical arXiv PDF URL
                    aid = paper.arxiv_id.replace("arxiv:", "")
                    mineru_url = f"https://arxiv.org/pdf/{aid}.pdf"
                    mineru_is_html = False
                elif paper.doi:
                    # DOI resolves to a landing page (HTML)
                    mineru_url = f"https://doi.org/{paper.doi}"
                    mineru_is_html = True

                if mineru_url:
                    log.info("fallback_to_mineru", url=mineru_url[:80], is_html=mineru_is_html)
                    parse_via_mineru.delay(paper_id, mineru_url, is_html=mineru_is_html)
                else:
                    # No URL, just index metadata
                    index_paper_task.delay(paper_id)

            return {
                "status": "acquired" if acq_result.success else "not_available",
                "source": acq_result.source,
                "content_type": acq_result.content_type if acq_result.success else None,
            }

    try:
        return _run_async(_acquire())
    except Exception as exc:
        log.error("acquire_fulltext_failed", error=str(exc))
        self.retry(exc=exc, countdown=2 ** self.request.retries * 30)


# Keep old name as alias
acquire_pdf = acquire_fulltext


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def parse_fulltext_task(self, paper_id: str, content_type: str = "pdf"):
    """
    Parse acquired full-text based on its content type.

    Routes:
    - PDF  → GROBID API → structured TEI XML
    - TeX  → ArxivClient.extract_text_from_latex() → plain text with sections
    - XML  → Direct use (Elsevier/Springer already structured)

    After parsing completes and commits, queues index_paper_task so the
    search index reflects the parsed content (title, abstract, keywords).
    """
    log = logger.bind(paper_id=paper_id, content_type=content_type, task_id=self.request.id)
    log.info("parse_fulltext_start")

    async def _parse():
        from app.dependencies import async_session_factory
        from app.models.paper import Paper
        from app.services.parsing.grobid_client import GROBIDClient
        from app.services.ingestion.pdf_downloader import PDFDownloaderService
        from app.clients.arxiv import ArxivClient

        from sqlalchemy import select

        async with async_session_factory() as session:
            result = await session.execute(
                select(Paper).where(Paper.id == paper_id)
            )
            paper = result.scalar_one_or_none()
            if not paper or not paper.pdf_path:
                log.error("paper_or_content_not_found")
                return {"status": "error"}

            # Load persisted content
            content = PDFDownloaderService.load_content(paper.pdf_path)
            if content is None:
                log.error("content_not_on_disk", path=paper.pdf_path)
                paper.ingestion_error = f"Content file not found: {paper.pdf_path}"
                paper.ingestion_status = "parse_failed"
                await session.commit()
                return {"status": "error", "message": "Content not found on disk"}

            try:
                if content_type == "pdf":
                    # ── PDF → GROBID ─────────────────────────────
                    grobid = GROBIDClient()
                    if not await grobid.is_alive():
                        log.warning("grobid_not_available")
                        paper.ingestion_error = "GROBID service unavailable"
                        paper.ingestion_status = "parse_failed"
                        await session.commit()
                        # Still index metadata even if parse fails
                        index_paper_task.delay(paper_id)
                        return {"status": "grobid_unavailable"}

                    grobid_result = await grobid.parse_pdf(content, paper_id=paper_id)
                    paper.grobid_tei = grobid_result.tei_xml
                    # Update metadata from GROBID if better than existing
                    if grobid_result.title and (not paper.title or paper.title == paper.doi):
                        paper.title = grobid_result.title
                    if grobid_result.abstract and not paper.abstract:
                        paper.abstract = grobid_result.abstract
                    if grobid_result.keywords:
                        paper.keywords = grobid_result.keywords
                    # Store sections in raw_metadata for downstream use
                    paper.raw_metadata = paper.raw_metadata or {}
                    paper.raw_metadata["parsed_sections"] = grobid_result.sections
                    paper.raw_metadata["parsed_references"] = grobid_result.references
                    paper.parser_version = "grobid"
                    log.info("grobid_parse_complete",
                             sections=len(grobid_result.sections),
                             references=len(grobid_result.references))

                elif content_type == "tex":
                    # ── LaTeX → plain text extraction ────────────
                    tex_source = content.decode("utf-8", errors="replace")
                    extracted_text = ArxivClient.extract_text_from_latex(tex_source)
                    paper.raw_metadata = paper.raw_metadata or {}
                    paper.raw_metadata["extracted_fulltext"] = extracted_text[:100000]  # Cap size
                    paper.raw_metadata["tex_source_length"] = len(tex_source)
                    paper.parser_version = "latex_extract"
                    log.info("latex_parse_complete", text_length=len(extracted_text))

                elif content_type == "xml":
                    # ── TDM XML → stored as-is (already structured) ──
                    xml_text = content.decode("utf-8", errors="replace")
                    paper.grobid_tei = xml_text  # Reuse grobid_tei column for structured XML
                    paper.raw_metadata = paper.raw_metadata or {}
                    paper.raw_metadata["xml_source"] = "tdm_api"
                    paper.parser_version = "tdm_xml"
                    log.info("xml_parse_complete", xml_length=len(xml_text))

                else:
                    log.warning("unknown_content_type", content_type=content_type)
                    paper.ingestion_status = "parse_failed"
                    paper.ingestion_error = f"Unknown content type: {content_type}"
                    await session.commit()
                    index_paper_task.delay(paper_id)
                    return {"status": "error", "message": f"Unknown content type: {content_type}"}

                paper.ingestion_status = "parsed"

                # ── Materialize PaperReference rows from parsed data ──
                # Idempotent: delete existing refs before re-inserting
                from app.models.paper import PaperReference
                from sqlalchemy import delete as sa_delete

                await session.execute(
                    sa_delete(PaperReference).where(
                        PaperReference.citing_paper_id == paper.id
                    )
                )

                parsed_refs = (paper.raw_metadata or {}).get("parsed_references", [])
                for ref in parsed_refs:
                    paper_ref = PaperReference(
                        citing_paper_id=paper.id,
                        cited_paper_id=None,  # Resolved later by reference linker
                        raw_title=ref.get("title"),
                        raw_authors=", ".join(ref.get("authors", [])),
                        raw_year=ref.get("year"),
                        raw_doi=ref.get("doi"),
                        raw_string=ref.get("raw_string"),
                        position=ref.get("position"),
                    )
                    session.add(paper_ref)

                if parsed_refs:
                    log.info("references_materialized", count=len(parsed_refs))

                # ── Resolve cited_paper_id by matching DOI/title ──
                # This is the "reference linker" step that connects edges
                unresolved = await session.execute(
                    select(PaperReference).where(
                        PaperReference.citing_paper_id == paper.id,
                        PaperReference.cited_paper_id.is_(None),
                    )
                )
                resolved_count = 0
                for ref in unresolved.scalars().all():
                    cited = None
                    # 1) Match by DOI (exact, fast)
                    if ref.raw_doi:
                        doi_result = await session.execute(
                            select(Paper.id).where(
                                Paper.doi == ref.raw_doi,
                                Paper.deleted_at.is_(None),
                            ).limit(1)
                        )
                        cited = doi_result.scalar_one_or_none()

                    # 2) Fallback: match by title (case-insensitive)
                    if not cited and ref.raw_title and len(ref.raw_title) > 10:
                        title_result = await session.execute(
                            select(Paper.id).where(
                                Paper.title.ilike(ref.raw_title.strip()),
                                Paper.deleted_at.is_(None),
                            ).limit(1)
                        )
                        cited = title_result.scalar_one_or_none()

                    if cited:
                        ref.cited_paper_id = cited
                        resolved_count += 1

                if resolved_count:
                    log.info("references_resolved", resolved=resolved_count)

                # ── Commit FIRST, then queue index ───────────────
                await session.commit()

                # Now index with the freshly parsed data
                index_paper_task.delay(paper_id)

                # Queue graph sync if references were materialized
                if parsed_refs:
                    try:
                        from app.tasks.graph_tasks import sync_paper_to_graph
                        sync_paper_to_graph.delay(paper_id)
                        log.info("graph_sync_queued", paper_id=paper_id)
                    except Exception as e:
                        log.warning("graph_sync_queue_failed", error=str(e))

                return {"status": "parsed", "parser": paper.parser_version}

            except Exception as e:
                log.error("parse_failed", error=str(e))
                paper.ingestion_status = "parse_failed"
                paper.ingestion_error = str(e)[:500]
                await session.commit()
                # Still index metadata
                index_paper_task.delay(paper_id)
                return {"status": "error", "message": str(e)}

    try:
        return _run_async(_parse())
    except Exception as exc:
        log.error("parse_fulltext_failed", error=str(exc))
        self.retry(exc=exc, countdown=60)


# Keep old name as alias for backward compat
parse_pdf_task = parse_fulltext_task


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def index_paper_task(self, paper_id: str):
    """
    Index paper in Meilisearch and Qdrant.

    Always runs as the LAST step in the chain, so it has access to
    all metadata, parsed content, and enriched fields.

    Tracks per-engine success and sets differentiated status.
    """
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

            meili_ok = False
            qdrant_ok = False

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
                meili_ok = True
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
                qdrant_ok = True
            except Exception as e:
                log.warning("qdrant_index_failed", error=str(e))

            # ── Set status based on actual results ───────────────
            if meili_ok and qdrant_ok:
                paper.ingestion_status = "indexed"
            elif meili_ok or qdrant_ok:
                paper.ingestion_status = "index_partial"
                paper.ingestion_error = (
                    f"Partial index: meili={'ok' if meili_ok else 'FAIL'}, "
                    f"qdrant={'ok' if qdrant_ok else 'FAIL'}"
                )
                log.warning("index_partial", meili=meili_ok, qdrant=qdrant_ok)
            else:
                paper.ingestion_status = "index_failed"
                paper.ingestion_error = "Both Meilisearch and Qdrant indexing failed"
                log.error("index_both_failed")

            await session.commit()

            log.info("index_paper_complete", meili=meili_ok, qdrant=qdrant_ok)
            return {"status": paper.ingestion_status, "meili": meili_ok, "qdrant": qdrant_ok}

    try:
        return _run_async(_index())
    except Exception as exc:
        log.error("index_paper_failed", error=str(exc))
        self.retry(exc=exc, countdown=30)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def parse_via_mineru(self, paper_id: str, url: str, is_html: bool = False):
    """
    Parse a paper from URL using MinerU API → stored as markdown.

    Alternative to parse_fulltext_task (GROBID). Uses MinerU cloud API
    for PDF/HTML → Markdown conversion.

    After parsing, queues index_paper_task for search indexing.
    """
    log = logger.bind(paper_id=paper_id, url=url[:80], task_id=self.request.id)
    log.info("parse_via_mineru_start")

    async def _parse():
        from app.dependencies import async_session_factory
        from app.services.parsing.mineru_service import MinerUParsingService

        async with async_session_factory() as session:
            svc = MinerUParsingService(session)
            try:
                result = await svc.parse_from_url(
                    paper_id=paper_id,
                    url=url,
                    is_html=is_html,
                )
            finally:
                await svc.close()

            await session.commit()

            if result.get("status") == "parsed":
                # Queue graph sync if references were found
                if result.get("references", 0) > 0:
                    try:
                        from app.tasks.graph_tasks import sync_paper_to_graph
                        sync_paper_to_graph.delay(paper_id)
                        log.info("graph_sync_queued", paper_id=paper_id)
                    except Exception as e:
                        log.warning("graph_sync_queue_failed", error=str(e))

            # Always index metadata whether parse succeeded or failed
            index_paper_task.delay(paper_id)

            return result

    try:
        return _run_async(_parse())
    except Exception as exc:
        log.error("parse_via_mineru_failed", error=str(exc))
        self.retry(exc=exc, countdown=2 ** self.request.retries * 60)

