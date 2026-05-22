"""ClaimDependencyService — models which claims depend on which other claims being true."""

import re
import uuid
from collections import deque

import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim_ledger import ClaimRelation, GlobalClaim, ClaimMention
from app.services.claim_ledger_service import ClaimLedgerService, SIMILARITY_RELATED

logger = structlog.get_logger(__name__)

DEPENDENCY_INDICATORS = [
    "depends on", "depend on", "requires", "require ",
    "assumes", "assume ", "relies on", "rely on",
    "contingent on", "presupposes", "presuppose ",
    "given that", "conditional on", "predicated on",
    "building on", "built on", "based on",
    "derived from", "follows from", "follow from",
    "if ", "only if", "under the assumption",
    "mediated by", "driven by", "enabled by",
    "because", "since ", "due to",
    "leveraging", "exploiting", "utilizing",
]

CAUSAL_INDICATORS = [
    "causes", "leads to", "results in", "produces", "enables",
    "triggers", "drives", "implies", "entails", "necessitates",
]


class ClaimDependencyService:
    """Manages claim dependency edges and impact analysis."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._ledger = ClaimLedgerService(db)

    async def detect_dependencies(
        self,
        claim_id: str,
        *,
        max_candidates: int = 10,
        min_confidence: float = 0.60,
    ) -> dict:
        """Detect what a claim depends on by checking semantic neighbors and heuristics."""
        result = await self.db.execute(
            select(GlobalClaim).where(GlobalClaim.id == uuid.UUID(claim_id))
        )
        claim = result.scalar_one_or_none()
        if not claim:
            return {"error": "Claim not found"}

        embedding = await self._ledger._embed_claim(claim.normalized_text)
        matches = await self._ledger._find_semantic_matches(embedding, limit=max_candidates)

        candidates = []
        for m in matches:
            if m["id"] == claim_id:
                continue
            candidates.append(m)

        if not candidates:
            return {"claim_id": claim_id, "dependencies_found": 0, "dependencies": []}

        candidate_ids = [uuid.UUID(c["id"]) for c in candidates]
        claims_q = await self.db.execute(
            select(GlobalClaim).where(GlobalClaim.id.in_(candidate_ids))
        )
        candidate_claims = {str(c.id): c for c in claims_q.scalars().all()}

        dependencies = []
        claim_lower = claim.canonical_text.lower()

        for cand in candidates:
            cand_claim = candidate_claims.get(cand["id"])
            if not cand_claim or cand_claim.status == "rejected":
                continue

            cand_lower = cand_claim.canonical_text.lower()
            relation, direction, confidence, rationale = self._classify_dependency(
                claim_lower, cand_lower, cand["score"]
            )

            if relation and confidence >= min_confidence:
                if direction == "depends_on":
                    source_id = uuid.UUID(claim_id)
                    target_id = uuid.UUID(cand["id"])
                elif direction == "depended_by":
                    source_id = uuid.UUID(cand["id"])
                    target_id = uuid.UUID(claim_id)
                else:
                    continue

                existing = await self.db.execute(
                    select(ClaimRelation).where(
                        ClaimRelation.source_claim_id == source_id,
                        ClaimRelation.target_claim_id == target_id,
                        ClaimRelation.relation == "depends_on",
                    )
                )
                if not existing.scalar_one_or_none():
                    rel = ClaimRelation(
                        source_claim_id=source_id,
                        target_claim_id=target_id,
                        relation="depends_on",
                        confidence=confidence,
                        method="heuristic",
                        rationale=rationale,
                    )
                    self.db.add(rel)
                    dependencies.append({
                        "source_claim_id": str(source_id),
                        "target_claim_id": str(target_id),
                        "target_text": cand_claim.canonical_text[:100],
                        "confidence": confidence,
                        "rationale": rationale,
                    })

        if dependencies:
            await self.db.commit()

        return {
            "claim_id": claim_id,
            "claim_text": claim.canonical_text[:100],
            "dependencies_found": len(dependencies),
            "dependencies": dependencies,
        }

    def _classify_dependency(
        self, claim_a: str, claim_b: str, similarity: float
    ) -> tuple[str | None, str | None, float, str]:
        """Classify whether A depends on B, B depends on A, or neither."""
        a_depends_on_b = 0.0
        b_depends_on_a = 0.0
        rationale_parts = []

        for indicator in DEPENDENCY_INDICATORS:
            if indicator in claim_a:
                fragment_after = claim_a.split(indicator, 1)[1][:80]
                words_b = set(claim_b.split())
                overlap = sum(1 for w in fragment_after.split() if w in words_b and len(w) > 3)
                if overlap >= 2:
                    a_depends_on_b += 0.3
                    rationale_parts.append(f"A contains '{indicator}' referencing B concepts")

        for indicator in DEPENDENCY_INDICATORS:
            if indicator in claim_b:
                fragment_after = claim_b.split(indicator, 1)[1][:80]
                words_a = set(claim_a.split())
                overlap = sum(1 for w in fragment_after.split() if w in words_a and len(w) > 3)
                if overlap >= 2:
                    b_depends_on_a += 0.3
                    rationale_parts.append(f"B contains '{indicator}' referencing A concepts")

        for indicator in CAUSAL_INDICATORS:
            if indicator in claim_a:
                fragment_after = claim_a.split(indicator, 1)[1][:80]
                words_b = set(claim_b.split())
                overlap = sum(1 for w in fragment_after.split() if w in words_b and len(w) > 3)
                if overlap >= 2:
                    b_depends_on_a += 0.25
                    rationale_parts.append(f"A causes/leads to B")

            if indicator in claim_b:
                fragment_after = claim_b.split(indicator, 1)[1][:80]
                words_a = set(claim_a.split())
                overlap = sum(1 for w in fragment_after.split() if w in words_a and len(w) > 3)
                if overlap >= 2:
                    a_depends_on_b += 0.25
                    rationale_parts.append(f"B causes/leads to A")

        if similarity > 0.75:
            specificity_a = len(claim_a.split())
            specificity_b = len(claim_b.split())
            if specificity_a > specificity_b * 1.3:
                a_depends_on_b += 0.15
                rationale_parts.append("A is more specific (likely derived from B)")
            elif specificity_b > specificity_a * 1.3:
                b_depends_on_a += 0.15
                rationale_parts.append("B is more specific (likely derived from A)")

        if a_depends_on_b > b_depends_on_a and a_depends_on_b >= 0.25:
            return "depends_on", "depends_on", min(0.95, a_depends_on_b + similarity * 0.3), "; ".join(rationale_parts)
        elif b_depends_on_a > a_depends_on_b and b_depends_on_a >= 0.25:
            return "depends_on", "depended_by", min(0.95, b_depends_on_a + similarity * 0.3), "; ".join(rationale_parts)

        return None, None, 0.0, ""

    async def get_upstream_premises(
        self, claim_id: str, *, depth: int = 2
    ) -> dict:
        """Get all claims that this claim depends on (prerequisites), up to N hops."""
        visited = set()
        queue = deque([(claim_id, 0)])
        premises = []

        while queue:
            current_id, current_depth = queue.popleft()
            if current_id in visited or current_depth > depth:
                continue
            visited.add(current_id)

            rels = await self.db.execute(
                select(ClaimRelation).where(
                    ClaimRelation.source_claim_id == uuid.UUID(current_id),
                    ClaimRelation.relation == "depends_on",
                )
            )
            for rel in rels.scalars().all():
                target_id = str(rel.target_claim_id)
                if target_id not in visited:
                    claim_q = await self.db.execute(
                        select(GlobalClaim).where(GlobalClaim.id == rel.target_claim_id)
                    )
                    target_claim = claim_q.scalar_one_or_none()
                    if target_claim:
                        premises.append({
                            "claim_id": target_id,
                            "text": target_claim.canonical_text[:120],
                            "depth": current_depth + 1,
                            "confidence": rel.confidence,
                            "evidence_strength": target_claim.evidence_strength_score,
                            "status": target_claim.status,
                        })
                        queue.append((target_id, current_depth + 1))

        return {
            "claim_id": claim_id,
            "upstream_premises": premises,
            "total": len(premises),
            "max_depth_reached": max((p["depth"] for p in premises), default=0),
        }

    async def get_downstream_impacts(
        self, claim_id: str, *, depth: int = 2
    ) -> dict:
        """Get all claims that depend on this claim (what breaks if this claim falls)."""
        visited = set()
        queue = deque([(claim_id, 0)])
        impacts = []

        while queue:
            current_id, current_depth = queue.popleft()
            if current_id in visited or current_depth > depth:
                continue
            visited.add(current_id)

            rels = await self.db.execute(
                select(ClaimRelation).where(
                    ClaimRelation.target_claim_id == uuid.UUID(current_id),
                    ClaimRelation.relation == "depends_on",
                )
            )
            for rel in rels.scalars().all():
                source_id = str(rel.source_claim_id)
                if source_id not in visited:
                    claim_q = await self.db.execute(
                        select(GlobalClaim).where(GlobalClaim.id == rel.source_claim_id)
                    )
                    source_claim = claim_q.scalar_one_or_none()
                    if source_claim:
                        impacts.append({
                            "claim_id": source_id,
                            "text": source_claim.canonical_text[:120],
                            "depth": current_depth + 1,
                            "confidence": rel.confidence,
                            "evidence_strength": source_claim.evidence_strength_score,
                            "status": source_claim.status,
                        })
                        queue.append((source_id, current_depth + 1))

        return {
            "claim_id": claim_id,
            "downstream_impacts": impacts,
            "total": len(impacts),
            "max_depth_reached": max((p["depth"] for p in impacts), default=0),
        }

    async def get_fragility_report(self, claim_id: str) -> dict:
        """Assess how fragile a claim is based on its dependency chain."""
        result = await self.db.execute(
            select(GlobalClaim).where(GlobalClaim.id == uuid.UUID(claim_id))
        )
        claim = result.scalar_one_or_none()
        if not claim:
            return {"error": "Claim not found"}

        upstream = await self.get_upstream_premises(claim_id, depth=3)
        downstream = await self.get_downstream_impacts(claim_id, depth=3)

        premises = upstream["upstream_premises"]
        weak_premises = [p for p in premises if (p.get("evidence_strength") or 0) < 30]
        disputed_premises = [p for p in premises if p.get("status") == "disputed"]

        dependency_depth = upstream["max_depth_reached"]
        downstream_count = downstream["total"]

        fragility_score = (
            len(weak_premises) * 15
            + len(disputed_premises) * 25
            + max(0, dependency_depth - 1) * 5
        )
        fragility_score = min(100, fragility_score)

        own_strength = claim.evidence_strength_score or 0
        criticality_score = round(own_strength * (1 + downstream_count * 0.5), 1)

        return {
            "claim_id": claim_id,
            "claim_text": claim.canonical_text[:120],
            "evidence_strength": own_strength,
            "fragility_score": fragility_score,
            "criticality_score": criticality_score,
            "dependency_depth": dependency_depth,
            "upstream_count": len(premises),
            "downstream_count": downstream_count,
            "weak_premises": weak_premises[:5],
            "disputed_premises": disputed_premises[:5],
            "risk_summary": self._risk_summary(fragility_score, criticality_score, weak_premises, disputed_premises),
        }

    def _risk_summary(self, fragility, criticality, weak, disputed) -> str:
        parts = []
        if fragility > 60:
            parts.append("HIGH FRAGILITY: this claim rests on weak or disputed foundations")
        elif fragility > 30:
            parts.append("MODERATE FRAGILITY: some upstream premises need stronger evidence")
        else:
            parts.append("LOW FRAGILITY: upstream premises are reasonably well-supported")

        if criticality > 100:
            parts.append(f"HIGH CRITICALITY: {criticality:.0f} impact score — many downstream claims depend on this")
        elif criticality > 50:
            parts.append(f"MODERATE CRITICALITY: some downstream claims would be affected if this falls")

        if weak:
            parts.append(f"WEAK PREMISES ({len(weak)}): {weak[0]['text'][:60]}...")
        if disputed:
            parts.append(f"DISPUTED PREMISES ({len(disputed)}): {disputed[0]['text'][:60]}...")

        return "; ".join(parts)

    async def build_dependency_map(
        self, dossier_id: str, *, max_claims: int = 50
    ) -> dict:
        """Build a full dependency map for all claims in a dossier."""
        mentions_q = await self.db.execute(
            select(ClaimMention.global_claim_id).where(
                ClaimMention.dossier_id == uuid.UUID(dossier_id)
            ).distinct()
        )
        claim_ids = [row[0] for row in mentions_q.all()]

        if not claim_ids:
            return {"dossier_id": dossier_id, "nodes": [], "edges": [], "stats": {}}

        claims_q = await self.db.execute(
            select(GlobalClaim).where(
                GlobalClaim.id.in_(claim_ids[:max_claims]),
                GlobalClaim.status != "rejected",
            )
        )
        claims = claims_q.scalars().all()

        nodes = []
        for c in claims:
            nodes.append({
                "id": str(c.id),
                "text": c.canonical_text[:100],
                "evidence_strength": c.evidence_strength_score,
                "status": c.status,
                "support_count": c.support_count,
            })

        all_ids = [c.id for c in claims]
        rels_q = await self.db.execute(
            select(ClaimRelation).where(
                ClaimRelation.relation == "depends_on",
                (ClaimRelation.source_claim_id.in_(all_ids)) |
                (ClaimRelation.target_claim_id.in_(all_ids)),
            )
        )
        relations = rels_q.scalars().all()

        edges = []
        for r in relations:
            edges.append({
                "source": str(r.source_claim_id),
                "target": str(r.target_claim_id),
                "confidence": r.confidence,
                "rationale": r.rationale,
            })

        root_ids = set(str(c.id) for c in claims) - set(e["source"] for e in edges)
        leaf_ids = set(str(c.id) for c in claims) - set(e["target"] for e in edges)

        return {
            "dossier_id": dossier_id,
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_claims": len(nodes),
                "total_edges": len(edges),
                "root_premises": len(root_ids),
                "leaf_conclusions": len(leaf_ids),
                "avg_depth": round(len(edges) / max(len(nodes), 1), 2),
            },
        }

    async def backfill_dependencies(self, dossier_id: str | None = None) -> dict:
        """Detect dependencies for all claims, optionally scoped to a dossier."""
        if dossier_id:
            mentions_q = await self.db.execute(
                select(ClaimMention.global_claim_id).where(
                    ClaimMention.dossier_id == uuid.UUID(dossier_id)
                ).distinct()
            )
            claim_ids = [str(row[0]) for row in mentions_q.all()]
        else:
            claims_q = await self.db.execute(
                select(GlobalClaim.id).where(GlobalClaim.status != "rejected")
            )
            claim_ids = [str(row[0]) for row in claims_q.all()]

        total_deps = 0
        results = []
        for cid in claim_ids:
            r = await self.detect_dependencies(cid)
            if r.get("dependencies_found", 0) > 0:
                total_deps += r["dependencies_found"]
                results.append({
                    "claim_id": cid,
                    "deps_found": r["dependencies_found"],
                })

        return {
            "claims_processed": len(claim_ids),
            "dependencies_created": total_deps,
            "claims_with_deps": len(results),
            "details": results[:20],
        }
