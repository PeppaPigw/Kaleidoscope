"""MinerU parsing service — convert PDF/HTML to Markdown and extract structure.

Replaces GROBID for remote papers. Stores markdown directly in Paper.full_text_markdown,
extracts sections/figures/references from markdown structure, and materializes
PaperReference rows for citation graph consistency.
"""

import re
from datetime import UTC, datetime

import structlog
from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.clients.mineru_client import MinerUClient, MinerUModel
from app.models.paper import Paper, PaperReference

logger = structlog.get_logger(__name__)


def sanitize_mineru_markdown(markdown: str | None) -> str:
    """Strip control bytes MinerU occasionally leaks that PostgreSQL rejects."""
    if not markdown:
        return ""
    return markdown.replace("\x00", "")


def extract_title_from_markdown(markdown: str | None) -> str | None:
    """Best-effort title extraction from the first meaningful H1 heading."""
    if not markdown:
        return None

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        match = re.match(r"^#\s+(.+)$", line)
        if not match:
            continue

        title = re.sub(r"\s+", " ", match.group(1)).strip(" #\t")
        if not title:
            continue
        if title.startswith((": ", ":", "-", "–", "—")):
            continue

        normalized = re.sub(r"^\d+(?:\.\d+)*[\s.:_-]*", "", title).strip()
        lowered = normalized.casefold()
        if lowered in {
            "abstract",
            "contents",
            "table of contents",
            "introduction",
            "references",
            "bibliography",
        }:
            return None

        return title

    return None


class MinerUParsingService:
    """Parse documents via MinerU API and store as markdown."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._client: MinerUClient | None = None

    async def _get_client(self) -> MinerUClient:
        if self._client is None:
            self._client = MinerUClient()
        return self._client

    async def parse_from_url(
        self,
        paper_id: str,
        url: str,
        is_html: bool = False,
    ) -> dict:
        """
        Parse a paper from URL via MinerU → stored as markdown.

        Args:
            paper_id: Paper UUID
            url: PDF or HTML URL
            is_html: Whether the URL points to HTML content

        Returns:
            Result dict with status and metadata
        """
        log = logger.bind(paper_id=paper_id, url=url[:80])
        log.info("mineru_parse_start")

        result = await self.db.execute(select(Paper).where(Paper.id == paper_id))
        paper = result.scalar_one_or_none()
        if not paper:
            return {"status": "error", "error": "Paper not found"}

        client = await self._get_client()

        try:
            extraction = await client.extract(
                url=url,
                is_html=is_html,
                max_wait_seconds=300,
            )
        except Exception as e:
            log.error("mineru_extraction_failed", error=str(e))
            paper.ingestion_status = "parse_failed"
            paper.ingestion_error = f"MinerU: {str(e)[:400]}"
            await self.db.flush()
            return {"status": "error", "error": str(e)}

        if not extraction.success:
            log.error("mineru_extraction_unsuccessful", error=extraction.error)
            paper.ingestion_status = "parse_failed"
            paper.ingestion_error = f"MinerU: {extraction.error}"
            await self.db.flush()
            return {"status": "error", "error": extraction.error}

        # ── Store markdown content ────────────────────────────────
        markdown = sanitize_mineru_markdown(extraction.markdown)
        paper.full_text_markdown = markdown
        paper.has_full_text = True
        paper.markdown_provenance = {
            "source": "mineru",
            "model_version": (
                MinerUModel.HTML.value if is_html else MinerUModel.PDF_VLM.value
            ),
            "task_id": extraction.task_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "markdown_length": len(markdown),
        }

        # ── Store original URL (assign new list for SQLAlchemy tracking) ──
        existing_urls: list[dict] = paper.remote_urls or []
        if not any(u.get("url") == url for u in existing_urls):
            paper.remote_urls = existing_urls + [
                {
                    "url": url,
                    "source": "mineru_input",
                    "type": "html" if is_html else "pdf",
                }
            ]

        # ── Extract structure from markdown ───────────────────────
        sections = self._extract_sections(markdown)
        paper.parsed_sections = sections

        title_text = (paper.title or "").strip()
        if (
            not title_text
            or title_text == (paper.doi or "").strip()
            or title_text.lower().startswith("arxiv:")
        ):
            extracted_title = extract_title_from_markdown(markdown)
            if extracted_title:
                paper.title = extracted_title

        # ── Extract metadata from markdown if missing ─────────────
        if not paper.abstract:
            paper.abstract = self._extract_abstract(markdown)

        # ── Clear stale error state on success ────────────────────
        paper.ingestion_status = "parsed"
        paper.ingestion_error = None
        paper.parser_version = "mineru"

        # ── Build references and materialize PaperReference rows ──
        refs = self._extract_references(markdown)

        # Always update raw_metadata (including sections for downstream chunker)
        raw_meta = dict(paper.raw_metadata or {})
        raw_meta["parsed_sections"] = sections
        raw_meta["parsed_references"] = refs  # Always overwrite, even if empty
        paper.raw_metadata = raw_meta

        # Materialize PaperReference rows (same pattern as ingest_tasks.py)
        await self._materialize_references(paper, refs)

        # Flag JSONB mutations for SQLAlchemy change tracking
        flag_modified(paper, "markdown_provenance")
        if paper.remote_urls is not None:
            flag_modified(paper, "remote_urls")
        if paper.raw_metadata is not None:
            flag_modified(paper, "raw_metadata")
        if paper.parsed_sections is not None:
            flag_modified(paper, "parsed_sections")

        await self.db.flush()
        log.info(
            "mineru_parse_complete",
            sections=len(sections),
            references=len(refs),
            markdown_length=len(markdown),
        )

        return {
            "status": "parsed",
            "parser": "mineru",
            "markdown_length": len(markdown),
            "sections": len(sections),
            "references": len(refs),
        }

    async def _materialize_references(self, paper: Paper, refs: list[dict]) -> None:
        """
        Idempotently create PaperReference rows from extracted references,
        then resolve cited_paper_id by matching DOI/title.
        Mirrors the pattern in ingest_tasks.py.
        """
        paper_id = paper.id

        # Delete existing references
        await self.db.execute(
            sa_delete(PaperReference).where(PaperReference.citing_paper_id == paper_id)
        )

        for ref in refs:
            paper_ref = PaperReference(
                citing_paper_id=paper_id,
                cited_paper_id=None,
                raw_title=ref.get("title"),
                raw_authors=None,
                raw_year=ref.get("year"),
                raw_doi=ref.get("doi"),
                raw_string=ref.get("raw_string"),
                position=ref.get("position"),
            )
            self.db.add(paper_ref)

        await self.db.flush()

        # Resolve cited_paper_id by matching DOI/title in existing papers
        unresolved = await self.db.execute(
            select(PaperReference).where(
                PaperReference.citing_paper_id == paper_id,
                PaperReference.cited_paper_id.is_(None),
            )
        )
        resolved_count = 0
        for ref in unresolved.scalars().all():
            cited = None
            if ref.raw_doi:
                doi_result = await self.db.execute(
                    select(Paper.id)
                    .where(
                        Paper.doi == ref.raw_doi,
                        Paper.deleted_at.is_(None),
                    )
                    .limit(1)
                )
                cited = doi_result.scalar_one_or_none()

            if not cited and ref.raw_title and len(ref.raw_title) > 10:
                title_result = await self.db.execute(
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
            logger.info("references_resolved", resolved=resolved_count)

    def _extract_sections(self, markdown: str) -> list[dict]:
        """Extract section structure from markdown headings."""
        sections: list[dict] = []
        current_paragraphs: list[str] = []
        current_title: str | None = None
        current_level: int = 1

        for line in markdown.split("\n"):
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if heading_match:
                # Save previous section
                if current_title is not None:
                    sections.append(
                        {
                            "title": current_title,
                            "level": current_level,
                            "paragraphs": [p for p in current_paragraphs if p.strip()],
                        }
                    )
                current_level = len(heading_match.group(1))
                current_title = heading_match.group(2).strip()
                current_paragraphs = []
            elif line.strip():
                current_paragraphs.append(line.strip())

        # Last section
        if current_title is not None:
            sections.append(
                {
                    "title": current_title,
                    "level": current_level,
                    "paragraphs": [p for p in current_paragraphs if p.strip()],
                }
            )

        return sections

    def _extract_abstract(self, markdown: str) -> str | None:
        """Try to extract abstract from markdown content."""
        # Look for explicit "Abstract" heading
        match = re.search(
            r"#+\s*Abstract\s*\n([\s\S]*?)(?=\n#|\Z)",
            markdown,
            re.IGNORECASE,
        )
        if match:
            abstract = match.group(1).strip()
            # Clean up markdown formatting
            abstract = re.sub(r"\*\*([^*]+)\*\*", r"\1", abstract)
            abstract = re.sub(r"\*([^*]+)\*", r"\1", abstract)
            if 50 < len(abstract) < 3000:
                return abstract

        # Fallback: first substantial paragraph
        paragraphs = [
            p.strip()
            for p in markdown.split("\n\n")
            if p.strip() and not p.strip().startswith("#") and len(p.strip()) > 100
        ]
        if paragraphs:
            return paragraphs[0][:2000]

        return None

    def _extract_references(self, markdown: str) -> list[dict]:
        """Extract references from markdown reference section."""
        refs: list[dict] = []

        # Find References/Bibliography section
        ref_match = re.search(
            r"#+\s*(?:References|Bibliography|Works Cited)\s*\n([\s\S]*?)(?=\n#[^#]|\Z)",
            markdown,
            re.IGNORECASE,
        )
        if not ref_match:
            return refs

        ref_text = ref_match.group(1)

        # Parse numbered references [1], [2], etc. or 1. 2. etc.
        ref_items = re.split(r"\n\s*(?:\[?\d+\]?[\.\)]\s*)", ref_text)

        for i, item in enumerate(ref_items):
            item = item.strip()
            if not item or len(item) < 20:
                continue

            ref: dict = {
                "position": i,
                "raw_string": item[:500],
            }

            # Try to extract DOI
            doi_match = re.search(r"(10\.\d{4,}/[^\s]+)", item)
            if doi_match:
                ref["doi"] = doi_match.group(1).rstrip(".,;)")

            # Try to extract year
            year_match = re.search(r"\b((?:19|20)\d{2})\b", item)
            if year_match:
                ref["year"] = year_match.group(1)

            # Try to extract title (usually in quotes or after authors)
            title_match = re.search(r'["""](.+?)["""]', item)
            if title_match:
                ref["title"] = title_match.group(1)

            refs.append(ref)

        return refs

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None
