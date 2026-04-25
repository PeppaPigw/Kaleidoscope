"""Universal paper identifier resolver."""

from __future__ import annotations

import re
from typing import Any, Literal
from urllib.parse import urlparse

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.openalex import OpenAlexClient
from app.clients.semantic_scholar import SemanticScholarClient
from app.models.paper import Paper
from app.utils.doi import extract_arxiv_id, extract_doi_from_url, normalize_arxiv_id, normalize_doi

logger = structlog.get_logger(__name__)

IdentifierType = Literal[
    "auto",
    "doi",
    "arxiv",
    "pmid",
    "pmcid",
    "openalex",
    "semantic_scholar",
    "url",
    "title",
]

_PMCID_RE = re.compile(r"\bPMC\d+\b", re.IGNORECASE)
_PMID_RE = re.compile(r"(?:pubmed/|PMID:?\s*)(\d{6,9})", re.IGNORECASE)
_OPENALEX_RE = re.compile(r"\bW\d+\b", re.IGNORECASE)
_S2_HEX_RE = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)


class PaperResolverService:
    """Resolve paper identifiers against local storage and scholarly APIs."""

    def __init__(
        self,
        db: AsyncSession,
        openalex_client: OpenAlexClient | None = None,
        semantic_scholar_client: SemanticScholarClient | None = None,
    ):
        self.db = db
        self._openalex = openalex_client
        self._s2 = semantic_scholar_client
        self._owns_openalex = openalex_client is None
        self._owns_s2 = semantic_scholar_client is None

    async def resolve(
        self,
        identifier: str,
        identifier_type: IdentifierType = "auto",
        include_external: bool = True,
        candidate_limit: int = 5,
    ) -> dict[str, Any]:
        """Resolve a DOI/arXiv/PMID/PMCID/OpenAlex/S2/URL/title to candidates."""
        normalized = self._normalize(identifier, identifier_type)
        local_candidates = await self._find_local_candidates(normalized, candidate_limit)
        external_candidates: list[dict[str, Any]] = []
        errors: list[dict[str, str]] = []

        if include_external:
            external_candidates, errors = await self._find_external_candidates(
                normalized,
                candidate_limit,
            )

        local_match = local_candidates[0] if local_candidates else None
        response = {
            "query": normalized,
            "local": {
                "matched": local_match is not None,
                "paper": local_match,
                "candidates": local_candidates,
            },
            "external_candidates": external_candidates,
            "duplicate_confidence": self._duplicate_confidence(
                local_match,
                external_candidates,
            ),
            "import_status": self._import_status(local_match, external_candidates),
            "recommended_action": self._recommended_action(
                local_match,
                external_candidates,
            ),
            "errors": errors,
        }
        return response

    def _normalize(
        self,
        identifier: str,
        requested_type: IdentifierType,
    ) -> dict[str, Any]:
        raw = identifier.strip()
        extracted = self._extract_identifiers(raw)
        resolved_type = requested_type

        if requested_type == "auto":
            resolved_type = self._infer_type(raw, extracted)

        canonical = self._canonical_value(raw, resolved_type, extracted)
        return {
            "identifier": raw,
            "identifier_type": resolved_type,
            "canonical": canonical,
            "extracted": extracted,
        }

    def _extract_identifiers(self, raw: str) -> dict[str, str]:
        doi = normalize_doi(raw) or extract_doi_from_url(raw) or ""
        arxiv_id = extract_arxiv_id(raw) or ""
        pmid = self._extract_pmid(raw)
        pmcid = self._extract_pmcid(raw)
        openalex_id = self._extract_openalex_id(raw)
        s2_id = self._extract_semantic_scholar_id(raw)
        return {
            key: value
            for key, value in {
                "doi": doi,
                "arxiv": normalize_arxiv_id(arxiv_id) if arxiv_id else "",
                "pmid": pmid,
                "pmcid": pmcid,
                "openalex": openalex_id,
                "semantic_scholar": s2_id,
            }.items()
            if value
        }

    def _infer_type(self, raw: str, extracted: dict[str, str]) -> IdentifierType:
        for candidate_type in (
            "doi",
            "arxiv",
            "pmid",
            "pmcid",
            "openalex",
            "semantic_scholar",
        ):
            if extracted.get(candidate_type):
                return candidate_type  # type: ignore[return-value]
        if raw.lower().startswith(("http://", "https://")):
            return "url"
        return "title"

    def _canonical_value(
        self,
        raw: str,
        identifier_type: IdentifierType,
        extracted: dict[str, str],
    ) -> str:
        if identifier_type in extracted:
            return extracted[identifier_type]
        if identifier_type == "doi":
            return normalize_doi(raw) or raw.lower()
        if identifier_type == "arxiv":
            return normalize_arxiv_id(raw)
        if identifier_type == "pmid":
            return self._extract_pmid(raw) or raw
        if identifier_type == "pmcid":
            return self._extract_pmcid(raw) or raw.upper()
        if identifier_type == "openalex":
            return self._extract_openalex_id(raw) or raw
        if identifier_type == "semantic_scholar":
            return self._extract_semantic_scholar_id(raw) or raw
        return raw

    @staticmethod
    def _extract_pmid(raw: str) -> str:
        match = _PMID_RE.search(raw)
        return match.group(1) if match else ""

    @staticmethod
    def _extract_pmcid(raw: str) -> str:
        match = _PMCID_RE.search(raw)
        return match.group(0).upper() if match else ""

    @staticmethod
    def _extract_openalex_id(raw: str) -> str:
        match = _OPENALEX_RE.search(raw)
        return match.group(0).upper() if match else ""

    @staticmethod
    def _extract_semantic_scholar_id(raw: str) -> str:
        parsed = urlparse(raw)
        if "semanticscholar.org" in parsed.netloc and "/paper/" in parsed.path:
            return parsed.path.rstrip("/").split("/")[-1]
        if _S2_HEX_RE.match(raw.strip()):
            return raw.strip()
        return ""

    async def _find_local_candidates(
        self,
        normalized: dict[str, Any],
        limit: int,
    ) -> list[dict[str, Any]]:
        identifier_type = normalized["identifier_type"]
        canonical = normalized["canonical"]
        extracted = normalized["extracted"]
        candidates: list[tuple[Any, str, float]] = []

        for field, value in self._local_lookup_fields(identifier_type, canonical, extracted):
            result = await self.db.execute(
                select(Paper)
                .where(Paper.deleted_at.is_(None), field == value)
                .limit(limit)
            )
            rows = result.scalars().all()
            candidates.extend((paper, identifier_type, 1.0) for paper in rows)
            if candidates:
                return self._dedupe_local_candidates(candidates)

        if identifier_type == "title" and canonical:
            exact = await self.db.execute(
                select(Paper)
                .where(
                    Paper.deleted_at.is_(None),
                    func.lower(Paper.title) == canonical.lower(),
                )
                .limit(limit)
            )
            exact_rows = exact.scalars().all()
            if exact_rows:
                candidates.extend((paper, "title_exact", 0.9) for paper in exact_rows)
                return self._dedupe_local_candidates(candidates)

            fuzzy = await self.db.execute(
                select(Paper)
                .where(Paper.deleted_at.is_(None), Paper.title.ilike(f"%{canonical}%"))
                .limit(limit)
            )
            fuzzy_rows = fuzzy.scalars().all()
            candidates.extend((paper, "title_fuzzy", 0.65) for paper in fuzzy_rows)

        return self._dedupe_local_candidates(candidates)

    def _local_lookup_fields(
        self,
        identifier_type: str,
        canonical: str,
        extracted: dict[str, str],
    ) -> list[tuple[Any, str]]:
        lookups: list[tuple[Any, str]] = []
        source_values = {identifier_type: canonical, **extracted}
        if value := source_values.get("doi"):
            lookups.append((Paper.doi, value))
        if value := source_values.get("arxiv"):
            lookups.append((Paper.arxiv_id, value))
        if value := source_values.get("pmid"):
            lookups.append((Paper.pmid, value))
        if value := source_values.get("openalex"):
            lookups.append((Paper.openalex_id, value))
            lookups.append((Paper.openalex_id, f"https://openalex.org/{value}"))
        if value := source_values.get("semantic_scholar"):
            lookups.append((Paper.semantic_scholar_id, value))
        return lookups

    def _dedupe_local_candidates(
        self,
        candidates: list[tuple[Any, str, float]],
    ) -> list[dict[str, Any]]:
        seen: set[str] = set()
        deduped: list[dict[str, Any]] = []
        for paper, match_type, confidence in candidates:
            paper_id = str(paper.id)
            if paper_id in seen:
                continue
            seen.add(paper_id)
            deduped.append(self._format_local_paper(paper, match_type, confidence))
        return deduped

    @staticmethod
    def _format_local_paper(
        paper: Any,
        match_type: str,
        confidence: float,
    ) -> dict[str, Any]:
        published_at = getattr(paper, "published_at", None)
        return {
            "paper_id": str(paper.id),
            "title": getattr(paper, "title", None),
            "doi": getattr(paper, "doi", None),
            "arxiv_id": getattr(paper, "arxiv_id", None),
            "pmid": getattr(paper, "pmid", None),
            "openalex_id": getattr(paper, "openalex_id", None),
            "semantic_scholar_id": getattr(paper, "semantic_scholar_id", None),
            "ingestion_status": getattr(paper, "ingestion_status", None),
            "has_full_text": getattr(paper, "has_full_text", None),
            "published_at": str(published_at) if published_at else None,
            "match_type": match_type,
            "confidence": confidence,
        }

    async def _find_external_candidates(
        self,
        normalized: dict[str, Any],
        limit: int,
    ) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
        candidates: list[dict[str, Any]] = []
        errors: list[dict[str, str]] = []
        openalex = self._openalex or OpenAlexClient()
        s2 = self._s2 or SemanticScholarClient()

        try:
            candidates.extend(await self._openalex_candidates(openalex, normalized, limit))
        except Exception as exc:  # noqa: BLE001
            logger.warning("resolve_openalex_failed", error=str(exc))
            errors.append({"source": "openalex", "error": str(exc)})

        try:
            candidates.extend(await self._s2_candidates(s2, normalized, limit))
        except Exception as exc:  # noqa: BLE001
            logger.warning("resolve_semantic_scholar_failed", error=str(exc))
            errors.append({"source": "semantic_scholar", "error": str(exc)})
        finally:
            if self._owns_openalex:
                await openalex.close()
            if self._owns_s2:
                await s2.close()

        return self._dedupe_external_candidates(candidates)[:limit], errors

    async def _openalex_candidates(
        self,
        client: OpenAlexClient,
        normalized: dict[str, Any],
        limit: int,
    ) -> list[dict[str, Any]]:
        identifier_type = normalized["identifier_type"]
        canonical = normalized["canonical"]
        extracted = normalized["extracted"]
        works: list[dict[str, Any]] = []

        if doi := extracted.get("doi") or (canonical if identifier_type == "doi" else ""):
            work = await client.get_work_by_doi(doi)
            works.extend([work] if work else [])
        elif openalex_id := extracted.get("openalex") or (
            canonical if identifier_type == "openalex" else ""
        ):
            work = await client.get_work(openalex_id)
            works.extend([work] if work else [])
        elif identifier_type == "title" and canonical:
            works.extend(await client.search_works(canonical, rows=limit))

        return [self._format_openalex_candidate(work, identifier_type) for work in works]

    async def _s2_candidates(
        self,
        client: SemanticScholarClient,
        normalized: dict[str, Any],
        limit: int,
    ) -> list[dict[str, Any]]:
        identifier_type = normalized["identifier_type"]
        canonical = normalized["canonical"]
        extracted = normalized["extracted"]
        query = self._s2_query(identifier_type, canonical, extracted)

        if query:
            paper = await client.get_paper(query)
            return [self._format_s2_candidate(paper, identifier_type)] if paper else []
        if identifier_type == "title" and canonical:
            papers = await client.search_papers(canonical, limit=limit)
            return [self._format_s2_candidate(paper, identifier_type) for paper in papers]
        return []

    def _s2_query(
        self,
        identifier_type: str,
        canonical: str,
        extracted: dict[str, str],
    ) -> str:
        if doi := extracted.get("doi") or (canonical if identifier_type == "doi" else ""):
            return f"DOI:{doi}"
        if arxiv_id := extracted.get("arxiv") or (
            canonical if identifier_type == "arxiv" else ""
        ):
            return f"arXiv:{arxiv_id}"
        if pmid := extracted.get("pmid") or (canonical if identifier_type == "pmid" else ""):
            return f"PMID:{pmid}"
        if pmcid := extracted.get("pmcid") or (
            canonical if identifier_type == "pmcid" else ""
        ):
            return f"PMCID:{pmcid}"
        if identifier_type == "semantic_scholar" and canonical:
            return canonical
        return ""

    @staticmethod
    def _format_openalex_candidate(
        work: dict[str, Any],
        match_type: str,
    ) -> dict[str, Any]:
        ids = work.get("ids") or {}
        doi = normalize_doi(work.get("doi") or ids.get("doi") or "")
        return {
            "source": "openalex",
            "external_id": (work.get("id") or "").rstrip("/").split("/")[-1],
            "title": work.get("display_name") or work.get("title"),
            "doi": doi,
            "arxiv_id": ids.get("arxiv"),
            "pmid": ids.get("pmid"),
            "pmcid": ids.get("pmcid"),
            "url": work.get("id"),
            "year": work.get("publication_year"),
            "citation_count": work.get("cited_by_count"),
            "match_type": match_type,
            "confidence": 0.9 if match_type != "title" else 0.75,
        }

    @staticmethod
    def _format_s2_candidate(
        paper: dict[str, Any],
        match_type: str,
    ) -> dict[str, Any]:
        ext_ids = paper.get("externalIds") or {}
        paper_id = paper.get("paperId")
        return {
            "source": "semantic_scholar",
            "external_id": paper_id,
            "title": paper.get("title"),
            "doi": normalize_doi(ext_ids.get("DOI") or ""),
            "arxiv_id": ext_ids.get("ArXiv"),
            "pmid": ext_ids.get("PubMed"),
            "pmcid": ext_ids.get("PubMedCentral"),
            "url": f"https://www.semanticscholar.org/paper/{paper_id}"
            if paper_id
            else None,
            "year": paper.get("year"),
            "citation_count": paper.get("citationCount"),
            "match_type": match_type,
            "confidence": 0.9 if match_type != "title" else 0.75,
        }

    @staticmethod
    def _dedupe_external_candidates(
        candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        seen: set[tuple[str, str]] = set()
        deduped: list[dict[str, Any]] = []
        for candidate in candidates:
            key_value = (
                candidate.get("doi")
                or candidate.get("external_id")
                or candidate.get("title")
                or ""
            )
            key = (candidate.get("source") or "unknown", str(key_value).lower())
            if key in seen:
                continue
            seen.add(key)
            deduped.append(candidate)
        return deduped

    @staticmethod
    def _duplicate_confidence(
        local_match: dict[str, Any] | None,
        external_candidates: list[dict[str, Any]],
    ) -> float:
        if local_match:
            return float(local_match.get("confidence") or 1.0)
        if external_candidates:
            return max(
                float(candidate.get("confidence") or 0.0)
                for candidate in external_candidates
            )
        return 0.0

    @staticmethod
    def _import_status(
        local_match: dict[str, Any] | None,
        external_candidates: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if local_match:
            return {
                "state": "existing",
                "paper_id": local_match["paper_id"],
                "ingestion_status": local_match.get("ingestion_status"),
            }
        if len(external_candidates) == 1:
            return {"state": "ready_to_import"}
        if len(external_candidates) > 1:
            return {"state": "ambiguous", "candidate_count": len(external_candidates)}
        return {"state": "not_found"}

    @staticmethod
    def _recommended_action(
        local_match: dict[str, Any] | None,
        external_candidates: list[dict[str, Any]],
    ) -> str:
        if local_match:
            return "open_local"
        if len(external_candidates) == 1:
            return "import"
        if len(external_candidates) > 1:
            return "review_candidates"
        return "provide_more_metadata"
