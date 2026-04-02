"""arXiv API client — preprint metadata, PDF, LaTeX source, and HTML retrieval."""

import re
import tarfile
import io

import structlog
import httpx

from app.exceptions import ExternalAPIError, RateLimitError
from app.utils.rate_limiter import ARXIV_LIMITER

logger = structlog.get_logger(__name__)

ARXIV_API_URL = "http://export.arxiv.org/api/query"


class ArxivClient:
    """
    arXiv API client.

    - Free, rate limit: 1 request per 3 seconds
    - Returns Atom XML feed for metadata
    - Full-text available in 3 formats:
        1. PDF: https://arxiv.org/pdf/{id}.pdf
        2. LaTeX source: https://arxiv.org/e-print/{id} (.tar.gz)
        3. HTML5: https://ar5iv.labs.arxiv.org/html/{id}
    """

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def get_paper(self, arxiv_id: str) -> dict:
        """
        Fetch metadata for an arXiv paper.

        Returns structured dict with title, abstract, authors, categories, etc.
        """
        client = await self._get_client()
        async with ARXIV_LIMITER:
            try:
                resp = await client.get(
                    ARXIV_API_URL,
                    params={"id_list": arxiv_id, "max_results": 1},
                )
                resp.raise_for_status()
                return self._parse_atom_entry(resp.text)
            except httpx.HTTPStatusError as e:
                logger.error(
                    "arxiv_api_error", arxiv_id=arxiv_id, status=e.response.status_code
                )
                raise ExternalAPIError("arxiv", e.response.status_code, str(e))

    # ─── Full-text retrieval ─────────────────────────────────────────

    async def get_latex_source(self, arxiv_id: str) -> dict | None:
        """
        Download and extract LaTeX source from arXiv e-print endpoint.

        Returns:
            dict with keys:
            - "main_tex": str — content of the main .tex file
            - "all_files": dict[str, str] — all text files in the archive
            - "arxiv_id": str
            Or None if source is not available / not a TeX submission.

        This is the HIGHEST QUALITY full-text source for arXiv papers:
        - Original author text with no OCR errors
        - Complete LaTeX math formulas
        - Full bibliography in BibTeX format
        - ~97% of arXiv papers provide TeX source
        """
        clean_id = arxiv_id.replace("arXiv:", "").strip()
        url = f"https://arxiv.org/e-print/{clean_id}"

        client = await self._get_client()
        async with ARXIV_LIMITER:
            try:
                resp = await client.get(url, follow_redirects=True)
                if resp.status_code != 200:
                    logger.warning(
                        "arxiv_source_unavailable",
                        arxiv_id=clean_id,
                        status=resp.status_code,
                    )
                    return None

                content_type = resp.headers.get("content-type", "")

                # Case 1: tar.gz archive (most common — multi-file submission)
                if "gzip" in content_type or "tar" in content_type:
                    return self._extract_tex_from_tar(resp.content, clean_id)

                # Case 2: Single .tex file (gzipped)
                if "x-tex" in content_type or "latex" in content_type:
                    import gzip

                    try:
                        tex_content = gzip.decompress(resp.content).decode(
                            "utf-8", errors="replace"
                        )
                    except Exception:
                        tex_content = resp.content.decode("utf-8", errors="replace")
                    return {
                        "arxiv_id": clean_id,
                        "main_tex": tex_content,
                        "all_files": {"main.tex": tex_content},
                    }

                # Case 3: PDF-only submission (no TeX source available)
                if "pdf" in content_type:
                    logger.info("arxiv_pdf_only_submission", arxiv_id=clean_id)
                    return None

                logger.warning(
                    "arxiv_source_unknown_type",
                    arxiv_id=clean_id,
                    content_type=content_type,
                )
                return None

            except Exception as e:
                logger.warning("arxiv_source_failed", arxiv_id=clean_id, error=str(e))
                return None

    async def get_html_fulltext(self, arxiv_id: str) -> str | None:
        """
        Fetch HTML5 full-text from ar5iv (LaTeXML-converted HTML).

        ar5iv.labs.arxiv.org provides HTML5 versions of arXiv papers,
        converted by LaTeXML. Good for text extraction without GROBID.

        Returns HTML string or None if not available.
        """
        clean_id = arxiv_id.replace("arXiv:", "").strip()
        url = f"https://ar5iv.labs.arxiv.org/html/{clean_id}"

        client = await self._get_client()
        async with ARXIV_LIMITER:
            try:
                resp = await client.get(url, follow_redirects=True)
                if resp.status_code == 200 and "html" in resp.headers.get(
                    "content-type", ""
                ):
                    return resp.text
                return None
            except Exception as e:
                logger.warning("ar5iv_failed", arxiv_id=clean_id, error=str(e))
                return None

    # ─── TeX extraction helpers ──────────────────────────────────────

    @staticmethod
    def _extract_tex_from_tar(tar_bytes: bytes, arxiv_id: str) -> dict | None:
        """Extract .tex files from a tar.gz archive."""
        try:
            with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:gz") as tar:
                all_files: dict[str, str] = {}
                tex_files: list[tuple[str, str]] = []

                for member in tar.getmembers():
                    if not member.isfile():
                        continue
                    name = member.name

                    # Read text-based files
                    if name.endswith((".tex", ".bib", ".bbl", ".sty", ".cls", ".txt")):
                        try:
                            f = tar.extractfile(member)
                            if f:
                                content = f.read().decode("utf-8", errors="replace")
                                all_files[name] = content
                                if name.endswith(".tex"):
                                    tex_files.append((name, content))
                        except Exception:
                            continue

                if not tex_files:
                    return None

                # Find main .tex file: prefer one with \begin{document} or the largest
                main_tex = None
                for name, content in tex_files:
                    if r"\begin{document}" in content:
                        main_tex = content
                        break

                if main_tex is None:
                    # Fallback: largest .tex file is usually the main one
                    main_tex = max(tex_files, key=lambda x: len(x[1]))[1]

                return {
                    "arxiv_id": arxiv_id,
                    "main_tex": main_tex,
                    "all_files": all_files,
                }

        except (tarfile.TarError, EOFError) as e:
            logger.warning("arxiv_tar_extract_failed", arxiv_id=arxiv_id, error=str(e))
            return None

    @staticmethod
    def extract_text_from_latex(tex_source: str) -> str:
        """
        Extract plain text from LaTeX source code.

        Strips LaTeX commands, keeps text content.
        Preserves section structure as markdown-like headers.
        """
        text = tex_source

        # Remove comments
        text = re.sub(r"(?<!\\)%.*$", "", text, flags=re.MULTILINE)

        # Convert section headers to readable format
        text = re.sub(r"\\section\*?\{([^}]+)\}", r"\n## \1\n", text)
        text = re.sub(r"\\subsection\*?\{([^}]+)\}", r"\n### \1\n", text)
        text = re.sub(r"\\subsubsection\*?\{([^}]+)\}", r"\n#### \1\n", text)

        # Extract title and abstract
        title_match = re.search(r"\\title\{([^}]+)\}", text)
        abstract_match = re.search(
            r"\\begin\{abstract\}(.*?)\\end\{abstract\}", text, re.DOTALL
        )

        # Remove common environments we don't want
        text = re.sub(r"\\begin\{figure\}.*?\\end\{figure\}", "", text, flags=re.DOTALL)
        text = re.sub(r"\\begin\{table\}.*?\\end\{table\}", "", text, flags=re.DOTALL)

        # Keep equations as-is (they're useful for understanding)
        # Convert inline math to $...$ readable form
        text = re.sub(r"\\\((.+?)\\\)", r"$\1$", text)
        text = re.sub(r"\\\[(.+?)\\\]", r"$$\1$$", text, flags=re.DOTALL)

        # Remove specific commands but keep content
        text = re.sub(
            r"\\(?:textbf|textit|emph|underline|texttt)\{([^}]+)\}", r"\1", text
        )
        text = re.sub(r"\\(?:cite|ref|label|eqref)\{[^}]*\}", "[ref]", text)
        text = re.sub(r"\\(?:footnote)\{([^}]+)\}", r" (\1)", text)

        # Remove remaining commands
        text = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])*(?:\{[^}]*\})*", "", text)

        # Clean up
        text = re.sub(r"\{|\}", "", text)  # Remove stray braces
        text = re.sub(r"\n{3,}", "\n\n", text)  # Collapse blank lines
        text = re.sub(r"[ \t]+", " ", text)  # Collapse whitespace

        # Extract between \begin{document} and \end{document}
        doc_match = re.search(
            r"\\begin\{document\}(.*)\\end\{document\}", text, re.DOTALL
        )
        if doc_match:
            text = doc_match.group(1)

        return text.strip()

    # ─── Metadata parsing ────────────────────────────────────────────

    @staticmethod
    def _parse_atom_entry(xml_text: str) -> dict:
        """Parse arXiv Atom XML response into a structured dict."""
        from lxml import etree

        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom",
        }

        root = etree.fromstring(xml_text.encode())
        entries = root.findall("atom:entry", ns)
        if not entries:
            return {}

        entry = entries[0]

        # Extract arXiv ID from entry id URL
        entry_id = entry.findtext("atom:id", default="", namespaces=ns)
        arxiv_id_match = re.search(r"abs/(.+?)(?:v\d+)?$", entry_id)
        arxiv_id = arxiv_id_match.group(1) if arxiv_id_match else ""

        # Authors
        authors = []
        for author_elem in entry.findall("atom:author", ns):
            name = author_elem.findtext("atom:name", default="", namespaces=ns)
            affiliation = author_elem.findtext(
                "arxiv:affiliation", default="", namespaces=ns
            )
            authors.append({"name": name, "affiliation": affiliation})

        # Categories
        categories = [
            cat.get("term", "")
            for cat in entry.findall("atom:category", ns)
            if cat.get("term")
        ]

        # DOI (if present)
        doi = entry.findtext("arxiv:doi", default=None, namespaces=ns)

        return {
            "arxiv_id": arxiv_id,
            "title": (entry.findtext("atom:title", default="", namespaces=ns) or "")
            .strip()
            .replace("\n", " "),
            "abstract": (
                entry.findtext("atom:summary", default="", namespaces=ns) or ""
            ).strip(),
            "authors": authors,
            "categories": categories,
            "published": entry.findtext("atom:published", default="", namespaces=ns),
            "updated": entry.findtext("atom:updated", default="", namespaces=ns),
            "doi": doi,
            "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}.pdf" if arxiv_id else None,
            "abs_url": f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else None,
            "source_url": f"https://arxiv.org/e-print/{arxiv_id}" if arxiv_id else None,
            "html_url": (
                f"https://ar5iv.labs.arxiv.org/html/{arxiv_id}" if arxiv_id else None
            ),
        }

    @staticmethod
    def construct_pdf_url(arxiv_id: str) -> str:
        """Construct PDF URL from arXiv ID."""
        clean_id = arxiv_id.replace("arXiv:", "").strip()
        return f"https://arxiv.org/pdf/{clean_id}.pdf"

    @staticmethod
    def construct_source_url(arxiv_id: str) -> str:
        """Construct LaTeX source URL from arXiv ID."""
        clean_id = arxiv_id.replace("arXiv:", "").strip()
        return f"https://arxiv.org/e-print/{clean_id}"

    @staticmethod
    def construct_html_url(arxiv_id: str) -> str:
        """Construct ar5iv HTML URL from arXiv ID."""
        clean_id = arxiv_id.replace("arXiv:", "").strip()
        return f"https://ar5iv.labs.arxiv.org/html/{clean_id}"

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
