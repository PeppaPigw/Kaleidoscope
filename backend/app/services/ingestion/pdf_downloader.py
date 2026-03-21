"""PDF & full-text acquisition service — download using priority cascade.

Supports four output formats:
  - PDF binary (for GROBID parsing)
  - Full-text XML (Elsevier/Wiley/Springer TDM — structured, no OCR needed)
  - LaTeX source (arXiv — highest quality, no parsing needed)
  - Metadata-only (fallback)

Content is persisted to MinIO (or local /tmp fallback in development).
"""

import hashlib
import json
from pathlib import Path

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

# Local fallback storage for development (when MinIO is not wired up)
_LOCAL_STORAGE_DIR = Path("/tmp/kaleidoscope-papers")
_LOCAL_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


class AcquisitionResult:
    """Result of a full-text acquisition attempt."""

    def __init__(
        self,
        success: bool,
        content_type: str = "none",  # "pdf", "xml", "tex", "none"
        storage_path: str | None = None,
        source: str | None = None,
        url: str | None = None,
        error: str | None = None,
        content_bytes: bytes | None = None,  # Actual content for downstream use
    ):
        self.success = success
        self.content_type = content_type
        self.storage_path = storage_path
        self.source = source
        self.url = url
        self.error = error
        self.content_bytes = content_bytes

    # Keep backward compat
    @property
    def pdf_path(self) -> str | None:
        return self.storage_path


class PDFDownloaderService:
    """
    Acquire full-text using the priority cascade from source.md:

    1. arXiv / preprint servers → direct PDF URL
    2. OA journals → construct PDF URL from DOI/link
    3. Unpaywall → best OA PDF location
    4. Semantic Scholar → openAccessPdf
    5. Publisher TDM APIs:
       a. Elsevier TDM → full-text XML (via X-ELS-APIKey)
       b. Wiley TDM → full-text PDF (via Wiley-TDM-Client-Token)
       c. Springer Nature → full-text XML (via api_key)
    6. Mark as metadata-only
    """

    # OA journal PDF URL patterns
    OA_PDF_PATTERNS = {
        "aps.org": lambda doi: f"https://journals.aps.org/{doi.split('/')[0].split('.')[-1].lower()}/pdf/{doi}",
        "nature.com": lambda doi: f"https://www.nature.com/articles/{doi.rsplit('/', 1)[-1]}.pdf",
        "science.org": lambda doi: f"https://www.science.org/doi/pdf/{doi}",
        "iopscience.iop.org": lambda doi: f"https://iopscience.iop.org/article/{doi}/pdf",
        "pnas.org": lambda doi: f"https://www.pnas.org/doi/pdf/{doi}",
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
        Attempt to acquire full-text through priority cascade.

        Returns AcquisitionResult with success status, content type, and storage path.
        """
        log = logger.bind(paper_id=str(paper.id), doi=paper.doi, arxiv_id=paper.arxiv_id)
        attempted_sources: list[str] = []

        # 1. arXiv — try LaTeX source first (best quality), then PDF
        if paper.arxiv_id:
            attempted_sources.append("arxiv")
            try:
                # 1a. LaTeX source — highest quality full-text (~97% available)
                # No GROBID needed, preserves math formulas, section structure
                latex_data = await self.arxiv.get_latex_source(paper.arxiv_id)
                if latex_data and latex_data.get("main_tex"):
                    doi_hash = hashlib.sha256(
                        (paper.doi or paper.arxiv_id).encode()
                    ).hexdigest()[:16]
                    object_key = f"papers/{doi_hash}/arxiv_source.tex"
                    tex_bytes = latex_data["main_tex"].encode("utf-8")
                    self._persist_content(object_key, tex_bytes)
                    # Also persist all files as JSON sidecar for full context
                    if latex_data.get("all_files"):
                        sidecar_key = f"papers/{doi_hash}/arxiv_all_files.json"
                        self._persist_content(
                            sidecar_key,
                            json.dumps(latex_data["all_files"], ensure_ascii=False).encode("utf-8"),
                        )
                    log.info("fulltext_acquired", source="arxiv_latex", type="tex",
                             files=len(latex_data.get("all_files", {})))
                    return AcquisitionResult(
                        success=True,
                        content_type="tex",
                        storage_path=object_key,
                        source="arxiv_latex",
                        url=ArxivClient.construct_source_url(paper.arxiv_id),
                        content_bytes=tex_bytes,
                    )
            except Exception as e:
                log.warning("arxiv_latex_failed", error=str(e))

            try:
                # 1b. PDF fallback (for the ~3% without TeX source)
                url = ArxivClient.construct_pdf_url(paper.arxiv_id)
                result = await self._download_pdf(url, paper, "arxiv")
                if result.success:
                    log.info("fulltext_acquired", source="arxiv", type="pdf")
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
                            log.info("fulltext_acquired", source=f"oa_{domain}", type="pdf")
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
                        log.info("fulltext_acquired", source="unpaywall", type="pdf")
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
                        log.info("fulltext_acquired", source="semantic_scholar", type="pdf")
                        return result
            except Exception as e:
                log.warning("s2_pdf_failed", error=str(e))

        # ─── 5. Publisher TDM APIs (full-text access with API keys) ───

        # 5a. Elsevier TDM — returns full-text XML or PDF
        if paper.doi and settings.elsevier_tdm_api_key:
            attempted_sources.append("elsevier_tdm")
            try:
                result = await self._try_elsevier_tdm(paper)
                if result.success:
                    log.info("fulltext_acquired", source="elsevier_tdm", type=result.content_type)
                    return result
            except Exception as e:
                log.warning("elsevier_tdm_failed", error=str(e))

        # 5b. Wiley TDM — returns PDF via token auth
        if paper.doi and settings.wiley_token:
            attempted_sources.append("wiley_tdm")
            try:
                result = await self._try_wiley_tdm(paper)
                if result.success:
                    log.info("fulltext_acquired", source="wiley_tdm", type=result.content_type)
                    return result
            except Exception as e:
                log.warning("wiley_tdm_failed", error=str(e))

        # 5c. Springer Nature — returns full-text XML via api_key
        if paper.doi and settings.springer_api_key:
            attempted_sources.append("springer_tdm")
            try:
                result = await self._try_springer_tdm(paper)
                if result.success:
                    log.info("fulltext_acquired", source="springer_tdm", type=result.content_type)
                    return result
            except Exception as e:
                log.warning("springer_tdm_failed", error=str(e))

        # 6. Mark as metadata-only
        log.info("fulltext_not_available", attempted=attempted_sources)
        return AcquisitionResult(
            success=False,
            source=None,
            error=f"No full-text available. Attempted: {', '.join(attempted_sources)}",
        )

    # ─── Private: content persistence ─────────────────────────────────

    @staticmethod
    def _persist_content(object_key: str, content: bytes) -> str:
        """
        Persist content to storage and return the verified path.

        Currently writes to local filesystem as MinIO integration is pending.
        TODO: Replace with MinIO upload when ready.
        """
        local_path = _LOCAL_STORAGE_DIR / object_key
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(content)
        logger.debug("content_persisted", path=str(local_path), size=len(content))
        return object_key

    @staticmethod
    def load_content(object_key: str) -> bytes | None:
        """
        Load previously persisted content by storage key.

        Returns None if the file does not exist.
        """
        local_path = _LOCAL_STORAGE_DIR / object_key
        if local_path.exists():
            return local_path.read_bytes()
        return None

    # ─── Private: PDF download ───────────────────────────────────────

    async def _download_pdf(
        self, url: str, paper: Paper, source: str
    ) -> AcquisitionResult:
        """Download a PDF from URL, persist it, and return the storage path."""
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
                    return AcquisitionResult(
                        success=False,
                        source=source,
                        url=url,
                        error=f"Not a PDF. Content-Type: {content_type}",
                    )

                # Persist the PDF
                doi_hash = hashlib.sha256((paper.doi or paper.title).encode()).hexdigest()[:16]
                object_key = f"papers/{doi_hash}/{source}.pdf"
                self._persist_content(object_key, resp.content)

                return AcquisitionResult(
                    success=True,
                    content_type="pdf",
                    storage_path=object_key,
                    source=source,
                    url=url,
                    content_bytes=resp.content,
                )

    # ─── Private: Elsevier TDM ───────────────────────────────────────

    async def _try_elsevier_tdm(self, paper: Paper) -> AcquisitionResult:
        """
        Elsevier TDM API — try full-text XML first (better for extraction),
        then fall back to PDF.

        Docs: https://dev.elsevier.com/documentation/FullTextRetrievalAPI.wadl
        Auth: X-ELS-APIKey header
        """
        doi_hash = hashlib.sha256(paper.doi.encode()).hexdigest()[:16]
        base_url = f"https://api.elsevier.com/content/article/doi/{paper.doi}"

        async with PUBLISHER_LIMITER:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Try 1: Full-text XML (structured, ideal for NLP)
                resp = await client.get(
                    base_url,
                    headers={
                        "X-ELS-APIKey": settings.elsevier_tdm_api_key,
                        "Accept": "text/xml",
                    },
                )
                if resp.status_code == 200 and "xml" in resp.headers.get("content-type", ""):
                    object_key = f"papers/{doi_hash}/elsevier_fulltext.xml"
                    self._persist_content(object_key, resp.content)
                    return AcquisitionResult(
                        success=True,
                        content_type="xml",
                        storage_path=object_key,
                        source="elsevier_tdm",
                        url=base_url,
                        content_bytes=resp.content,
                    )

                # Try 2: PDF
                resp = await client.get(
                    base_url,
                    headers={
                        "X-ELS-APIKey": settings.elsevier_tdm_api_key,
                        "Accept": "application/pdf",
                    },
                )
                if resp.status_code == 200:
                    object_key = f"papers/{doi_hash}/elsevier.pdf"
                    self._persist_content(object_key, resp.content)
                    return AcquisitionResult(
                        success=True,
                        content_type="pdf",
                        storage_path=object_key,
                        source="elsevier_tdm",
                        url=base_url,
                        content_bytes=resp.content,
                    )

                return AcquisitionResult(
                    success=False,
                    source="elsevier_tdm",
                    error=f"HTTP {resp.status_code}",
                )

    # ─── Private: Wiley TDM ──────────────────────────────────────────

    async def _try_wiley_tdm(self, paper: Paper) -> AcquisitionResult:
        """
        Wiley TDM API — download PDF with token authentication.

        Docs: https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining
        Auth: Wiley-TDM-Client-Token header
        URL:  https://api.wiley.com/onlinelibrary/tdm/v1/articles/{DOI}
        """
        doi_hash = hashlib.sha256(paper.doi.encode()).hexdigest()[:16]
        url = f"https://api.wiley.com/onlinelibrary/tdm/v1/articles/{paper.doi}"

        async with PUBLISHER_LIMITER:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    url,
                    headers={
                        "Wiley-TDM-Client-Token": settings.wiley_token,
                        "Accept": "application/pdf",
                    },
                )
                if resp.status_code == 200:
                    content_type = resp.headers.get("content-type", "")
                    if "pdf" in content_type:
                        object_key = f"papers/{doi_hash}/wiley.pdf"
                        self._persist_content(object_key, resp.content)
                        return AcquisitionResult(
                            success=True,
                            content_type="pdf",
                            storage_path=object_key,
                            source="wiley_tdm",
                            url=url,
                            content_bytes=resp.content,
                        )

                return AcquisitionResult(
                    success=False,
                    source="wiley_tdm",
                    error=f"HTTP {resp.status_code}",
                )

    # ─── Private: Springer Nature ────────────────────────────────────

    async def _try_springer_tdm(self, paper: Paper) -> AcquisitionResult:
        """
        Springer Nature OA API — retrieve full-text XML via DOI.

        Docs: https://dev.springernature.com/docs
        Auth: api_key query parameter
        Free tier: 5,000 requests/day
        """
        doi_hash = hashlib.sha256(paper.doi.encode()).hexdigest()[:16]
        url = f"https://api.springernature.com/openaccess/jats/doi/{paper.doi}"

        async with PUBLISHER_LIMITER:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    url,
                    params={"api_key": settings.springer_api_key},
                    headers={"Accept": "application/xml"},
                )
                if resp.status_code == 200 and len(resp.content) > 200:
                    object_key = f"papers/{doi_hash}/springer_fulltext.xml"
                    self._persist_content(object_key, resp.content)
                    return AcquisitionResult(
                        success=True,
                        content_type="xml",
                        storage_path=object_key,
                        source="springer_tdm",
                        url=url,
                        content_bytes=resp.content,
                    )

                return AcquisitionResult(
                    success=False,
                    source="springer_tdm",
                    error=f"HTTP {resp.status_code}",
                )
