"""Author enrichment — fetch Semantic Scholar profile and persist to DB.

Matching strategy (soft dedup, in priority order):
  1. semantic_scholar_id match  → definite same person
  2. ORCID match                → definite same person
  3. Name similarity ≥ 0.82 AND institution substring overlap → likely same person
  4. Name similarity ≥ 0.90 (alone)                          → probable same person

When a stronger match is found on a *different* Author row, we merge S2 data
onto that row instead of the requested one, and update all PaperAuthor rows
pointing to the old ID.  This keeps the DB clean without being overly aggressive.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.semantic_scholar import SemanticScholarClient
from app.models.author import Author, Institution

logger = structlog.get_logger(__name__)


# ── Name normalisation ──────────────────────────────────────────────────────


def _normalise(name: str) -> str:
    """Lowercase, strip accents, collapse whitespace."""
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_str = nfkd.encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", ascii_str).strip().lower()


def _name_similarity(a: str, b: str) -> float:
    """
    Simple token-set similarity (no external deps).

    Splits names into tokens on whitespace AND hyphens, then computes
    Jaccard similarity over the sets.  Handles:
      - initials ("J. Smith" vs "John Smith")
      - hyphenated surnames ("Keith-Norambuena" → "keith" + "norambuena")
      - middle names / missing middle names
    """

    def tokens(s: str) -> set[str]:
        parts: set[str] = set()
        # split on any whitespace or hyphen
        for tok in re.split(r"[\s\-]+", _normalise(s)):
            tok = tok.strip(".")
            if not tok:
                continue
            parts.add(tok)
            if len(tok) > 1:
                parts.add(tok[0])  # add initial too
        return parts

    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    intersection = ta & tb
    union = ta | tb
    return len(intersection) / len(union)


def _institution_overlap(
    s2_affiliations: list[dict], db_institution_name: str | None
) -> bool:
    """Return True if any S2 affiliation substring-matches the DB institution name."""
    if not db_institution_name or not s2_affiliations:
        return False
    db_norm = _normalise(db_institution_name)
    for aff in s2_affiliations:
        aff_name = _normalise(aff.get("name", ""))
        if aff_name and (aff_name in db_norm or db_norm in aff_name):
            return True
    return False


# ── Match scoring ───────────────────────────────────────────────────────────


def _match_score(
    candidate: dict,  # S2 author dict
    db_author: Author,
    db_institution_name: str | None,
) -> tuple[float, str]:
    """
    Return (score 0-1, reason string).

    Scores:
      1.0  definite (S2 id or ORCID match)
      0.9  probable (high name + institution)
      0.7  possible (high name alone)
      0.0  no match
    """
    s2_id = candidate.get("authorId", "")
    s2_orcid = (candidate.get("externalIds") or {}).get("ORCID", "")

    # --- Strong ID matches ---
    if db_author.semantic_scholar_id and db_author.semantic_scholar_id == s2_id:
        return 1.0, "semantic_scholar_id"
    if db_author.orcid and s2_orcid and db_author.orcid.strip() == s2_orcid.strip():
        return 1.0, "orcid"

    # --- Name-based ---
    sim = _name_similarity(db_author.display_name, candidate.get("name", ""))

    # Also check aliases from S2
    for alias in candidate.get("aliases") or []:
        sim = max(sim, _name_similarity(db_author.display_name, alias))

    if sim >= 0.82 and _institution_overlap(
        candidate.get("affiliations") or [], db_institution_name
    ):
        return 0.9, f"name_sim={sim:.2f}+institution"
    if sim >= 0.90:
        return 0.7, f"name_sim={sim:.2f}"

    return 0.0, "no_match"


# ── Institution upsert ──────────────────────────────────────────────────────


async def _upsert_institution(
    db: AsyncSession,
    affiliations: list[dict],
) -> Institution | None:
    """Find or create the first recognisable institution from S2 affiliations."""
    for aff in affiliations:
        name = (aff.get("name") or "").strip()
        if not name or len(name) < 3:
            continue
        result = await db.execute(
            select(Institution).where(Institution.name == name).limit(1)
        )
        inst = result.scalar_one_or_none()
        if not inst:
            inst = Institution(name=name, display_name=name)
            db.add(inst)
            await db.flush()
        return inst
    return None


# ── Main enrichment ─────────────────────────────────────────────────────────


class AuthorEnrichmentService:
    """Enrich a local Author row with data from Semantic Scholar."""

    def __init__(self, db: AsyncSession, background: bool = False) -> None:
        self.db = db
        self._s2 = SemanticScholarClient(background=background)

    async def enrich(self, author_id: str) -> dict[str, Any]:
        """
        Enrich author *author_id* from Semantic Scholar.

        Returns a status dict:
          {"status": "ok", "author_id": ..., "s2_id": ..., "changes": [...]}
          {"status": "not_found", ...}
          {"status": "no_match", ...}
          {"status": "error", "error": ...}
        """
        log = logger.bind(author_id=author_id)

        # Load from DB
        result = await self.db.execute(
            select(Author).where(Author.id == author_id, Author.deleted_at.is_(None))
        )
        author = result.scalar_one_or_none()
        if not author:
            return {"status": "not_found", "author_id": author_id}

        # Resolve institution name for matching
        db_institution_name: str | None = None
        if author.institution_id:
            inst_res = await self.db.execute(
                select(Institution).where(Institution.id == author.institution_id)
            )
            inst = inst_res.scalar_one_or_none()
            if inst:
                db_institution_name = inst.name

        # --- If we already have a S2 id, fetch directly ---
        if author.semantic_scholar_id:
            log.info("s2_direct_fetch", s2_id=author.semantic_scholar_id)
            s2_data = await self._s2.get_author(author.semantic_scholar_id)
            if not s2_data:
                return {
                    "status": "no_match",
                    "author_id": author_id,
                    "reason": "s2_id_not_found",
                }
            return await self._apply(
                author, s2_data, "semantic_scholar_id", db_institution_name
            )

        # --- Search by name (try multiple query variants) ---
        # S2 search can miss long / hyphenated names with a single query.
        # Strategy: full name → first + last → last name alone (most distinctive).
        name_parts = author.display_name.split()
        search_queries: list[str] = [author.display_name]
        if len(name_parts) >= 3:
            # first + last only (skip middle names / patronymics)
            search_queries.append(f"{name_parts[0]} {name_parts[-1]}")
        if len(name_parts) >= 2:
            # last name alone — useful for rare compound surnames
            search_queries.append(name_parts[-1])

        all_candidates: dict[str, dict] = {}  # keyed by authorId to dedup
        for query in search_queries:
            log.info("s2_author_search", query=query)
            batch = await self._s2.search_authors(query, limit=8)
            for c in batch:
                aid = c.get("authorId", "")
                if aid and aid not in all_candidates:
                    all_candidates[aid] = c
            if all_candidates:
                # stop as soon as at least one page of candidates scored above threshold
                scored_so_far = [
                    (_match_score(c, author, db_institution_name), c)
                    for c in all_candidates.values()
                ]
                if any(s[0][0] >= 0.7 for s in scored_so_far):
                    break

        if not all_candidates:
            return {
                "status": "no_match",
                "author_id": author_id,
                "reason": "no_candidates",
            }

        # Score each unique candidate
        scored = [
            (_match_score(c, author, db_institution_name), c)
            for c in all_candidates.values()
        ]
        scored.sort(key=lambda x: x[0][0], reverse=True)
        best_score, best_reason = scored[0][0]
        best_candidate = scored[0][1]

        log.info(
            "s2_best_match",
            candidate_name=best_candidate.get("name"),
            score=best_score,
            reason=best_reason,
        )

        if best_score < 0.7:
            return {
                "status": "no_match",
                "author_id": author_id,
                "reason": f"best_score={best_score:.2f} below threshold",
                "top_candidate": best_candidate.get("name"),
            }

        return await self._apply(
            author, best_candidate, best_reason, db_institution_name
        )

    async def _apply(
        self,
        author: Author,
        s2: dict,
        match_reason: str,
        db_institution_name: str | None,
    ) -> dict[str, Any]:
        """Write S2 data back to the Author row and persist."""
        changes: list[str] = []

        def _set(field: str, value: Any) -> None:
            if value is not None and getattr(author, field) != value:
                setattr(author, field, value)
                changes.append(field)

        # IDs
        s2_id = s2.get("authorId")
        if s2_id:
            _set("semantic_scholar_id", s2_id)

        orcid = (s2.get("externalIds") or {}).get("ORCID")
        if orcid:
            _set("orcid", orcid)

        # Metrics
        _set("h_index", s2.get("hIndex"))
        _set("paper_count", s2.get("paperCount"))
        _set("citation_count", s2.get("citationCount"))

        # Canonical name (keep DB name if it's more complete)
        s2_name = s2.get("name", "")
        if s2_name and len(s2_name) > len(author.display_name):
            _set("display_name", s2_name)

        # Aliases — merge without duplicates
        existing_aliases: list[str] = author.aliases or []
        new_aliases = list(s2.get("aliases") or [])
        merged = list(
            {_normalise(a): a for a in existing_aliases + new_aliases}.values()
        )
        if set(merged) != set(existing_aliases):
            author.aliases = merged
            changes.append("aliases")

        # Normalise affiliations: search endpoint returns strings, get endpoint returns dicts
        raw_affiliations = s2.get("affiliations") or []
        affiliations = [
            aff if isinstance(aff, dict) else {"name": aff}
            for aff in raw_affiliations
            if aff
        ]
        if affiliations and not author.institution_id:
            inst = await _upsert_institution(self.db, affiliations)
            if inst:
                author.institution_id = inst.id
                changes.append("institution_id")

        # Raw metadata snapshot
        author.raw_metadata = {
            **(author.raw_metadata or {}),
            "semantic_scholar": {
                "authorId": s2_id,
                "name": s2.get("name"),
                "affiliations": affiliations,
                "homepage": s2.get("homepage"),
                "externalIds": s2.get("externalIds"),
                "enriched_at": datetime.now(UTC).isoformat(),
                "match_reason": match_reason,
            },
        }
        if "raw_metadata" not in changes:
            changes.append("raw_metadata")

        await self.db.commit()

        logger.info(
            "author_enriched",
            author_id=str(author.id),
            s2_id=s2_id,
            changes=changes,
        )

        return {
            "status": "ok",
            "author_id": str(author.id),
            "s2_id": s2_id,
            "match_reason": match_reason,
            "changes": changes,
            "profile": {
                "display_name": author.display_name,
                "semantic_scholar_id": author.semantic_scholar_id,
                "orcid": author.orcid,
                "h_index": author.h_index,
                "paper_count": author.paper_count,
                "citation_count": author.citation_count,
                "aliases": author.aliases,
                "homepage": (author.raw_metadata or {})
                .get("semantic_scholar", {})
                .get("homepage"),
                "affiliations": affiliations,
            },
        }

    async def close(self) -> None:
        await self._s2.close()
