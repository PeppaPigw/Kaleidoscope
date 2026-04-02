"""GROBID client — parse PDFs into structured TEI XML."""

import httpx
import structlog

from app.config import settings
from app.exceptions import ParsingError

logger = structlog.get_logger(__name__)


class GROBIDResult:
    """Structured result from GROBID parsing."""

    def __init__(
        self,
        tei_xml: str,
        title: str | None = None,
        abstract: str | None = None,
        sections: list[dict] | None = None,
        references: list[dict] | None = None,
        authors: list[dict] | None = None,
        keywords: list[str] | None = None,
    ):
        self.tei_xml = tei_xml
        self.title = title
        self.abstract = abstract
        self.sections = sections or []
        self.references = references or []
        self.authors = authors or []
        self.keywords = keywords or []


class GROBIDClient:
    """
    GROBID API client for PDF parsing.

    GROBID extracts structured data from PDFs:
    - Title, abstract, keywords
    - Section structure (headers + body text)
    - Reference list with structured fields
    - Author names and affiliations

    Expects GROBID running as Docker service at settings.grobid_url.
    """

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or settings.grobid_url

    async def parse_pdf(self, pdf_content: bytes, paper_id: str = "") -> GROBIDResult:
        """
        Parse a PDF file with GROBID's full-text processing endpoint.

        Returns structured result with title, abstract, sections, and references.
        """
        log = logger.bind(paper_id=paper_id)

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{self.base_url}/api/processFulltextDocument",
                    files={"input": ("paper.pdf", pdf_content, "application/pdf")},
                    data={
                        "consolidateHeader": "1",
                        "consolidateCitations": "1",
                        "includeRawCitations": "1",
                        "teiCoordinates": "ref",
                    },
                )
                resp.raise_for_status()
                tei_xml = resp.text

        except httpx.HTTPError as e:
            log.error("grobid_request_failed", error=str(e))
            raise ParsingError(paper_id, "GROBID", f"Request failed: {e}")

        try:
            result = self._parse_tei(tei_xml)
            log.info(
                "grobid_parse_complete",
                sections=len(result.sections),
                references=len(result.references),
            )
            return result
        except Exception as e:
            log.error("grobid_tei_parse_failed", error=str(e))
            # Still return raw TEI even if structured parsing fails
            return GROBIDResult(tei_xml=tei_xml)

    def _parse_tei(self, tei_xml: str) -> GROBIDResult:
        """Parse GROBID TEI XML into structured data."""
        from lxml import etree

        ns = {"tei": "http://www.tei-c.org/ns/1.0"}
        root = etree.fromstring(tei_xml.encode())

        # --- Title ---
        title_elem = root.find(".//tei:titleStmt/tei:title", ns)
        title = (
            title_elem.text.strip()
            if title_elem is not None and title_elem.text
            else None
        )

        # --- Abstract ---
        abstract_elem = root.find(".//tei:profileDesc/tei:abstract", ns)
        abstract = None
        if abstract_elem is not None:
            abstract_parts = abstract_elem.itertext()
            abstract = " ".join(t.strip() for t in abstract_parts if t.strip())

        # --- Authors ---
        authors = []
        for author_elem in root.findall(".//tei:fileDesc//tei:author", ns):
            persname = author_elem.find("tei:persName", ns)
            if persname is not None:
                forename = persname.findtext("tei:forename", default="", namespaces=ns)
                surname = persname.findtext("tei:surname", default="", namespaces=ns)
                name = f"{forename} {surname}".strip()
                if name:
                    aff_elem = author_elem.find("tei:affiliation", ns)
                    affiliation = ""
                    if aff_elem is not None:
                        org = aff_elem.findtext(
                            "tei:orgName", default="", namespaces=ns
                        )
                        affiliation = org
                    authors.append({"name": name, "affiliation": affiliation})

        # --- Sections ---
        sections = []
        body = root.find(".//tei:body", ns)
        if body is not None:
            for div in body.findall("tei:div", ns):
                head = div.findtext("tei:head", default="", namespaces=ns)
                paragraphs = []
                for p in div.findall("tei:p", ns):
                    text_parts = p.itertext()
                    para_text = " ".join(t.strip() for t in text_parts if t.strip())
                    if para_text:
                        paragraphs.append(para_text)
                if head or paragraphs:
                    n = div.get("n", "")
                    sections.append(
                        {
                            "heading": head,
                            "number": n,
                            "paragraphs": paragraphs,
                        }
                    )

        # --- References ---
        references = []
        for i, ref in enumerate(root.findall(".//tei:listBibl/tei:biblStruct", ns)):
            ref_data: dict = {"position": i}

            # Title
            title_elem = ref.find(".//tei:title[@level='a']", ns)
            if title_elem is None:
                title_elem = ref.find(".//tei:title", ns)
            if title_elem is not None and title_elem.text:
                ref_data["title"] = title_elem.text.strip()

            # Authors
            ref_authors = []
            for author_elem in ref.findall(".//tei:author/tei:persName", ns):
                forename = author_elem.findtext(
                    "tei:forename", default="", namespaces=ns
                )
                surname = author_elem.findtext("tei:surname", default="", namespaces=ns)
                name = f"{forename} {surname}".strip()
                if name:
                    ref_authors.append(name)
            ref_data["authors"] = ref_authors

            # Year
            date_elem = ref.find(".//tei:date[@type='published']", ns)
            if date_elem is not None:
                ref_data["year"] = date_elem.get("when", "")[:4]

            # DOI
            doi_elem = ref.find(".//tei:idno[@type='DOI']", ns)
            if doi_elem is not None and doi_elem.text:
                ref_data["doi"] = doi_elem.text.strip()

            # Raw string
            raw_elem = ref.find(".//tei:note[@type='raw_reference']", ns)
            if raw_elem is not None and raw_elem.text:
                ref_data["raw_string"] = raw_elem.text.strip()

            references.append(ref_data)

        # --- Keywords ---
        keywords = []
        for kw in root.findall(".//tei:profileDesc//tei:term", ns):
            if kw.text and kw.text.strip():
                keywords.append(kw.text.strip())

        return GROBIDResult(
            tei_xml=tei_xml,
            title=title,
            abstract=abstract,
            sections=sections,
            references=references,
            authors=authors,
            keywords=keywords,
        )

    async def is_alive(self) -> bool:
        """Check if GROBID service is running."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/api/isalive")
                return resp.status_code == 200
        except Exception:
            return False
