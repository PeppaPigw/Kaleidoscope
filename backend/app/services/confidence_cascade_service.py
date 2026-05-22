"""ConfidenceCascadeService — propagates uncertainty through the claim dependency graph."""

import uuid
from collections import deque
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim_ledger import ClaimConfidenceEvent, ClaimRelation, GlobalClaim

logger = structlog.get_logger(__name__)

MIN_EDGE_CONFIDENCE = 0.70
MAX_CASCADE_DEPTH = 4
MIN_DELTA_THRESHOLD = 0.02


class ConfidenceCascadeService:
    """Propagates confidence changes through the claim dependency graph."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def compute_direct_confidence(self, claim: GlobalClaim) -> float:
        """Compute direct confidence from a claim's own evidence."""
        strength = claim.evidence_strength_score or 0
        support = claim.support_count or 0
        contradict = claim.contradict_count or 0

        if support + contradict == 0:
            return strength / 100.0

        support_ratio = support / (support + contradict)
        base = (strength / 100.0) * 0.6 + support_ratio * 0.4

        if claim.status == "disputed":
            base *= 0.7

        return round(max(0.0, min(1.0, base)), 3)

    def compute_effective_confidence(
        self, direct: float, upstream_factors: list[tuple[float, float]]
    ) -> float:
        """Compute effective confidence after upstream propagation.

        Formula: effective = direct * product(1 - edge_conf * (1 - upstream_effective))
        Each weak upstream premise reduces effective confidence proportionally.
        """
        if not upstream_factors:
            return direct

        product = 1.0
        for edge_confidence, upstream_effective in upstream_factors:
            penalty = edge_confidence * (1.0 - upstream_effective)
            product *= (1.0 - penalty)

        return round(max(0.0, min(1.0, direct * product)), 3)

    async def update_claim_confidence(
        self,
        claim_id: str,
        *,
        trigger_claim_id: str | None = None,
        reason: str = "direct update",
    ) -> dict:
        """Recompute confidence for a claim and cascade to downstream dependents."""
        result = await self.db.execute(
            select(GlobalClaim).where(GlobalClaim.id == uuid.UUID(claim_id))
        )
        claim = result.scalar_one_or_none()
        if not claim:
            return {"error": "Claim not found"}

        old_effective = claim.effective_confidence
        new_direct = self.compute_direct_confidence(claim)
        claim.direct_confidence = new_direct

        upstream_factors = await self._get_upstream_factors(claim_id)
        new_effective = self.compute_effective_confidence(new_direct, upstream_factors)

        claim.effective_confidence = new_effective
        claim.cascade_depth = len(upstream_factors)

        delta = (new_effective - old_effective) if old_effective is not None else 0.0

        event = ClaimConfidenceEvent(
            claim_id=claim.id,
            trigger_claim_id=uuid.UUID(trigger_claim_id) if trigger_claim_id else None,
            event_type="recompute",
            before_confidence=old_effective,
            after_confidence=new_effective,
            delta=round(delta, 4),
            depth=0,
            path=[claim_id],
            reason=reason,
        )
        self.db.add(event)
        await self.db.commit()

        cascade_results = []
        if abs(delta) >= MIN_DELTA_THRESHOLD:
            cascade_results = await self._cascade_downstream(
                claim_id, trigger_claim_id=claim_id, depth=1, path=[claim_id]
            )

        return {
            "claim_id": claim_id,
            "direct_confidence": new_direct,
            "effective_confidence": new_effective,
            "previous_effective": old_effective,
            "delta": round(delta, 4),
            "downstream_affected": len(cascade_results),
            "cascade_events": cascade_results[:10],
        }

    async def _get_upstream_factors(self, claim_id: str) -> list[tuple[float, float]]:
        """Get (edge_confidence, upstream_effective_confidence) for all upstream premises."""
        rels = await self.db.execute(
            select(ClaimRelation).where(
                ClaimRelation.source_claim_id == uuid.UUID(claim_id),
                ClaimRelation.relation == "depends_on",
                ClaimRelation.confidence >= MIN_EDGE_CONFIDENCE,
            )
        )
        factors = []
        for rel in rels.scalars().all():
            upstream_q = await self.db.execute(
                select(GlobalClaim).where(GlobalClaim.id == rel.target_claim_id)
            )
            upstream = upstream_q.scalar_one_or_none()
            if upstream:
                eff = upstream.effective_confidence
                if eff is None:
                    eff = self.compute_direct_confidence(upstream)
                factors.append((rel.confidence, eff))
        return factors

    async def _cascade_downstream(
        self,
        claim_id: str,
        *,
        trigger_claim_id: str,
        depth: int,
        path: list[str],
    ) -> list[dict]:
        """Propagate confidence change to all downstream dependents."""
        if depth > MAX_CASCADE_DEPTH:
            return []

        rels = await self.db.execute(
            select(ClaimRelation).where(
                ClaimRelation.target_claim_id == uuid.UUID(claim_id),
                ClaimRelation.relation == "depends_on",
                ClaimRelation.confidence >= MIN_EDGE_CONFIDENCE,
            )
        )
        events = []
        for rel in rels.scalars().all():
            downstream_id = str(rel.source_claim_id)
            if downstream_id in path:
                continue

            downstream_q = await self.db.execute(
                select(GlobalClaim).where(GlobalClaim.id == rel.source_claim_id)
            )
            downstream = downstream_q.scalar_one_or_none()
            if not downstream:
                continue

            old_effective = downstream.effective_confidence
            new_direct = downstream.direct_confidence or self.compute_direct_confidence(downstream)
            downstream.direct_confidence = new_direct

            upstream_factors = await self._get_upstream_factors(downstream_id)
            new_effective = self.compute_effective_confidence(new_direct, upstream_factors)

            delta = (new_effective - old_effective) if old_effective is not None else 0.0
            downstream.effective_confidence = new_effective
            downstream.cascade_depth = depth

            new_path = path + [downstream_id]
            event = ClaimConfidenceEvent(
                claim_id=downstream.id,
                trigger_claim_id=uuid.UUID(trigger_claim_id),
                event_type="cascade",
                before_confidence=old_effective,
                after_confidence=new_effective,
                delta=round(delta, 4),
                depth=depth,
                path=new_path,
                reason=f"upstream claim {claim_id[:8]} confidence changed",
            )
            self.db.add(event)

            event_info = {
                "claim_id": downstream_id,
                "text": downstream.canonical_text[:80],
                "before": old_effective,
                "after": new_effective,
                "delta": round(delta, 4),
                "depth": depth,
            }
            events.append(event_info)

            if abs(delta) >= MIN_DELTA_THRESHOLD:
                sub_events = await self._cascade_downstream(
                    downstream_id,
                    trigger_claim_id=trigger_claim_id,
                    depth=depth + 1,
                    path=new_path,
                )
                events.extend(sub_events)

        await self.db.commit()
        return events

    async def propagate_dispute(self, claim_id: str) -> dict:
        """Trigger a cascade when a claim becomes disputed."""
        result = await self.db.execute(
            select(GlobalClaim).where(GlobalClaim.id == uuid.UUID(claim_id))
        )
        claim = result.scalar_one_or_none()
        if not claim:
            return {"error": "Claim not found"}

        return await self.update_claim_confidence(
            claim_id,
            trigger_claim_id=claim_id,
            reason="claim disputed — propagating uncertainty",
        )

    async def recompute_all(self, dossier_id: str | None = None) -> dict:
        """Recompute confidence for all claims, optionally scoped to a dossier."""
        if dossier_id:
            from app.models.claim_ledger import ClaimMention
            mentions_q = await self.db.execute(
                select(ClaimMention.global_claim_id).where(
                    ClaimMention.dossier_id == uuid.UUID(dossier_id)
                ).distinct()
            )
            claim_ids = [row[0] for row in mentions_q.all()]
            claims_q = await self.db.execute(
                select(GlobalClaim).where(
                    GlobalClaim.id.in_(claim_ids),
                    GlobalClaim.status != "rejected",
                )
            )
        else:
            claims_q = await self.db.execute(
                select(GlobalClaim).where(GlobalClaim.status != "rejected")
            )

        claims = claims_q.scalars().all()

        updated = []
        for claim in claims:
            new_direct = self.compute_direct_confidence(claim)
            claim.direct_confidence = new_direct

            upstream_factors = await self._get_upstream_factors(str(claim.id))
            new_effective = self.compute_effective_confidence(new_direct, upstream_factors)
            claim.effective_confidence = new_effective
            claim.cascade_depth = len(upstream_factors)

            updated.append({
                "claim_id": str(claim.id),
                "text": claim.canonical_text[:60],
                "direct": new_direct,
                "effective": new_effective,
                "upstream_deps": len(upstream_factors),
            })

        await self.db.commit()

        updated.sort(key=lambda x: x["effective"])
        return {
            "total_recomputed": len(updated),
            "claims": updated,
            "weakest": updated[:5] if updated else [],
            "strongest": updated[-5:] if updated else [],
        }

    async def get_confidence_history(self, claim_id: str, limit: int = 20) -> dict:
        """Get the confidence event history for a claim."""
        events_q = await self.db.execute(
            select(ClaimConfidenceEvent).where(
                ClaimConfidenceEvent.claim_id == uuid.UUID(claim_id)
            ).order_by(ClaimConfidenceEvent.created_at.desc()).limit(limit)
        )
        events = events_q.scalars().all()

        return {
            "claim_id": claim_id,
            "events": [
                {
                    "event_type": e.event_type,
                    "before": e.before_confidence,
                    "after": e.after_confidence,
                    "delta": e.delta,
                    "depth": e.depth,
                    "reason": e.reason,
                    "trigger_claim_id": str(e.trigger_claim_id) if e.trigger_claim_id else None,
                    "created_at": str(e.created_at),
                }
                for e in events
            ],
            "total": len(events),
        }
