"""Celery tasks for paper ingestion pipeline.

Task chain: ingest_paper → acquire_fulltext → parse_fulltext → index_paper

Each task commits its state to the DB BEFORE queuing the next task,
ensuring the downstream task always sees the updated row.
"""

import asyncio

import structlog
from celery.exceptions import MaxRetriesExceededError

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
def ingest_paper(
    self, identifier: str, id_type: str, title: str = "", abstract: str = ""
):
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
    task_state: dict[str, str | None] = {"paper_id": None}

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
            normalize_doi,
            extract_arxiv_id,
            extract_pmid,
            normalize_arxiv_id,
            extract_doi_from_url,
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
                    log.info(
                        "restoring_soft_deleted_paper",
                        existing_id=dedup_result.existing_paper_id,
                    )
                    from sqlalchemy import update

                    await session.execute(
                        update(Paper)
                        .where(Paper.id == dedup_result.existing_paper_id)
                        .values(deleted_at=None, ingestion_status="discovered")
                    )
                    await session.commit()
                    paper_id = dedup_result.existing_paper_id
                    task_state["paper_id"] = str(paper_id)
                    # Re-process: commit done, now safe to queue
                    acquire_fulltext.delay(paper_id)
                    return {"status": "restored", "paper_id": paper_id}
                else:
                    log.info(
                        "paper_is_duplicate", existing_id=dedup_result.existing_paper_id
                    )
                    return {
                        "status": "duplicate",
                        "existing_id": dedup_result.existing_paper_id,
                    }

            # ── 3. Create paper ──────────────────────────────────
            paper = Paper(
                doi=doi,
                arxiv_id=arxiv_id,
                pmid=pmid,
                title=title or "",
                abstract=abstract or None,
                ingestion_status="discovered",
            )
            session.add(paper)
            await session.flush()  # Get the ID
            paper_id = str(paper.id)
            task_state["paper_id"] = paper_id

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
            fetch_paper_links_task.delay(paper_id)

            log.info("ingest_paper_complete", paper_id=paper_id)
            return {"status": "created", "paper_id": paper_id}

    try:
        return _run_async(_ingest())
    except Exception as exc:
        log.error("ingest_paper_failed", error=str(exc))
        try:
            raise self.retry(exc=exc, countdown=2**self.request.retries * 60)
        except MaxRetriesExceededError:
            logger.error(
                "ingest_failed_permanently",
                task_id=self.request.id,
                paper_id=task_state["paper_id"] or identifier,
                error=str(exc),
            )
            raise


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def acquire_fulltext(self, paper_id: str):
    """
    Acquire full-text for a paper through priority cascade.

    For remote papers, parsing now prefers MinerU whenever we can resolve
    a stable source URL. The older local parser path is kept only as a
    fallback for records that have downloaded content but no parseable URL.

    On success: commits pdf_path + has_full_text, then queues MinerU (preferred)
    or parse_fulltext_task (fallback).
    On failure: tries MinerU from a known remote URL; otherwise queues
                index_paper_task so at least metadata gets indexed.
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
            result = await session.execute(select(Paper).where(Paper.id == paper_id))
            paper = result.scalar_one_or_none()
            if not paper:
                log.error("paper_not_found")
                return {"status": "error", "message": "Paper not found"}

            def resolve_mineru_target() -> tuple[str | None, bool]:
                if paper.remote_urls:
                    stored = next(
                        (u for u in paper.remote_urls if u.get("url")),
                        None,
                    )
                    if stored and stored.get("url"):
                        return stored["url"], stored.get("type") == "html"

                if paper.arxiv_id:
                    aid = paper.arxiv_id.replace("arxiv:", "")
                    return f"https://arxiv.org/pdf/{aid}.pdf", False

                if paper.doi:
                    return f"https://doi.org/{paper.doi}", True

                return None, False

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

            mineru_url, mineru_is_html = resolve_mineru_target()

            if mineru_url:
                log.info(
                    "queue_parse_via_mineru",
                    url=mineru_url[:80],
                    is_html=mineru_is_html,
                    acquired_pdf=acq_result.success,
                )
                parse_via_mineru.delay(paper_id, mineru_url, is_html=mineru_is_html)
            elif acq_result.success:
                # No remote URL available, so fall back to local parsing.
                parse_fulltext_task.delay(paper_id, acq_result.content_type)
            else:
                # No parseable source URL and no acquired content — index metadata only.
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
        self.retry(exc=exc, countdown=2**self.request.retries * 30)


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
    log = logger.bind(
        paper_id=paper_id, content_type=content_type, task_id=self.request.id
    )
    log.info("parse_fulltext_start")

    async def _parse():
        from app.dependencies import async_session_factory
        from app.models.paper import Paper
        from app.services.parsing.grobid_client import GROBIDClient
        from app.services.ingestion.pdf_downloader import PDFDownloaderService
        from app.clients.arxiv import ArxivClient

        from sqlalchemy import select

        async with async_session_factory() as session:
            result = await session.execute(select(Paper).where(Paper.id == paper_id))
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
                    if grobid_result.title and (
                        not paper.title or paper.title == paper.doi
                    ):
                        paper.title = grobid_result.title
                    if grobid_result.abstract and not paper.abstract:
                        paper.abstract = grobid_result.abstract
                    if grobid_result.keywords:
                        paper.keywords = grobid_result.keywords
                    # Store sections in BOTH the direct column (for content API)
                    # and raw_metadata (for downstream analysis)
                    paper.parsed_sections = grobid_result.sections
                    paper.raw_metadata = paper.raw_metadata or {}
                    paper.raw_metadata["parsed_sections"] = grobid_result.sections
                    paper.raw_metadata["parsed_references"] = grobid_result.references
                    # Explicitly flag in-place JSONB mutation for change tracking
                    from sqlalchemy.orm.attributes import flag_modified

                    flag_modified(paper, "raw_metadata")
                    paper.parser_version = "grobid"
                    log.info(
                        "grobid_parse_complete",
                        sections=len(grobid_result.sections),
                        references=len(grobid_result.references),
                    )

                elif content_type == "tex":
                    # ── LaTeX → plain text extraction ────────────
                    tex_source = content.decode("utf-8", errors="replace")
                    extracted_text = ArxivClient.extract_text_from_latex(tex_source)
                    paper.raw_metadata = paper.raw_metadata or {}
                    paper.raw_metadata["extracted_fulltext"] = extracted_text[
                        :100000
                    ]  # Cap size
                    paper.raw_metadata["tex_source_length"] = len(tex_source)
                    paper.parser_version = "latex_extract"
                    log.info("latex_parse_complete", text_length=len(extracted_text))

                elif content_type == "xml":
                    # ── TDM XML → stored as-is (already structured) ──
                    xml_text = content.decode("utf-8", errors="replace")
                    paper.grobid_tei = (
                        xml_text  # Reuse grobid_tei column for structured XML
                    )
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
                    return {
                        "status": "error",
                        "message": f"Unknown content type: {content_type}",
                    }

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
                            select(Paper.id)
                            .where(
                                Paper.doi == ref.raw_doi,
                                Paper.deleted_at.is_(None),
                            )
                            .limit(1)
                        )
                        cited = doi_result.scalar_one_or_none()

                    # 2) Fallback: match by title (case-insensitive)
                    if not cited and ref.raw_title and len(ref.raw_title) > 10:
                        title_result = await session.execute(
                            select(Paper.id)
                            .where(
                                Paper.title.ilike(ref.raw_title.strip()),
                                Paper.deleted_at.is_(None),
                            )
                            .limit(1)
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
                logger.warning(
                    "parser_failure",
                    paper_id=paper_id,
                    stage=content_type,
                    error=str(e),
                )
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
            result = await session.execute(select(Paper).where(Paper.id == paper_id))
            paper = result.scalar_one_or_none()
            if not paper:
                log.error("paper_not_found")
                return {"status": "error"}

            meili_ok = False
            qdrant_ok = False

            # Index in Meilisearch
            try:
                kw_service = KeywordSearchService()
                # Resolve author names from relationship
                author_names = []
                if hasattr(paper, "authors") and paper.authors:
                    author_names = [a.name for a in paper.authors if a.name]
                # Resolve venue from relationship
                venue_name = ""
                if hasattr(paper, "venue") and paper.venue:
                    venue_name = paper.venue.name or ""
                kw_service.index_paper(
                    {
                        "id": str(paper.id),
                        "title": paper.title or "",
                        "abstract": paper.abstract or "",
                        "keywords": paper.keywords or [],
                        "author_names": author_names,
                        "year": paper.published_at.year if paper.published_at else None,
                        "venue": venue_name,
                        "paper_type": paper.paper_type,
                        "oa_status": paper.oa_status,
                        "has_full_text": paper.has_full_text,
                        "citation_count": paper.citation_count or 0,
                    }
                )
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

            # ── Evaluate alert rules for newly indexed paper ──────
            if paper.ingestion_status == "indexed":
                try:
                    from app.models.collection import DEFAULT_USER_ID
                    from app.api.v1.sse import broadcast_event as _broadcast
                    from app.services.monitoring.alert_service import AlertService

                    alert_svc = AlertService(session, user_id=DEFAULT_USER_ID)
                    fired = await alert_svc.evaluate_rules(paper)
                    if fired:
                        await session.commit()
                        log.info("alerts_fired", count=len(fired))
                        for alert in fired:
                            try:
                                _broadcast(
                                    "alert.matched",
                                    {
                                        "alert_id": str(getattr(alert, "id", "")),
                                        "paper_id": paper_id,
                                        "title": paper.title,
                                        "rule_name": str(
                                            getattr(alert, "rule_name", "")
                                        ),
                                    },
                                )
                            except Exception:
                                pass
                except Exception as e:
                    log.warning("alert_evaluation_failed", error=str(e))

                # ── Fire webhooks for newly indexed paper ──────────
                try:
                    from app.services.governance_service import GovernanceService

                    gov_svc = GovernanceService(session)
                    await gov_svc.fire_webhooks(
                        "paper.indexed",
                        {
                            "paper_id": paper_id,
                            "title": paper.title,
                            "doi": paper.doi,
                        },
                    )
                    # Commit so hook.last_triggered_at persists (task uses raw session,
                    # not the auto-committing get_db() wrapper)
                    await session.commit()
                except Exception as e:
                    log.warning("webhook_dispatch_failed", error=str(e))

                # ── Broadcast to SSE subscribers ──────────────────
                try:
                    from app.api.v1.sse import broadcast_event

                    broadcast_event(
                        "paper.indexed",
                        {
                            "paper_id": paper_id,
                            "title": paper.title,
                            "doi": paper.doi,
                            "arxiv_id": paper.arxiv_id,
                        },
                    )
                except Exception as e:
                    log.warning("sse_broadcast_failed", error=str(e))

                # ── Evaluate smart collections ────────────────────
                try:
                    from app.services.collection_service import CollectionService

                    col_svc = CollectionService(session, user_id=DEFAULT_USER_ID)
                    matched = await col_svc.evaluate_smart_collections(paper)
                    if matched:
                        await session.commit()
                        log.info("smart_collections_matched", count=len(matched))
                except Exception as e:
                    log.warning("smart_collection_eval_failed", error=str(e))

                # ── Auto-label newly indexed paper ────────────────
                try:
                    from app.services.analysis.labeling_service import LabelingService

                    label_svc = LabelingService(session)
                    await label_svc.label_paper(paper)
                    await session.commit()
                    await label_svc.close()
                    log.info("paper_labeled_on_index")
                except Exception as e:
                    log.warning("paper_label_on_index_failed", error=str(e))

                # ── Auto deep-analyse newly indexed paper ─────────
                _analysis_ok = False
                try:
                    from app.services.analysis.paper_analyst import (
                        PaperAnalystService,
                        deep_analysis_is_valid,
                    )

                    analyst = PaperAnalystService(session)
                    await analyst.analyse_and_persist(paper, session)
                    await session.commit()
                    await analyst.close()
                    log.info("paper_analysed_on_index")
                    _analysis_ok = deep_analysis_is_valid(paper.deep_analysis)
                except Exception as e:
                    log.warning("paper_analysis_on_index_failed", error=str(e))

                # ── Auto generate 一图速览 after deep analysis ──────
                if _analysis_ok:
                    try:
                        from app.services.analysis.overview_image_service import (
                            OverviewImageService,
                        )
                        from datetime import datetime, timezone

                        analysis_text = (paper.deep_analysis or {}).get("analysis", "")
                        if analysis_text:
                            paper.overview_image = {"status": "generating"}
                            paper.overview_image_at = datetime.now(timezone.utc)
                            await session.commit()

                            img_svc = OverviewImageService()
                            try:
                                url = await img_svc.generate(paper.title, analysis_text)
                                paper.overview_image = {
                                    "status": "ok",
                                    "url": url,
                                    "generated_at": datetime.now(
                                        timezone.utc
                                    ).isoformat(),
                                }
                            except Exception as img_e:
                                paper.overview_image = {
                                    "status": "error",
                                    "error": str(img_e)[:300],
                                }
                                log.warning(
                                    "overview_image_on_index_failed",
                                    error=str(img_e)[:120],
                                )
                            finally:
                                await img_svc.close()

                            paper.overview_image_at = datetime.now(timezone.utc)
                            await session.commit()
                            log.info(
                                "overview_image_on_index_done",
                                status=paper.overview_image.get("status"),
                            )
                    except Exception as e:
                        log.warning(
                            "overview_image_on_index_outer_failed", error=str(e)
                        )

            log.info("index_paper_complete", meili=meili_ok, qdrant=qdrant_ok)
            return {
                "status": paper.ingestion_status,
                "meili": meili_ok,
                "qdrant": qdrant_ok,
            }

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
        logger.warning(
            "parser_failure",
            paper_id=paper_id,
            stage="mineru",
            error=str(exc),
        )
        log.error("parse_via_mineru_failed", error=str(exc))
        self.retry(exc=exc, countdown=2**self.request.retries * 60)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def fetch_paper_links_task(self, paper_id: str):
    """Fetch AI-powered supplementary links for a paper (venue, code, datasets, etc.)."""
    log = logger.bind(paper_id=paper_id, task_id=self.request.id)
    log.info("fetch_paper_links_start")

    async def _fetch():
        from sqlalchemy import select
        from app.dependencies import async_session_factory
        from app.models.paper import Paper
        from app.services.analysis.links_service import LinksService
        from datetime import datetime, timezone

        async with async_session_factory() as session:
            result = await session.execute(select(Paper).where(Paper.id == paper_id))
            paper = result.scalar_one_or_none()
            if not paper:
                return {"status": "error", "message": "Paper not found"}
            if not paper.title.strip():
                return {"status": "skip", "message": "No title"}
            if (paper.paper_links or {}).get("status") in ("ok", "fetching"):
                return {"status": "skip", "message": "Already done"}
            paper.paper_links = {"status": "fetching"}
            paper.paper_links_at = datetime.now(timezone.utc)
            await session.commit()
            title = paper.title
            arxiv_id = paper.arxiv_id
            doi = paper.doi

        try:
            async with LinksService() as svc:
                links = await svc.fetch_links(title, arxiv_id=arxiv_id, doi=doi)
            links_data = {
                "status": "ok",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                **links,
            }
            log.info("fetch_paper_links_done", title=title[:60])
        except Exception as e:
            links_data = {"status": "error", "error": str(e)[:300]}
            log.warning("fetch_paper_links_error", error=str(e)[:120])

        async with async_session_factory() as session:
            result = await session.execute(select(Paper).where(Paper.id == paper_id))
            paper = result.scalar_one_or_none()
            if paper:
                paper.paper_links = links_data
                paper.paper_links_at = datetime.now(timezone.utc)
                await session.commit()

        return links_data

    try:
        return _run_async(_fetch())
    except Exception as exc:
        log.error("fetch_paper_links_failed", error=str(exc))
        try:
            raise self.retry(exc=exc, countdown=2**self.request.retries * 60)
        except MaxRetriesExceededError:
            raise


@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def auto_discover_papers(self):
    """
    Periodic task: Automatically discover and ingest trending papers.

    This task runs periodically to:
    1. Fetch trending papers from DeepXiv (7-day, 14-day, 30-day windows)
    2. Search for high-impact papers in key categories
    3. Queue new papers for ingestion

    Scheduled by Celery Beat to continuously expand the database.
    """
    log = logger.bind(task="auto_discover_papers")
    log.info("auto_discover_start")

    async def _discover():
        from app.dependencies import async_session_factory
        from app.models.paper import Paper
        from app.services.deepxiv_service import get_deepxiv_service
        from sqlalchemy import select

        deepxiv = get_deepxiv_service()
        total_queued = 0
        total_skipped = 0

        # 1. Fetch trending papers from multiple time windows
        for days in [7, 14, 30]:
            try:
                trending_resp = await deepxiv.trending(days=days, limit=50)
                papers_list = trending_resp.get("papers", [])
                arxiv_ids = [p["arxiv_id"] for p in papers_list if p.get("arxiv_id")]

                if arxiv_ids:
                    async with async_session_factory() as session:
                        result = await session.execute(
                            select(Paper.arxiv_id).where(Paper.arxiv_id.in_(arxiv_ids))
                        )
                        existing_ids = {row[0] for row in result.fetchall()}
                        new_ids = [aid for aid in arxiv_ids if aid not in existing_ids]

                        for arxiv_id in new_ids:
                            try:
                                ingest_paper.delay(arxiv_id, "arxiv")
                                total_queued += 1
                            except Exception:
                                log.warning("failed_to_queue", arxiv_id=arxiv_id)

                        total_skipped += len(existing_ids)
                        log.info(
                            "trending_batch_done",
                            days=days,
                            queued=len(new_ids),
                            skipped=len(existing_ids),
                        )
            except Exception as e:
                log.warning("trending_fetch_failed", days=days, error=str(e)[:200])

        # 2. Search for high-impact papers in key categories
        categories = ["cs.AI", "cs.LG", "cs.CL", "cs.CV", "stat.ML"]
        for category in categories:
            try:
                search_resp = await deepxiv.search(
                    q="",
                    size=20,
                    offset=0,
                    search_mode="hybrid",
                    bm25_weight=0.5,
                    vector_weight=0.5,
                    categories=[category],
                    authors=None,
                    min_citation=10,
                    date_from=None,
                    date_to=None,
                )

                results = search_resp.get("results", [])
                arxiv_ids = [r.get("arxiv_id") for r in results if r.get("arxiv_id")]

                if arxiv_ids:
                    async with async_session_factory() as session:
                        result = await session.execute(
                            select(Paper.arxiv_id).where(Paper.arxiv_id.in_(arxiv_ids))
                        )
                        existing_ids = {row[0] for row in result.fetchall()}
                        new_ids = [aid for aid in arxiv_ids if aid not in existing_ids]

                        for arxiv_id in new_ids:
                            try:
                                ingest_paper.delay(arxiv_id, "arxiv")
                                total_queued += 1
                            except Exception:
                                log.warning("failed_to_queue", arxiv_id=arxiv_id)

                        total_skipped += len(existing_ids)
                        log.info(
                            "category_batch_done",
                            category=category,
                            queued=len(new_ids),
                            skipped=len(existing_ids),
                        )
            except Exception as e:
                log.warning(
                    "category_search_failed", category=category, error=str(e)[:200]
                )

        log.info(
            "auto_discover_complete",
            total_queued=total_queued,
            total_skipped=total_skipped,
        )
        return {"queued": total_queued, "skipped": total_skipped}

    try:
        return _run_async(_discover())
    except Exception as exc:
        log.error("auto_discover_failed", error=str(exc))
        try:
            raise self.retry(exc=exc, countdown=300)
        except MaxRetriesExceededError:
            log.error("auto_discover_max_retries_exceeded")
            raise


@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def refresh_trending_keywords(self):
    """
    Periodic task: Refresh trending keywords cache from local database.

    Extracts meaningful research keywords from paper titles and abstracts.
    Focuses on multi-word technical terms and research concepts.
    """
    log = logger.bind(task="refresh_trending_keywords")
    log.info("refresh_keywords_start")

    async def _refresh():
        import re
        from collections import Counter
        from datetime import datetime, timedelta
        from app.dependencies import async_session_factory
        from app.models.paper import Paper
        from app.services.cache_service import get_cache_service
        from sqlalchemy import select, desc

        cache = get_cache_service()

        try:
            cutoff_date = datetime.utcnow() - timedelta(days=30)

            async with async_session_factory() as session:
                result = await session.execute(
                    select(Paper.title, Paper.abstract)
                    .where(
                        Paper.deleted_at.is_(None),
                        Paper.title.isnot(None),
                        Paper.created_at >= cutoff_date,
                    )
                    .order_by(desc(Paper.citation_count), desc(Paper.created_at))
                    .limit(200)
                )
                papers = result.all()

            if not papers:
                log.warning("no_papers_found")
                return {"keywords": [], "papers_processed": 0}

            log.info("fetched_papers", count=len(papers))

            # Extract multi-word phrases and technical terms
            keyword_freq: Counter = Counter()

            # Stop words - generic terms to exclude
            stop_words = {
                "model",
                "models",
                "method",
                "methods",
                "approach",
                "approaches",
                "paper",
                "study",
                "research",
                "analysis",
                "system",
                "systems",
                "performance",
                "results",
                "evaluation",
                "experiments",
                "data",
                "using",
                "based",
                "novel",
                "improved",
                "efficient",
                "effective",
                "propose",
                "proposed",
                "present",
                "presented",
                "show",
                "demonstrate",
                "across",
                "while",
                "through",
                "within",
                "between",
                "among",
                "framework",
                "frameworks",
                "technique",
                "techniques",
            }

            # Multi-word patterns to extract (research methods, architectures, concepts)
            bigram_patterns = [
                r"\b(deep learning|machine learning|reinforcement learning|transfer learning|meta learning|few shot learning|zero shot learning)\b",
                r"\b(neural network|convolutional neural|recurrent neural|graph neural|attention mechanism)\b",
                r"\b(large language model|language model|vision transformer|diffusion model|generative model)\b",
                r"\b(natural language|computer vision|speech recognition|image generation|text generation)\b",
                r"\b(self supervised|semi supervised|unsupervised learning|supervised learning|contrastive learning)\b",
                r"\b(prompt engineering|in context learning|chain of thought|retrieval augmented)\b",
                r"\b(knowledge graph|graph convolution|message passing|graph attention)\b",
                r"\b(object detection|semantic segmentation|instance segmentation|image classification)\b",
                r"\b(question answering|information retrieval|document understanding|reading comprehension)\b",
                r"\b(multi modal|cross modal|vision language|audio visual)\b",
                r"\b(adversarial training|adversarial attack|robust optimization|domain adaptation)\b",
                r"\b(neural architecture|architecture search|model compression|knowledge distillation)\b",
                r"\b(time series|sequence modeling|temporal modeling|video understanding)\b",
                r"\b(federated learning|distributed training|parallel computing|edge computing)\b",
                r"\b(quantum computing|quantum machine|quantum algorithm)\b",
            ]

            # Single technical terms (specific architectures, algorithms, concepts)
            technical_terms = {
                "transformer",
                "bert",
                "gpt",
                "llama",
                "clip",
                "vit",
                "resnet",
                "unet",
                "diffusion",
                "gan",
                "vae",
                "autoencoder",
                "lstm",
                "gru",
                "attention",
                "embedding",
                "tokenization",
                "fine-tuning",
                "pretraining",
                "reasoning",
                "planning",
                "grounding",
                "alignment",
                "hallucination",
                "multimodal",
                "cross-modal",
                "retrieval",
                "ranking",
                "reranking",
                "optimization",
                "regularization",
                "normalization",
                "dropout",
                "backpropagation",
                "gradient",
                "convergence",
                "overfitting",
                "classification",
                "regression",
                "clustering",
                "segmentation",
                "detection",
                "tracking",
                "recognition",
                "generation",
                "synthesis",
                "quantum",
                "probabilistic",
                "bayesian",
                "stochastic",
                "deterministic",
            }

            papers_processed = 0
            for title, abstract in papers:
                papers_processed += 1
                text = (title or "") + " " + (abstract or "")
                text_lower = text.lower()

                # Extract multi-word phrases (higher weight)
                for pattern in bigram_patterns:
                    matches = re.findall(pattern, text_lower, re.IGNORECASE)
                    for match in matches:
                        keyword_freq[match] += 5

                # Extract single technical terms (medium weight)
                words = re.findall(r"\b[a-z]{4,}\b", text_lower)
                for word in words:
                    if word in technical_terms:
                        keyword_freq[word] += 2

            # Remove duplicates (singular/plural, hyphen variations)
            normalized_freq: Counter = Counter()
            seen_roots = set()

            for keyword, count in keyword_freq.most_common(100):
                # Normalize: remove hyphens, get root form
                normalized = keyword.replace("-", " ").strip()
                root = normalized.rstrip("s").rstrip("ing").rstrip("ed")

                # Skip if we've seen a similar root
                if root in seen_roots:
                    continue

                seen_roots.add(root)
                normalized_freq[normalized] = count

            # Get top 80 keywords with significant frequency differences
            top_keywords = [
                {"keyword": kw, "count": count}
                for kw, count in normalized_freq.most_common(80)
                if count >= 2  # Only include keywords that appear at least twice
            ]

            # Cache for 6 hours
            cache_data = {
                "keywords": top_keywords,
                "total_papers_with_keywords": papers_processed,
                "updated_at": None,
            }

            await cache.set("trending_keywords", cache_data, ttl=21600)

            log.info(
                "refresh_keywords_complete",
                keywords_count=len(top_keywords),
                papers_processed=papers_processed,
            )

            return {
                "keywords": top_keywords,
                "papers_processed": papers_processed,
            }

        except Exception as e:
            log.error("refresh_keywords_error", error=str(e)[:200])
            raise

    try:
        return _run_async(_refresh())
    except Exception as exc:
        log.error("refresh_keywords_failed", error=str(exc))
        try:
            raise self.retry(exc=exc, countdown=300)
        except MaxRetriesExceededError:
            log.error("refresh_keywords_max_retries_exceeded")
            raise
