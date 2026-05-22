"""ClaimResolutionService — Targeted Claim Resolver.

Takes a specific claim and autonomously resolves it: audit → search → compile → adjudicate → update → cascade.
"""

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim_ledger import GlobalClaim

logger = structlog.get_logger(__name__)

ADJUDICATION_SYSTEM = """You are a scientific evidence adjudicator. Given a TARGET claim and a piece of EXTRACTED evidence, determine the relationship.

Classify as exactly one of:
- "supports": the evidence directly confirms or strengthens the target claim
- "contradicts": the evidence directly challenges or weakens the target claim
- "qualifies": the evidence adds nuance, conditions, or boundary cases to the target claim
- "irrelevant": the evidence has no meaningful bearing on the target claim

Output JSON:
{
  "stance": "supports|contradicts|qualifies|irrelevant",
  "confidence": 0.0-1.0,
  "rationale": "one sentence explaining why"
}"""

ADJUDICATION_PROMPT = """TARGET CLAIM: {target}

EXTRACTED EVIDENCE: {evidence}

Classify the relationship. Return ONLY valid JSON."""

OBJECTIVES = {
    "strengthen": "Find supporting evidence to increase confidence",
    "resolve_contradiction": "Find meta-analysis or comparison study to resolve dispute",
    "refresh_recency": "Find recent (2023+) evidence confirming the claim still holds",
}


class ClaimResolutionService:
    """Autonomously resolves a claim by finding and adjudicating evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def resolve_claim(
        self,
        claim_id: str,
        *,
        objective: str = "strengthen",
        budget_papers: int = 6,
        dossier_id: str | None = None,
    ) -> dict:
        """Full resolution loop for a single claim."""
        result = await self.db.execute(
            select(GlobalClaim).where(GlobalClaim.id == uuid.UUID(claim_id))
        )
        claim = result.scalar_one_or_none()
        if not claim:
            return {"error": "Claim not found"}

        if objective not in OBJECTIVES:
            return {"error": f"Unknown objective. Choose from: {list(OBJECTIVES.keys())}"}

        before_state = {
            "strength": claim.evidence_strength_score or 0,
            "effective_confidence": claim.effective_confidence or 0,
            "direct_confidence": claim.direct_confidence or 0,
            "support_count": claim.support_count or 0,
            "contradict_count": claim.contradict_count or 0,
            "status": claim.status,
        }

        from app.services.evidence_sufficiency_service import EvidenceSufficiencyService
        suff_svc = EvidenceSufficiencyService(self.db)
        audit = await suff_svc.audit_claim(claim_id)
        blockers = audit.get("blockers", [])
        queries = audit.get("recommended_queries", [])

        if not queries:
            queries = [f"evidence {claim.canonical_text[:60]}"]

        if objective == "resolve_contradiction":
            queries = [f"meta-analysis {claim.canonical_text[:60]}",
                       f"systematic review {claim.canonical_text[:60]}"] + queries[:2]
        elif objective == "refresh_recency":
            queries = [f"{claim.canonical_text[:60]} 2024 2025",
                       f"recent study {claim.canonical_text[:60]}"] + queries[:2]

        from app.clients.openalex import OpenAlexClient
        openalex = OpenAlexClient()

        all_papers = []
        for query in queries[:3]:
            try:
                papers = await openalex.search_works(query, rows=3)
                all_papers.extend(papers[:2])
            except Exception as e:
                logger.warning("resolution_search_error", query=query, error=str(e))

        all_papers = all_papers[:budget_papers]
        if not all_papers:
            return {
                "claim_id": claim_id,
                "objective": objective,
                "status": "no_papers_found",
                "before": before_state,
                "after": before_state,
                "evidence_added": [],
                "resolution_report": "No relevant papers found for the given queries.",
            }

        from app.services.claim_compiler_service import ClaimCompilerService
        compiler = ClaimCompilerService(self.db)

        extracted_claims = []
        for paper in all_papers:
            compile_result = await compiler.compile_from_openalex(paper, dossier_id=dossier_id)
            if compile_result.get("claim_ids"):
                for cid in compile_result["claim_ids"]:
                    ec_result = await self.db.execute(
                        select(GlobalClaim).where(GlobalClaim.id == uuid.UUID(cid))
                    )
                    ec = ec_result.scalar_one_or_none()
                    if ec:
                        extracted_claims.append(ec)

        adjudications = []
        for ec in extracted_claims:
            adj = await self._adjudicate(claim, ec)
            if adj and adj["stance"] != "irrelevant":
                adjudications.append(adj)

        supports = [a for a in adjudications if a["stance"] == "supports"]
        contradicts = [a for a in adjudications if a["stance"] == "contradicts"]
        qualifies = [a for a in adjudications if a["stance"] == "qualifies"]

        from app.services.claim_ledger_service import ClaimLedgerService
        ledger = ClaimLedgerService(self.db)

        for adj in adjudications:
            try:
                await ledger.record_relation(
                    source_claim_id=adj["evidence_claim_id"],
                    target_claim_id=claim_id,
                    relation="supports" if adj["stance"] == "supports" else
                             "contradicts" if adj["stance"] == "contradicts" else "qualifies",
                    confidence=adj["confidence"],
                )
            except Exception as e:
                logger.warning("relation_write_error", error=str(e))

        from app.services.evidence_strength_service import EvidenceStrengthService
        strength_svc = EvidenceStrengthService(self.db)
        await strength_svc.score_global_claim(claim_id)

        from app.services.confidence_cascade_service import ConfidenceCascadeService
        cascade_svc = ConfidenceCascadeService(self.db)
        cascade_result = await cascade_svc.update_claim_confidence(claim_id)

        await self.db.commit()

        refreshed = await self.db.execute(
            select(GlobalClaim).where(GlobalClaim.id == uuid.UUID(claim_id))
        )
        updated_claim = refreshed.scalar_one_or_none()

        after_state = {
            "strength": updated_claim.evidence_strength_score or 0,
            "effective_confidence": updated_claim.effective_confidence or 0,
            "direct_confidence": updated_claim.direct_confidence or 0,
            "support_count": updated_claim.support_count or 0,
            "contradict_count": updated_claim.contradict_count or 0,
            "status": updated_claim.status,
        } if updated_claim else before_state

        strength_delta = (after_state["strength"] or 0) - (before_state["strength"] or 0)
        confidence_delta = (after_state["effective_confidence"] or 0) - (before_state["effective_confidence"] or 0)

        return {
            "claim_id": claim_id,
            "claim_text": claim.canonical_text[:150],
            "objective": objective,
            "status": "resolved" if strength_delta > 0 or confidence_delta > 0 else "no_lift",
            "before": before_state,
            "after": after_state,
            "strength_delta": round(strength_delta, 2),
            "confidence_delta": round(confidence_delta, 4),
            "papers_searched": len(all_papers),
            "claims_extracted": len(extracted_claims),
            "adjudications": {
                "supports": len(supports),
                "contradicts": len(contradicts),
                "qualifies": len(qualifies),
                "total": len(adjudications),
            },
            "evidence_added": [
                {
                    "claim_id": a["evidence_claim_id"],
                    "text": a["evidence_text"][:80],
                    "stance": a["stance"],
                    "confidence": a["confidence"],
                    "rationale": a["rationale"],
                }
                for a in adjudications[:10]
            ],
            "remaining_blockers": [b["type"] for b in blockers if b.get("estimated_lift", 0) > 5],
            "cascade_effects": cascade_result if isinstance(cascade_result, dict) else {},
        }

    async def _adjudicate(self, target: GlobalClaim, evidence: GlobalClaim) -> dict | None:
        """Use LLM to classify the relationship between evidence and target claim."""
        from app.clients.llm_client import LLMClient
        import json
        import re

        if target.id == evidence.id:
            return None

        llm = LLMClient()
        try:
            raw = await llm.complete(
                prompt=ADJUDICATION_PROMPT.format(
                    target=target.canonical_text[:200],
                    evidence=evidence.canonical_text[:200],
                ),
                system=ADJUDICATION_SYSTEM,
                max_tokens=256,
                temperature=0.1,
            )

            parsed = self._parse_json(raw)
            stance = parsed.get("stance", "irrelevant")
            if stance not in ("supports", "contradicts", "qualifies", "irrelevant"):
                stance = "irrelevant"

            return {
                "evidence_claim_id": str(evidence.id),
                "evidence_text": evidence.canonical_text,
                "stance": stance,
                "confidence": parsed.get("confidence", 0.5),
                "rationale": parsed.get("rationale", ""),
            }
        except Exception as e:
            logger.warning("adjudication_error", error=str(e))
            return None

    def _parse_json(self, text: str) -> dict:
        import json
        import re
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return {}
