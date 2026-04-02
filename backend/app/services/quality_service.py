"""Quality service — metadata completeness, retraction, and provenance."""

from collections.abc import Sequence
from datetime import date, datetime
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.governance import UserCorrection
from app.models.paper import Paper

REPRODUCIBILITY_KEYWORDS = [
    "github.com",
    "code available",
    "reproducible",
    "open source",
    "zenodo",
]

# Fields whose provenance we track, with friendly labels
PROVENANCE_FIELDS = [
    "title",
    "abstract",
    "doi",
    "arxiv_id",
    "published_at",
    "keywords",
    "authors",
    "venue_id",
    "citation_count",
    "summary",
    "highlights",
    "contributions",
    "limitations",
]

CROSSREF_API = "https://api.crossref.org/works/{doi}"


class QualityService:
    """Evaluate metadata completeness and reproducibility signals for papers."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Retraction Check (Feature 7) ─────────────────────────────

    async def retraction_check(self, paper_id: str) -> dict:
        """Check CrossRef for retraction status of a paper."""
        paper = await self._get_paper(paper_id)
        if not paper:
            return {"paper_id": paper_id, "error": "Paper not found"}

        if not paper.doi:
            return {
                "paper_id": paper_id,
                "doi": None,
                "is_retracted": None,
                "status": "no_doi",
                "message": "Cannot check — paper has no DOI.",
            }

        try:
            url = CROSSREF_API.format(doi=paper.doi)
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers={"User-Agent": "Kaleidoscope/1.0"})

            if resp.status_code == 404:
                return {
                    "paper_id": paper_id,
                    "doi": paper.doi,
                    "is_retracted": None,
                    "status": "doi_not_found",
                    "message": "DOI not found in CrossRef.",
                }
            resp.raise_for_status()
            data = resp.json().get("message", {})
            is_retracted: bool = data.get("is-retracted", False)
            update_to = data.get("update-to", [])
            retraction_notices = [
                {
                    "type": u.get("type"),
                    "doi": u.get("DOI"),
                    "updated": u.get("updated", {}).get("date-parts"),
                }
                for u in update_to
                if u.get("type") in ("retraction", "partial-retraction", "correction")
            ]
            return {
                "paper_id": paper_id,
                "doi": paper.doi,
                "is_retracted": is_retracted,
                "status": "retracted" if is_retracted else "ok",
                "retraction_notices": retraction_notices,
                "crossref_update_to": update_to,
            }
        except httpx.HTTPStatusError as exc:
            return {
                "paper_id": paper_id,
                "doi": paper.doi,
                "is_retracted": None,
                "status": "crossref_error",
                "message": str(exc),
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "paper_id": paper_id,
                "doi": paper.doi,
                "is_retracted": None,
                "status": "error",
                "message": str(exc),
            }

    # ── Field Provenance (Feature 8) ─────────────────────────────

    async def get_provenance(self, paper_id: str) -> dict:
        """Return field-level provenance chain for a paper.

        Provenance is reconstructed from raw_metadata source markers written
        by the ingestion pipeline (CrossRef, OpenAlex, SemanticScholar, arXiv,
        GROBID, MinerU). If a dedicated provenance field is absent, we use
        source_type and markdown_provenance as fallbacks.
        """
        paper = await self._get_paper(paper_id)
        if not paper:
            return {"paper_id": paper_id, "error": "Paper not found"}

        raw = paper.raw_metadata or {}
        prov_meta = raw.get("provenance", {})
        ingested_at = str(paper.created_at) if paper.created_at else None

        fields = {}
        for field in PROVENANCE_FIELDS:
            value = getattr(paper, field, None)
            field_prov = prov_meta.get(field, {})
            fields[field] = {
                "present": value is not None,
                "source": field_prov.get("source") or self._infer_source(field, paper),
                "confidence": field_prov.get("confidence"),
                "fetched_at": field_prov.get("fetched_at") or ingested_at,
                "note": field_prov.get("note"),
            }

        return {
            "paper_id": paper_id,
            "doi": paper.doi,
            "arxiv_id": paper.arxiv_id,
            "source_type": paper.source_type,
            "markdown_provenance": paper.markdown_provenance,
            "parser_version": paper.parser_version,
            "ingest_sources": raw.get("ingest_sources", []),
            "fields": fields,
        }

    @staticmethod
    def _infer_source(field: str, paper: Paper) -> str:
        """Infer probable source for a field from available top-level signals."""
        doi_fields = {"citation_count", "venue_id", "published_at"}
        arxiv_fields = {"abstract", "keywords", "authors"}
        llm_fields = {"summary", "highlights", "contributions", "limitations"}

        if field in llm_fields:
            return "llm_extraction"
        if field == "title":
            return paper.source_type or "unknown"
        if field in doi_fields and paper.doi:
            return "crossref"
        if field in arxiv_fields and paper.arxiv_id:
            return "arxiv"
        return paper.source_type or "unknown"

    async def get_metadata_score(self, paper_id: str) -> dict:
        """Compute metadata completeness score for a paper."""
        paper = await self._get_paper(paper_id)
        if not paper:
            return {"paper_id": paper_id, "error": "Paper not found"}

        fields = [
            ("title", paper.title),
            ("abstract", paper.abstract),
            ("doi", paper.doi),
            ("arxiv_id", paper.arxiv_id),
            ("published_at", paper.published_at),
            ("keywords", paper.keywords),
            ("citation_count", paper.citation_count),
            ("venue_id", paper.venue_id),
            ("summary", paper.summary),
            ("highlights", paper.highlights),
            ("contributions", paper.contributions),
            ("limitations", paper.limitations),
        ]

        details = []
        filled_fields = 0
        for field_name, value in fields:
            present = self._is_present(field_name, value)
            if present:
                filled_fields += 1
            details.append(
                {
                    "field": field_name,
                    "present": present,
                    "value_preview": self._preview_value(value),
                }
            )

        total_fields = len(fields)
        score_pct = (
            int(round((filled_fields / total_fields) * 100)) if total_fields else 0
        )
        return {
            "paper_id": str(paper.id),
            "total_fields": total_fields,
            "filled_fields": filled_fields,
            "score_pct": score_pct,
            "details": details,
        }

    async def get_reproducibility(self, paper_id: str) -> dict:
        """Compute reproducibility signals and a coarse score for a paper."""
        paper = await self._get_paper(paper_id)
        if not paper:
            return {"paper_id": paper_id, "error": "Paper not found"}

        searchable_text = " ".join(
            part
            for part in [
                self._stringify(paper.raw_metadata),
                paper.grobid_tei or "",
                paper.full_text_markdown or "",
            ]
            if part
        ).lower()
        matched_keywords = [
            kw for kw in REPRODUCIBILITY_KEYWORDS if kw in searchable_text
        ]

        has_code_keyword = any(
            kw in matched_keywords
            for kw in ("github.com", "code available", "open source")
        )
        has_open_artifact_keyword = any(
            kw in matched_keywords for kw in ("reproducible", "zenodo")
        )

        reproducibility_signals: list[str] = []
        if paper.has_full_text:
            reproducibility_signals.append("has_full_text")
        if paper.markdown_provenance:
            reproducibility_signals.append("markdown_provenance")
        if paper.source_type:
            reproducibility_signals.append(f"source_type:{paper.source_type}")
        reproducibility_signals.extend(f"keyword:{kw}" for kw in matched_keywords)

        score = min(
            5,
            int(bool(paper.has_full_text))
            + int(bool(paper.markdown_provenance))
            + int(bool(paper.source_type))
            + int(has_code_keyword)
            + int(has_open_artifact_keyword),
        )

        return {
            "paper_id": str(paper.id),
            "reproducibility_signals": reproducibility_signals,
            "has_code_keyword": has_code_keyword,
            "has_full_text": paper.has_full_text,
            "score": score,
        }

    async def get_quality_report(self, paper_id: str) -> dict:
        """Aggregate completeness, reproducibility, and correction data."""
        metadata_score = await self.get_metadata_score(paper_id)
        reproducibility = await self.get_reproducibility(paper_id)
        corrections_result = await self.db.execute(
            select(UserCorrection)
            .where(UserCorrection.paper_id == paper_id)
            .order_by(UserCorrection.created_at.desc())
        )
        corrections = [
            {
                "id": str(c.id),
                "field_name": c.field_name,
                "original_value": c.original_value,
                "corrected_value": c.corrected_value,
                "note": c.note,
                "status": c.status,
                "created_at": str(c.created_at),
            }
            for c in corrections_result.scalars().all()
        ]
        return {
            "paper_id": paper_id,
            "metadata_score": metadata_score,
            "reproducibility": reproducibility,
            "corrections": corrections,
        }

    async def _get_paper(self, paper_id: str) -> Paper | None:
        result = await self.db.execute(
            select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def score_metadata(self, paper_id: str) -> dict:
        """Alias for get_metadata_score — used by agent-summary endpoint."""
        return await self.get_metadata_score(paper_id)

    @staticmethod
    def _is_present(field_name: str, value: object) -> bool:
        if field_name == "citation_count":
            return value is not None
        if field_name in {"keywords", "highlights", "contributions", "limitations"}:
            if isinstance(value, dict):
                return len(value) > 0
            if isinstance(value, Sequence) and not isinstance(value, str):
                return len(value) > 0
            return False
        if isinstance(value, str):
            return bool(value.strip())
        return value is not None

    @staticmethod
    def _preview_value(value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value[:120]
        if isinstance(value, (date, datetime, UUID)):
            return str(value)
        return str(value)[:120]

    @staticmethod
    def _stringify(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        return str(value)
