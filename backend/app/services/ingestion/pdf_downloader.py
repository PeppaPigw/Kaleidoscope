"""PDF acquisition service — download full-text PDFs using priority cascade."""

import hashlib

import httpx
import structlog

from app.clients.arxiv import ArxivClient
from app.clients.unpaywall import UnpaywallClient
from app.clients.semantic_scholar import SemanticScholarClient
from app.config import settings
from app.exceptions import PDFAcquisitionError
from app.models.paper import Paper
from app.utils.rate_limiter import PUBLISHER_LIMITER

logger = structlog.get_logger(__name__)


class AcquisitionResult:
    """Result of a PDF acquisition attempt."""

    def __init__(
        self,
        success: bool,
        pdf_path: str | None = None,
        source: str | None = None,
        url: str | None = None,
        error: str | None = None,
    ):
        self.success = success
        self.pdf_path = pdf_path
        self.source = source
        self.url = url
        self.error = error


class PDFDownloaderService:
    """
    Download PDFs using the priority cascade from source.md:

    1. arXiv / preprint servers → direct PDF URL
    2. OA journals → construct PDF URL from DOI/link
    3. Unpaywall → best OA PDF location
    4. Semantic Scholar → openAccessPdf
    5. Publisher TDM APIs (Elsevier, Wiley, Springer)
    6. Mark as metadata-only
    """

    # OA journal PDF URL patterns
    OA_PDF_PATTERNS = {
        "aps.org": lambda doi: f"https://journals.aps.org/{doi.split('/')[0].split('.')[-1].lower()}/pdf/{doi}",
        "nature.com": lambda doi: f"https://www.nature.com/articles/{doi.rsplit('/', 1)[-1]}.pdf",
        "science.org": lambda doi: f"https://www.science.org/doi/pdf/{doi}",
        "iopscience.iop.org": lambda doi: f"https://iopscience.iop.org/article/{doi}/pdf",
    }

    def __init__(
        self,
        arxiv_client: ArxivClient,
        unpaywall_client: UnpaywallClient,
        s2_client: SemanticScholarClient,
    ):
        self.arxiv = arxiv_client
        self.unpaywall = unpaywall_client
        self.s2 = s2_client

    async def acquire_pdf(self, paper: Paper) -> AcquisitionResult:
        """
        Attempt to acquire PDF through priority cascade.

        Returns AcquisitionResult with success status and file path/URL.
        """
        log = logger.bind(paper_id=str(paper.id), doi=paper.doi, arxiv_id=paper.arxiv_id)
        attempted_sources: list[str] = []

        # 1. arXiv direct download
        if paper.arxiv_id:
            attempted_sources.append("arxiv")
            try:
                url = ArxivClient.construct_pdf_url(paper.arxiv_id)
                result = await self._download_pdf(url, paper, "arxiv")
                if result.success:
                    log.info("pdf_acquired", source="arxiv")
                    return result
            except Exception as e:
                log.warning("arxiv_pdf_failed", error=str(e))

        # 2. Known OA journal patterns
        if paper.doi:
            for domain, url_fn in self.OA_PDF_PATTERNS.items():
                if paper.remote_urls and any(domain in (u.get("url", "") or "") for u in paper.remote_urls):
                    attempted_sources.append(f"oa_{domain}")
                    try:
                        url = url_fn(paper.doi)
                        result = await self._download_pdf(url, paper, f"oa_{domain}")
                        if result.success:
                            log.info("pdf_acquired", source=f"oa_{domain}")
                            return result
                    except Exception as e:
                        log.warning("oa_pdf_failed", domain=domain, error=str(e))

        # 3. Unpaywall
        if paper.doi:
            attempted_sources.append("unpaywall")
            try:
                pdf_url = await self.unpaywall.get_pdf_url(paper.doi)
                if pdf_url:
                    result = await self._download_pdf(pdf_url, paper, "unpaywall")
                    if result.success:
                        log.info("pdf_acquired", source="unpaywall")
                        return result
            except Exception as e:
                log.warning("unpaywall_pdf_failed", error=str(e))

        # 4. Semantic Scholar openAccessPdf
        s2_id = paper.semantic_scholar_id or (f"DOI:{paper.doi}" if paper.doi else None)
        if s2_id:
            attempted_sources.append("semantic_scholar")
            try:
                s2_data = await self.s2.get_paper(s2_id)
                oa_pdf = s2_data.get("openAccessPdf", {})
                if oa_pdf and oa_pdf.get("url"):
                    result = await self._download_pdf(oa_pdf["url"], paper, "semantic_scholar")
                    if result.success:
                        log.info("pdf_acquired", source="semantic_scholar")
                        return result
            except Exception as e:
                log.warning("s2_pdf_failed", error=str(e))

        # 5. TDM APIs (if keys configured)
        if paper.doi and settings.elsevier_tdm_api_key:
            attempted_sources.append("elsevier_tdm")
            try:
                result = await self._try_elsevier_tdm(paper)
                if result.success:
                    log.info("pdf_acquired", source="elsevier_tdm")
                    return result
            except Exception as e:
                log.warning("elsevier_tdm_failed", error=str(e))

        # 6. Mark as metadata-only
        log.info("pdf_not_available", attempted=attempted_sources)
        return AcquisitionResult(
            success=False,
            source=None,
            error=f"No PDF available. Attempted: {', '.join(attempted_sources)}",
        )

    async def _download_pdf(
        self, url: str, paper: Paper, source: str
    ) -> AcquisitionResult:
        """Download a PDF from URL and return the MinIO path."""
        async with PUBLISHER_LIMITER:
            async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
                resp = await client.get(url)

                if resp.status_code != 200:
                    return AcquisitionResult(
                        success=False,
                        source=source,
                        url=url,
                        error=f"HTTP {resp.status_code}",
                    )

                content_type = resp.headers.get("content-type", "")
                if "pdf" not in content_type and not url.endswith(".pdf"):
                    # Not a PDF response — might be a login page or HTML
                    return AcquisitionResult(
                        success=False,
                        source=source,
                        url=url,
                        error=f"Not a PDF. Content-Type: {content_type}",
                    )

                # Compute storage path
                doi_hash = hashlib.sha256((paper.doi or paper.title).encode()).hexdigest()[:16]
                object_key = f"papers/{doi_hash}/{source}.pdf"

                # NOTE: In production, upload to MinIO here
                # For now, return the URL as the path (to be replaced with MinIO upload)
                return AcquisitionResult(
                    success=True,
                    pdf_path=object_key,
                    source=source,
                    url=url,
                )

    async def _try_elsevier_tdm(self, paper: Paper) -> AcquisitionResult:
        """Try Elsevier TDM API for full-text XML."""
        url = f"https://api.elsevier.com/content/article/doi/{paper.doi}"
        async with PUBLISHER_LIMITER:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    url,
                    headers={
                        "X-ELS-APIKey": settings.elsevier_tdm_api_key,
                        "Accept": "application/pdf",
                    },
                )
                if resp.status_code == 200:
                    doi_hash = hashlib.sha256(paper.doi.encode()).hexdigest()[:16]
                    object_key = f"papers/{doi_hash}/elsevier.pdf"
                    return AcquisitionResult(
                        success=True,
                        pdf_path=object_key,
                        source="elsevier_tdm",
                        url=url,
                    )
                return AcquisitionResult(
                    success=False,
                    source="elsevier_tdm",
                    error=f"HTTP {resp.status_code}",
                )
