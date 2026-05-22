"""QuestionResolutionService — Question-to-Thesis Compiler.

Takes a research question and returns a defended answer object with:
- provisional thesis
- supporting/contradicting/qualifying claims
- confidence and fragility
- missing evidence
- next best action
"""

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim_ledger import GlobalClaim, ClaimMention, ClaimRelation

logger = structlog.get_logger(__name__)

DECOMPOSE_SYSTEM = """You are a research question decomposer. Given a research question, decompose it into 1-3 testable claims that, if resolved, would answer the question.

Rules:
- Each claim must be atomic, falsifiable, and 25-200 characters
- Claims should cover the key aspects of the question
- Include the main thesis claim and any critical sub-claims

Output JSON:
{
  "thesis": "the main claim that directly answers the question",
  "sub_claims": ["supporting claim 1", "supporting claim 2"],
  "answer_mode": "binary|spectrum|conditional"
}"""

DECOMPOSE_PROMPT = """Research question: {question}

Decompose into testable claims. Return ONLY valid JSON."""

SYNTHESIS_SYSTEM = """You are a research synthesis engine. Given a question, supporting evidence, contradicting evidence, and qualifiers, produce a concise defended answer.

Output JSON:
{
  "answer": "1-3 sentence direct answer to the question",
  "confidence_rationale": "why the confidence level is what it is",
  "key_caveat": "the single most important limitation or condition"
}"""

SYNTHESIS_PROMPT = """Question: {question}

Supporting evidence ({support_count} claims):
{supports}

Contradicting evidence ({contradict_count} claims):
{contradicts}

Qualifiers ({qualify_count} claims):
{qualifiers}

Overall confidence: {confidence}

Synthesize a defended answer. Return ONLY valid JSON."""


class QuestionResolutionService:
    """Compiles a research question into a defended thesis with live uncertainty."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def resolve_question(
        self,
        question: str,
        *,
        dossier_id: str | None = None,
        budget_papers: int = 6,
        resolve_claims: bool = True,
        target_confidence: float = 0.7,
    ) -> dict:
        """Full question resolution pipeline."""
        import json
        import re

        from app.clients.llm_client import LLMClient
        llm = LLMClient()

        raw = await llm.complete(
            prompt=DECOMPOSE_PROMPT.format(question=question),
            system=DECOMPOSE_SYSTEM,
            max_tokens=512,
            temperature=0.1,
        )
        decomposition = self._parse_json(raw)
        thesis_text = decomposition.get("thesis", question)
        sub_claims = decomposition.get("sub_claims", [])
        answer_mode = decomposition.get("answer_mode", "binary")

        all_target_texts = [thesis_text] + sub_claims

        from app.services.claim_ledger_service import ClaimLedgerService
        ledger = ClaimLedgerService(self.db)

        matched_claims = []
        for text in all_target_texts:
            result = await ledger.upsert_claim(
                text=text,
                dossier_id=dossier_id,
                source_tool="question_compiler",
            )
            if result and not result.get("error"):
                claims = result.get("claims", [])
                if claims:
                    for c in claims:
                        cid = c.get("claim_id") or c.get("global_claim_id")
                        if cid:
                            matched_claims.append(cid)
                elif result.get("claim_id") or result.get("global_claim_id"):
                    matched_claims.append(str(result.get("claim_id") or result.get("global_claim_id")))

        if not matched_claims:
            return {
                "question": question,
                "status": "no_claims_generated",
                "answer": None,
                "confidence": 0,
            }

        thesis_claim_id = matched_claims[0]

        if resolve_claims:
            from app.services.claim_resolution_service import ClaimResolutionService
            resolver = ClaimResolutionService(self.db)

            per_claim_budget = max(2, budget_papers // len(matched_claims))
            for cid in matched_claims[:3]:
                try:
                    await resolver.resolve_claim(
                        cid,
                        objective="strengthen",
                        budget_papers=per_claim_budget,
                        dossier_id=dossier_id,
                    )
                except Exception as e:
                    logger.warning("claim_resolution_error", claim_id=cid, error=str(e))

        claim_objects = []
        for cid in matched_claims:
            result = await self.db.execute(
                select(GlobalClaim).where(GlobalClaim.id == uuid.UUID(cid))
            )
            claim = result.scalar_one_or_none()
            if claim:
                claim_objects.append(claim)

        thesis_claim = claim_objects[0] if claim_objects else None

        rels_q = await self.db.execute(
            select(ClaimRelation).where(
                ClaimRelation.target_claim_id.in_([uuid.UUID(c) for c in matched_claims])
            )
        )
        relations = rels_q.scalars().all()

        supporting_ids = set()
        contradicting_ids = set()
        qualifying_ids = set()

        for r in relations:
            if r.relation == "supports":
                supporting_ids.add(r.source_claim_id)
            elif r.relation == "contradicts":
                contradicting_ids.add(r.source_claim_id)
            elif r.relation in ("qualifies", "depends_on"):
                qualifying_ids.add(r.source_claim_id)

        all_evidence_ids = supporting_ids | contradicting_ids | qualifying_ids
        evidence_claims = {}
        if all_evidence_ids:
            ev_q = await self.db.execute(
                select(GlobalClaim).where(GlobalClaim.id.in_(all_evidence_ids))
            )
            for ec in ev_q.scalars().all():
                evidence_claims[ec.id] = ec

        supports = [
            {"claim_id": str(cid), "text": evidence_claims[cid].canonical_text[:120],
             "strength": evidence_claims[cid].evidence_strength_score}
            for cid in supporting_ids if cid in evidence_claims
        ]
        contradicts = [
            {"claim_id": str(cid), "text": evidence_claims[cid].canonical_text[:120],
             "strength": evidence_claims[cid].evidence_strength_score}
            for cid in contradicting_ids if cid in evidence_claims
        ]
        qualifiers = [
            {"claim_id": str(cid), "text": evidence_claims[cid].canonical_text[:120],
             "strength": evidence_claims[cid].evidence_strength_score}
            for cid in qualifying_ids if cid in evidence_claims
        ]

        confidence = self._compute_answer_confidence(thesis_claim, supports, contradicts)

        from app.services.evidence_sufficiency_service import EvidenceSufficiencyService
        suff_svc = EvidenceSufficiencyService(self.db)
        audit = await suff_svc.audit_claim(thesis_claim_id)
        missing_evidence = audit.get("minimum_evidence_needed", [])
        blockers = audit.get("blockers", [])

        from app.services.research_strategy_service import ResearchStrategyService
        strategy = ResearchStrategyService(self.db)
        if dossier_id:
            plan = await strategy.plan_next_actions(
                dossier_id, objective="maximize_certainty", max_actions=1,
                target_claims=[thesis_claim_id],
            )
            next_action = plan.get("actions", [None])[0]
        else:
            next_action = None

        supports_text = "\n".join(f"- {s['text']}" for s in supports[:5]) or "None found"
        contradicts_text = "\n".join(f"- {c['text']}" for c in contradicts[:5]) or "None found"
        qualifiers_text = "\n".join(f"- {q['text']}" for q in qualifiers[:5]) or "None found"

        try:
            synth_raw = await llm.complete(
                prompt=SYNTHESIS_PROMPT.format(
                    question=question,
                    support_count=len(supports),
                    supports=supports_text,
                    contradict_count=len(contradicts),
                    contradicts=contradicts_text,
                    qualify_count=len(qualifiers),
                    qualifiers=qualifiers_text,
                    confidence=f"{confidence:.2f}",
                ),
                system=SYNTHESIS_SYSTEM,
                max_tokens=512,
                temperature=0.2,
            )
            synthesis = self._parse_json(synth_raw)
        except Exception:
            synthesis = {"answer": thesis_text, "confidence_rationale": "", "key_caveat": ""}

        fragility = 0
        if thesis_claim:
            from app.services.claim_dependency_service import ClaimDependencyService
            dep_svc = ClaimDependencyService(self.db)
            frag_report = await dep_svc.get_fragility_report(thesis_claim_id)
            fragility = frag_report.get("fragility_score", 0)

        return {
            "question": question,
            "answer": synthesis.get("answer", thesis_text),
            "confidence": round(confidence, 3),
            "confidence_rationale": synthesis.get("confidence_rationale", ""),
            "key_caveat": synthesis.get("key_caveat", ""),
            "answer_mode": answer_mode,
            "thesis_claim_id": thesis_claim_id,
            "thesis_text": thesis_text,
            "fragility": fragility,
            "supporting_claims": supports,
            "contradicting_claims": contradicts,
            "qualifiers": qualifiers,
            "critical_assumptions": [
                {"claim_id": str(c.id), "text": c.canonical_text[:100],
                 "strength": c.evidence_strength_score}
                for c in claim_objects[1:] if c.evidence_strength_score and c.evidence_strength_score < 40
            ],
            "missing_evidence": missing_evidence[:5],
            "remaining_blockers": [b["type"] for b in blockers[:3]],
            "next_best_action": next_action,
            "trace": {
                "claims_generated": len(matched_claims),
                "claims_resolved": len(matched_claims) if resolve_claims else 0,
                "papers_budget": budget_papers,
                "relations_found": len(relations),
            },
        }

    def _compute_answer_confidence(self, thesis_claim, supports, contradicts) -> float:
        if not thesis_claim:
            return 0.0

        base = (thesis_claim.effective_confidence or thesis_claim.direct_confidence or 0)
        if not base:
            strength = thesis_claim.evidence_strength_score or 0
            base = strength / 100.0 * 0.6

        support_boost = min(0.2, len(supports) * 0.05)
        contradict_penalty = min(0.3, len(contradicts) * 0.1)

        return max(0.0, min(1.0, base + support_boost - contradict_penalty))

    def _parse_json(self, text: str) -> dict:
        import json
        import re
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        fence = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if fence:
            try:
                return json.loads(fence.group(1).strip())
            except json.JSONDecodeError:
                pass
        match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return {}
