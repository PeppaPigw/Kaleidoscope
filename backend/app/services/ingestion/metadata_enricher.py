"""Metadata enrichment — cascade through APIs to fill missing metadata."""

from datetime import date, datetime, timezone

import httpx
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.crossref import CrossRefClient
from app.clients.openalex import OpenAlexClient
from app.clients.semantic_scholar import SemanticScholarClient
from app.models.paper import Paper
from app.utils.doi import normalize_doi, normalize_arxiv_id

logger = structlog.get_logger(__name__)

# PubMed E-utilities base URL (free, no key required for <3 req/s)
PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


class MetadataEnricherService:
    """
    Enrich paper metadata via cascading API queries.

    Supports multiple entry points:
    - DOI paper: CrossRef → OpenAlex → Semantic Scholar
    - arXiv paper: Semantic Scholar → OpenAlex (via arXiv ID)
    - PMID paper: PubMed → CrossRef (if DOI found) → S2
    - Title-only paper: CrossRef search → resolve DOI → full cascade

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

        Routes to the appropriate enrichment path based on available identifiers.
        """
        log = logger.bind(paper_id=str(paper.id), doi=paper.doi,
                          arxiv_id=paper.arxiv_id, pmid=paper.pmid)

        # ── PMID path: resolve via PubMed first ─────────────────
        if paper.pmid and not paper.doi:
            try:
                doi = await self._resolve_pmid_to_doi(paper.pmid)
                if doi:
                    paper.doi = doi
                    log.info("pmid_resolved_to_doi", doi=doi)
                else:
                    # Still try to get metadata from PubMed directly
                    await self._enrich_from_pubmed(paper)
            except Exception as e:
                log.warning("pmid_resolution_failed", error=str(e))

        # ── Title-only path: search CrossRef for DOI ─────────────
        if not paper.doi and not paper.arxiv_id and paper.title:
            try:
                resolved_doi = await self._resolve_title_to_doi(paper.title)
                if resolved_doi:
                    paper.doi = resolved_doi
                    log.info("title_resolved_to_doi", doi=resolved_doi)
            except Exception as e:
                log.warning("title_resolution_failed", error=str(e))

        # ── Standard enrichment cascade ──────────────────────────

        # --- CrossRef (requires DOI) ---
        if paper.doi:
            try:
                cr_data = await self.crossref.get_work(paper.doi)
                if cr_data:
                    self._apply_crossref(paper, cr_data)
                    log.info("enriched_from_crossref")
            except Exception as e:
                log.warning("crossref_enrichment_failed", error=str(e))

        # --- OpenAlex (DOI or arXiv) ---
        if paper.doi:
            try:
                oa_data = await self.openalex.get_work_by_doi(paper.doi)
                if oa_data:
                    self._apply_openalex(paper, oa_data)
                    log.info("enriched_from_openalex")
            except Exception as e:
                log.warning("openalex_enrichment_failed", error=str(e))

        # --- Semantic Scholar (DOI, arXiv, PMID, or title) ---
        s2_query = self._build_s2_query(paper)
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

    # ─── Identifier resolution ───────────────────────────────────

    async def _resolve_pmid_to_doi(self, pmid: str) -> str | None:
        """
        Resolve a PubMed ID to DOI using NCBI E-utilities.

        Uses efetch with rettype=xml to get the <ArticleId IdType="doi"> element.
        Free API: 3 requests/second without API key, 10/s with key.
        """
        url = f"{PUBMED_EFETCH_URL}/efetch.fcgi"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params={
                "db": "pubmed",
                "id": pmid,
                "rettype": "xml",
                "retmode": "xml",
            })
            if resp.status_code != 200:
                return None

            # Extract DOI from XML response
            import re
            doi_match = re.search(
                r'<ArticleId\s+IdType="doi">([^<]+)</ArticleId>',
                resp.text
            )
            if doi_match:
                return normalize_doi(doi_match.group(1))

        return None

    async def _enrich_from_pubmed(self, paper: Paper) -> None:
        """
        Fetch basic metadata directly from PubMed when no DOI can be resolved.

        Populates title, abstract, published_at from PubMed XML.
        """
        url = f"{PUBMED_EFETCH_URL}/efetch.fcgi"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params={
                    "db": "pubmed",
                    "id": paper.pmid,
                    "rettype": "xml",
                    "retmode": "xml",
                })
                if resp.status_code != 200:
                    return

                import re

                # Title
                if not paper.title or paper.title == paper.pmid:
                    title_match = re.search(
                        r'<ArticleTitle>(.+?)</ArticleTitle>',
                        resp.text, re.DOTALL
                    )
                    if title_match:
                        paper.title = title_match.group(1).strip()

                # Abstract
                if not paper.abstract:
                    abs_match = re.search(
                        r'<AbstractText[^>]*>(.+?)</AbstractText>',
                        resp.text, re.DOTALL
                    )
                    if abs_match:
                        paper.abstract = abs_match.group(1).strip()

                # Published date
                if not paper.published_at:
                    year_match = re.search(r'<PubDate>.*?<Year>(\d{4})</Year>', resp.text, re.DOTALL)
                    month_match = re.search(r'<PubDate>.*?<Month>(\d{1,2})</Month>', resp.text, re.DOTALL)
                    if year_match:
                        try:
                            paper.published_at = date(
                                int(year_match.group(1)),
                                int(month_match.group(1)) if month_match else 1,
                                1,
                            )
                        except ValueError:
                            pass

                logger.info("enriched_from_pubmed", pmid=paper.pmid)

        except Exception as e:
            logger.warning("pubmed_enrichment_failed", pmid=paper.pmid, error=str(e))

    async def _resolve_title_to_doi(self, title: str) -> str | None:
        """
        Search CrossRef by title to find the most likely DOI.

        Uses CrossRef's /works?query= endpoint. Only returns a DOI if the
        top result's title is a close match (>85% similarity).
        """
        from app.utils.text import titles_are_similar

        results = await self.crossref.search_works(title, rows=3)
        if not results:
            return None

        for result in results:
            result_titles = result.get("title", [])
            if not result_titles:
                continue
            result_title = result_titles[0]
            if titles_are_similar(title, result_title, threshold=0.85):
                doi = result.get("DOI")
                if doi:
                    return normalize_doi(doi)

        return None

    # ─── S2 query builder ────────────────────────────────────────

    @staticmethod
    def _build_s2_query(paper: Paper) -> str | None:
        """
        Build the Semantic Scholar query for a paper.

        Priority: DOI → arXiv → PMID → None
        Always normalizes arXiv IDs to prevent arXiv:arXiv:... duplication.
        """
        if paper.doi:
            return f"DOI:{paper.doi}"
        if paper.arxiv_id:
            clean_id = normalize_arxiv_id(paper.arxiv_id)
            return f"arXiv:{clean_id}"
        if paper.pmid:
            return f"PMID:{paper.pmid}"
        return None

    # ─── Metadata applicators ────────────────────────────────────

    def _apply_crossref(self, paper: Paper, data: dict) -> None:
        """Apply CrossRef metadata to paper (only fills empty fields)."""
        # Overwrite title if empty or if it looks like a raw identifier
        _is_identifier = (
            not paper.title
            or paper.title == ""
            or paper.title.startswith("10.")  # DOI prefix
            or paper.title.startswith("arXiv:")
            or paper.title.startswith("arxiv:")
        )
        if _is_identifier:
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
                paper.arxiv_id = normalize_arxiv_id(ext_ids["ArXiv"])

        # Backfill DOI if discovered via S2
        if not paper.doi:
            ext_ids = data.get("externalIds", {})
            if ext_ids.get("DOI"):
                paper.doi = normalize_doi(ext_ids["DOI"])

        # Backfill PMID if discovered via S2
        if not paper.pmid:
            ext_ids = data.get("externalIds", {})
            if ext_ids.get("PubMed"):
                paper.pmid = ext_ids["PubMed"]

        paper.citation_count_updated_at = datetime.now(timezone.utc)
