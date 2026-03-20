"""Metadata enrichment — cascade through APIs to fill missing metadata."""

from datetime import date, datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.crossref import CrossRefClient
from app.clients.openalex import OpenAlexClient
from app.clients.semantic_scholar import SemanticScholarClient
from app.models.paper import Paper

logger = structlog.get_logger(__name__)


class MetadataEnricherService:
    """
    Enrich paper metadata via cascading API queries.

    Order: CrossRef → OpenAlex → Semantic Scholar
    Each source fills in missing fields without overwriting existing data.
    """

    def __init__(
        self,
        db: AsyncSession,
        crossref: CrossRefClient,
        openalex: OpenAlexClient,
        semantic_scholar: SemanticScholarClient,
    ):
        self.db = db
        self.crossref = crossref
        self.openalex = openalex
        self.s2 = semantic_scholar

    async def enrich(self, paper: Paper) -> Paper:
        """
        Enrich a paper with metadata from external APIs.

        Attempts each source in order. Only fills fields that are currently empty.
        """
        log = logger.bind(paper_id=str(paper.id), doi=paper.doi)

        # --- CrossRef ---
        if paper.doi:
            try:
                cr_data = await self.crossref.get_work(paper.doi)
                if cr_data:
                    self._apply_crossref(paper, cr_data)
                    log.info("enriched_from_crossref")
            except Exception as e:
                log.warning("crossref_enrichment_failed", error=str(e))

        # --- OpenAlex ---
        if paper.doi:
            try:
                oa_data = await self.openalex.get_work_by_doi(paper.doi)
                if oa_data:
                    self._apply_openalex(paper, oa_data)
                    log.info("enriched_from_openalex")
            except Exception as e:
                log.warning("openalex_enrichment_failed", error=str(e))

        # --- Semantic Scholar ---
        s2_query = f"DOI:{paper.doi}" if paper.doi else (f"arXiv:{paper.arxiv_id}" if paper.arxiv_id else None)
        if s2_query:
            try:
                s2_data = await self.s2.get_paper(s2_query)
                if s2_data:
                    self._apply_semantic_scholar(paper, s2_data)
                    log.info("enriched_from_semantic_scholar")
            except Exception as e:
                log.warning("s2_enrichment_failed", error=str(e))

        paper.ingestion_status = "enriched"
        return paper

    def _apply_crossref(self, paper: Paper, data: dict) -> None:
        """Apply CrossRef metadata to paper (only fills empty fields)."""
        if not paper.title or paper.title == "":
            titles = data.get("title", [])
            if titles:
                paper.title = titles[0]

        if not paper.abstract:
            paper.abstract = data.get("abstract")

        if not paper.published_at:
            date_parts = data.get("published", {}).get("date-parts", [[]])
            if date_parts and date_parts[0]:
                parts = date_parts[0]
                try:
                    paper.published_at = date(
                        parts[0],
                        parts[1] if len(parts) > 1 else 1,
                        parts[2] if len(parts) > 2 else 1,
                    )
                except (ValueError, IndexError):
                    pass

        if not paper.paper_type:
            paper.paper_type = data.get("type")

        if not paper.citation_count:
            paper.citation_count = data.get("is-referenced-by-count", 0)

        # Container title → venue name
        container = data.get("container-title", [])
        if container and not paper.venue_id:
            # Store for later venue linking
            if paper.raw_metadata is None:
                paper.raw_metadata = {}
            paper.raw_metadata["crossref_venue"] = container[0]

        # License
        licenses = data.get("license", [])
        if licenses and not paper.license:
            paper.license = licenses[0].get("URL", "")

        # Raw metadata
        if paper.raw_metadata is None:
            paper.raw_metadata = {}
        paper.raw_metadata["crossref"] = data

    def _apply_openalex(self, paper: Paper, data: dict) -> None:
        """Apply OpenAlex metadata to paper."""
        if not paper.openalex_id:
            paper.openalex_id = data.get("id", "").replace("https://openalex.org/", "")

        if not paper.abstract and data.get("abstract_inverted_index"):
            # Reconstruct abstract from inverted index
            inverted = data["abstract_inverted_index"]
            word_positions: list[tuple[int, str]] = []
            for word, positions in inverted.items():
                for pos in positions:
                    word_positions.append((pos, word))
            word_positions.sort()
            paper.abstract = " ".join(w for _, w in word_positions)

        if not paper.oa_status:
            oa = data.get("open_access", {})
            paper.oa_status = oa.get("oa_status")

        if not paper.citation_count:
            paper.citation_count = data.get("cited_by_count", 0)

        if not paper.published_at and data.get("publication_date"):
            try:
                paper.published_at = date.fromisoformat(data["publication_date"])
            except ValueError:
                pass

        if not paper.paper_type:
            paper.paper_type = data.get("type")

        # Keywords from concepts
        if not paper.keywords:
            concepts = data.get("concepts", [])
            if concepts:
                paper.keywords = [
                    c["display_name"]
                    for c in sorted(concepts, key=lambda x: x.get("score", 0), reverse=True)[:10]
                ]

        if paper.raw_metadata is None:
            paper.raw_metadata = {}
        paper.raw_metadata["openalex"] = {
            "id": data.get("id"),
            "type": data.get("type"),
            "cited_by_count": data.get("cited_by_count"),
        }

    def _apply_semantic_scholar(self, paper: Paper, data: dict) -> None:
        """Apply Semantic Scholar metadata to paper."""
        if not paper.semantic_scholar_id:
            paper.semantic_scholar_id = data.get("paperId")

        if not paper.abstract:
            paper.abstract = data.get("abstract")

        if not paper.citation_count:
            paper.citation_count = data.get("citationCount", 0)

        if not paper.influential_citation_count:
            paper.influential_citation_count = data.get("influentialCitationCount")

        # Check for open access PDF
        oa_pdf = data.get("openAccessPdf", {})
        if oa_pdf and not paper.remote_urls:
            paper.remote_urls = [
                {"url": oa_pdf.get("url"), "source": "semantic_scholar", "type": "pdf"}
            ]

        if not paper.arxiv_id:
            ext_ids = data.get("externalIds", {})
            if ext_ids.get("ArXiv"):
                paper.arxiv_id = ext_ids["ArXiv"]

        paper.citation_count_updated_at = datetime.now(timezone.utc)
