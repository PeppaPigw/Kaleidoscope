"""Citation export service — BibTeX, RIS, and CSL-JSON generation."""

import json
from datetime import date

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.paper import Paper
from app.models.author import PaperAuthor, Author

logger = structlog.get_logger(__name__)


class ExportService:
    """Generate citation exports in multiple formats."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def export_papers(
        self, paper_ids: list[str], format: str = "bibtex"
    ) -> str:
        """Export citations for the given papers in the requested format."""
        result = await self.db.execute(
            select(Paper)
            .where(Paper.id.in_(paper_ids))
            .options(
                selectinload(Paper.authors).selectinload(PaperAuthor.author)
            )
        )
        papers = list(result.scalars().all())

        if format == "bibtex":
            return self._to_bibtex(papers)
        elif format == "ris":
            return self._to_ris(papers)
        elif format == "csl_json":
            return self._to_csl_json(papers)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    @staticmethod
    def _get_author_names(paper: Paper) -> list[str]:
        """
        Extract author display names from the paper's author relationships.

        Returns names in order of authorship position (first author first).
        Falls back to raw_metadata authors if ORM relationships are empty.
        """
        if paper.authors:
            # Sort by position (PaperAuthor.position)
            sorted_authors = sorted(paper.authors, key=lambda pa: pa.position)
            return [pa.author.display_name for pa in sorted_authors if pa.author]

        # Fallback: try raw_metadata GROBID authors
        raw = paper.raw_metadata or {}
        if raw.get("parsed_sections"):
            # GROBID also stores authors at top level
            pass
        grobid_authors = raw.get("authors", [])
        if grobid_authors:
            return [a.get("name", "") for a in grobid_authors if a.get("name")]

        return []

    def _to_bibtex(self, papers: list[Paper]) -> str:
        """Generate BibTeX entries."""
        entries = []
        for paper in papers:
            cite_key = self._make_cite_key(paper)
            entry_type = self._bibtex_type(paper.paper_type)
            author_names = self._get_author_names(paper)

            lines = [f"@{entry_type}{{{cite_key},"]
            lines.append(f"  title = {{{paper.title}}},")

            # Authors in BibTeX format: "Last1, First1 and Last2, First2"
            if author_names:
                lines.append(f"  author = {{{' and '.join(author_names)}}},")

            if paper.doi:
                lines.append(f"  doi = {{{paper.doi}}},")

            if paper.arxiv_id:
                lines.append(f"  eprint = {{{paper.arxiv_id}}},")
                lines.append("  archiveprefix = {arXiv},")

            if paper.published_at:
                lines.append(f"  year = {{{paper.published_at.year}}},")
                lines.append(f"  month = {{{paper.published_at.month}}},")

            if paper.abstract:
                # Escape special BibTeX characters
                abstract = paper.abstract.replace("{", "\\{").replace("}", "\\}")
                lines.append(f"  abstract = {{{abstract}}},")

            if paper.keywords:
                lines.append(f"  keywords = {{{', '.join(paper.keywords)}}},")

            # Try to get venue from raw_metadata
            venue = self._get_venue(paper)
            if venue:
                if entry_type == "inproceedings":
                    lines.append(f"  booktitle = {{{venue}}},")
                else:
                    lines.append(f"  journal = {{{venue}}},")

            if paper.remote_urls:
                urls = [u.get("url", "") for u in paper.remote_urls if u.get("url")]
                if urls:
                    lines.append(f"  url = {{{urls[0]}}},")

            lines.append("}")
            entries.append("\n".join(lines))

        return "\n\n".join(entries)

    def _to_ris(self, papers: list[Paper]) -> str:
        """Generate RIS entries."""
        entries = []
        for paper in papers:
            lines = []
            ris_type = self._ris_type(paper.paper_type)
            lines.append(f"TY  - {ris_type}")
            lines.append(f"TI  - {paper.title}")

            # Authors — one AU line per author
            author_names = self._get_author_names(paper)
            for name in author_names:
                lines.append(f"AU  - {name}")

            if paper.doi:
                lines.append(f"DO  - {paper.doi}")

            if paper.published_at:
                lines.append(f"PY  - {paper.published_at.year}")
                da = paper.published_at.strftime("%Y/%m/%d")
                lines.append(f"DA  - {da}")

            if paper.abstract:
                lines.append(f"AB  - {paper.abstract}")

            if paper.keywords:
                for kw in paper.keywords:
                    lines.append(f"KW  - {kw}")

            venue = self._get_venue(paper)
            if venue:
                if ris_type == "CPAPER":
                    lines.append(f"T2  - {venue}")
                else:
                    lines.append(f"JO  - {venue}")

            if paper.remote_urls:
                urls = [u.get("url", "") for u in paper.remote_urls if u.get("url")]
                if urls:
                    lines.append(f"UR  - {urls[0]}")

            lines.append("ER  - ")
            entries.append("\n".join(lines))

        return "\n\n".join(entries)

    def _to_csl_json(self, papers: list[Paper]) -> str:
        """Generate CSL-JSON."""
        items = []
        for paper in papers:
            item = {
                "id": str(paper.id),
                "type": self._csl_type(paper.paper_type),
                "title": paper.title,
            }

            # Authors in CSL-JSON format: [{family, given}]
            author_names = self._get_author_names(paper)
            if author_names:
                csl_authors = []
                for name in author_names:
                    parts = name.rsplit(" ", 1)
                    if len(parts) == 2:
                        csl_authors.append({"given": parts[0], "family": parts[1]})
                    else:
                        csl_authors.append({"literal": name})
                item["author"] = csl_authors

            if paper.doi:
                item["DOI"] = paper.doi

            if paper.published_at:
                item["issued"] = {
                    "date-parts": [[
                        paper.published_at.year,
                        paper.published_at.month,
                        paper.published_at.day,
                    ]]
                }

            if paper.abstract:
                item["abstract"] = paper.abstract

            venue = self._get_venue(paper)
            if venue:
                item["container-title"] = venue

            items.append(item)

        return json.dumps(items, indent=2, ensure_ascii=False)

    # ─── Helpers ─────────────────────────────────────────────────

    @staticmethod
    def _make_cite_key(paper: Paper) -> str:
        """Generate a BibTeX cite key from paper metadata."""
        # Use DOI-based or arXiv-based key
        if paper.doi:
            # e.g., "10.1038/s41586-024-00001" → "s41586-024-00001"
            parts = paper.doi.split("/")
            return parts[-1] if parts else str(paper.id)[:8]
        if paper.arxiv_id:
            return paper.arxiv_id.replace("/", "_").replace(".", "_")
        # Fallback: sanitized title
        title_words = (paper.title or "untitled").split()[:3]
        key = "_".join(w.lower() for w in title_words)
        if paper.published_at:
            key += f"_{paper.published_at.year}"
        return key

    @staticmethod
    def _get_venue(paper: Paper) -> str | None:
        """Extract venue name from raw_metadata."""
        if paper.raw_metadata and paper.raw_metadata.get("crossref_venue"):
            return paper.raw_metadata["crossref_venue"]
        return None

    @staticmethod
    def _bibtex_type(paper_type: str | None) -> str:
        mapping = {
            "journal-article": "article",
            "proceedings-article": "inproceedings",
            "book": "book",
            "book-chapter": "incollection",
            "posted-content": "misc",
            "dissertation": "phdthesis",
        }
        return mapping.get(paper_type or "", "article")

    @staticmethod
    def _ris_type(paper_type: str | None) -> str:
        mapping = {
            "journal-article": "JOUR",
            "proceedings-article": "CPAPER",
            "book": "BOOK",
            "book-chapter": "CHAP",
            "posted-content": "UNPB",
            "dissertation": "THES",
        }
        return mapping.get(paper_type or "", "JOUR")

    @staticmethod
    def _csl_type(paper_type: str | None) -> str:
        mapping = {
            "journal-article": "article-journal",
            "proceedings-article": "paper-conference",
            "book": "book",
            "book-chapter": "chapter",
            "posted-content": "article",
            "dissertation": "thesis",
        }
        return mapping.get(paper_type or "", "article-journal")
