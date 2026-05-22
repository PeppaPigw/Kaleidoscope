"""LiteratureGapService — identifies unanswered questions by analyzing claim coverage."""

import uuid
from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim_ledger import ClaimMention, ClaimRelation, GlobalClaim
from app.models.dossier import ResearchDossier

logger = structlog.get_logger(__name__)

GAP_TYPES = {
    "unsupported_leaf": "Claim with no upstream evidence or dependencies — floating assertion",
    "weak_foundation": "Claim with low effective confidence that many others depend on",
    "contradiction_unresolved": "Disputed claim with no resolution or additional evidence",
    "stale_high_impact": "High-impact claim not updated with recent evidence",
    "missing_replication": "Claim supported by single source, no independent confirmation",
    "dead_end_chain": "Dependency chain that terminates in an unverified premise",
}


class LiteratureGapService:
    """Detects literature gaps from claim graph structure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect_gaps(
        self,
        dossier_id: str,
        *,
        max_gaps: int = 20,
        min_gap_score: float = 0.3,
    ) -> dict:
        """Run full gap detection for a dossier. Returns scored, prioritized gaps."""
        mentions_q = await self.db.execute(
            select(ClaimMention.global_claim_id).where(
                ClaimMention.dossier_id == uuid.UUID(dossier_id)
            ).distinct()
        )
        claim_ids = [row[0] for row in mentions_q.all()]

        if not claim_ids:
            return {"dossier_id": dossier_id, "gaps": [], "total": 0, "coverage_score": 0}

        claims_q = await self.db.execute(
            select(GlobalClaim).where(
                GlobalClaim.id.in_(claim_ids),
                GlobalClaim.status != "rejected",
            )
        )
        claims = claims_q.scalars().all()
        claim_map = {c.id: c for c in claims}

        rels_q = await self.db.execute(
            select(ClaimRelation).where(
                ClaimRelation.relation == "depends_on",
                (ClaimRelation.source_claim_id.in_(claim_ids)) |
                (ClaimRelation.target_claim_id.in_(claim_ids)),
            )
        )
        relations = rels_q.scalars().all()

        downstream_map = {}
        upstream_map = {}
        for r in relations:
            downstream_map.setdefault(r.target_claim_id, []).append(r.source_claim_id)
            upstream_map.setdefault(r.source_claim_id, []).append(r.target_claim_id)

        gaps = []

        for claim in claims:
            claim_gaps = self._analyze_claim_gaps(
                claim, claim_map, downstream_map, upstream_map
            )
            gaps.extend(claim_gaps)

        gaps.sort(key=lambda g: g["score"], reverse=True)
        gaps = [g for g in gaps if g["score"] >= min_gap_score][:max_gaps]

        coverage_score = self._compute_coverage_score(claims, gaps)

        await self._persist_gaps(dossier_id, gaps, coverage_score)

        return {
            "dossier_id": dossier_id,
            "gaps": gaps,
            "total": len(gaps),
            "coverage_score": coverage_score,
            "gap_type_counts": self._count_by_type(gaps),
            "suggested_actions": self._suggest_actions(gaps[:5]),
        }

    def _analyze_claim_gaps(
        self,
        claim: GlobalClaim,
        claim_map: dict,
        downstream_map: dict,
        upstream_map: dict,
    ) -> list[dict]:
        """Analyze a single claim for gap signals."""
        gaps = []
        cid = claim.id
        effective = claim.effective_confidence or 0
        direct = claim.direct_confidence or 0
        strength = claim.evidence_strength_score or 0
        support = claim.support_count or 0
        contradict = claim.contradict_count or 0
        downstream_count = len(downstream_map.get(cid, []))
        upstream_count = len(upstream_map.get(cid, []))

        if upstream_count == 0 and strength < 40 and support <= 1:
            score = (1.0 - strength / 100.0) * 0.6 + (0.4 if downstream_count > 0 else 0.2)
            gaps.append(self._make_gap(
                claim, "unsupported_leaf", score,
                f"No upstream evidence, strength={strength}, {downstream_count} claims depend on it",
            ))

        if effective < 0.4 and downstream_count >= 2:
            score = (1.0 - effective) * 0.5 + min(0.4, downstream_count * 0.1)
            gaps.append(self._make_gap(
                claim, "weak_foundation", score,
                f"Effective confidence={effective:.2f}, {downstream_count} downstream claims at risk",
            ))

        if claim.status == "disputed" and contradict > 0:
            score = 0.5 + min(0.4, contradict * 0.15)
            gaps.append(self._make_gap(
                claim, "contradiction_unresolved", score,
                f"{contradict} contradiction(s) with no resolution",
            ))

        if support == 1 and strength > 20 and downstream_count > 0:
            score = 0.4 + min(0.3, downstream_count * 0.1)
            gaps.append(self._make_gap(
                claim, "missing_replication", score,
                f"Single source, {downstream_count} downstream claims depend on it",
            ))

        if upstream_count > 0:
            upstream_ids = upstream_map.get(cid, [])
            unverified_premises = [
                uid for uid in upstream_ids
                if uid in claim_map and (claim_map[uid].evidence_strength_score or 0) < 20
            ]
            if unverified_premises:
                score = 0.4 + min(0.4, len(unverified_premises) * 0.15)
                gaps.append(self._make_gap(
                    claim, "dead_end_chain", score,
                    f"Depends on {len(unverified_premises)} unverified premise(s)",
                ))

        return gaps

    def _make_gap(self, claim: GlobalClaim, gap_type: str, score: float, detail: str) -> dict:
        return {
            "claim_id": str(claim.id),
            "claim_text": claim.canonical_text[:120],
            "gap_type": gap_type,
            "gap_description": GAP_TYPES.get(gap_type, ""),
            "score": round(min(1.0, score), 3),
            "detail": detail,
            "evidence_strength": claim.evidence_strength_score,
            "effective_confidence": claim.effective_confidence,
            "status": claim.status,
        }

    def _compute_coverage_score(self, claims: list, gaps: list) -> int:
        """Compute 0-100 coverage score. Higher = fewer gaps relative to claims."""
        if not claims:
            return 0
        total_claims = len(claims)
        high_severity_gaps = sum(1 for g in gaps if g["score"] > 0.6)
        medium_gaps = sum(1 for g in gaps if 0.3 < g["score"] <= 0.6)

        penalty = high_severity_gaps * 15 + medium_gaps * 5
        score = max(0, 100 - penalty)

        avg_effective = sum(
            (c.effective_confidence or 0.5) for c in claims
        ) / total_claims
        score = int(score * 0.6 + avg_effective * 100 * 0.4)

        return max(0, min(100, score))

    def _count_by_type(self, gaps: list) -> dict:
        counts = {}
        for g in gaps:
            counts[g["gap_type"]] = counts.get(g["gap_type"], 0) + 1
        return counts

    def _suggest_actions(self, top_gaps: list) -> list[str]:
        """Generate actionable research suggestions from top gaps."""
        actions = []
        for gap in top_gaps:
            gt = gap["gap_type"]
            text = gap["claim_text"][:60]
            if gt == "unsupported_leaf":
                actions.append(f"Find supporting evidence for: '{text}...'")
            elif gt == "weak_foundation":
                actions.append(f"Strengthen evidence base for critical premise: '{text}...'")
            elif gt == "contradiction_unresolved":
                actions.append(f"Investigate and resolve contradiction: '{text}...'")
            elif gt == "missing_replication":
                actions.append(f"Find independent replication for: '{text}...'")
            elif gt == "dead_end_chain":
                actions.append(f"Verify unproven premises underlying: '{text}...'")
            elif gt == "stale_high_impact":
                actions.append(f"Update with recent literature: '{text}...'")
        return actions

    async def _persist_gaps(self, dossier_id: str, gaps: list, coverage_score: int):
        """Persist gap analysis results to the dossier."""
        import json
        gap_summary = {
            "last_analyzed": datetime.now(timezone.utc).isoformat(),
            "total_gaps": len(gaps),
            "coverage_score": coverage_score,
            "top_gaps": gaps[:10],
        }
        await self.db.execute(text("""
            UPDATE research_dossiers
            SET gaps = CAST(:gaps AS jsonb),
                coverage_score = :score,
                updated_at = NOW()
            WHERE id = :id
        """), {
            "gaps": json.dumps(gap_summary),
            "score": coverage_score,
            "id": dossier_id,
        })
        await self.db.commit()

    async def get_research_priorities(self, dossier_id: str) -> dict:
        """Get prioritized research actions based on gap analysis."""
        result = await self.detect_gaps(dossier_id)
        gaps = result.get("gaps", [])

        priorities = []
        for i, gap in enumerate(gaps[:10]):
            priority = {
                "rank": i + 1,
                "action": self._suggest_actions([gap])[0] if gap else "",
                "gap_type": gap["gap_type"],
                "severity": "high" if gap["score"] > 0.7 else "medium" if gap["score"] > 0.4 else "low",
                "claim_id": gap["claim_id"],
                "claim_text": gap["claim_text"],
                "expected_impact": self._estimate_impact(gap),
            }
            priorities.append(priority)

        return {
            "dossier_id": dossier_id,
            "coverage_score": result["coverage_score"],
            "priorities": priorities,
            "total_gaps": result["total"],
        }

    def _estimate_impact(self, gap: dict) -> str:
        score = gap["score"]
        if score > 0.7:
            return "Resolving this would significantly strengthen the dossier's evidence base"
        elif score > 0.5:
            return "Addressing this would improve confidence in dependent conclusions"
        else:
            return "Minor improvement to overall coverage"
