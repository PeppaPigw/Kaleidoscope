"""ContradictionDetectorService — Claim Consistency Analysis.

Finds contradictions, tensions, and inconsistencies between claims within
a research corpus. Distinguishes genuine contradictions from apparent ones
(different contexts, different operationalizations, different time periods).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CONTRADICTION_SYSTEM = """You are a contradiction detection expert. Given a set of claims, find all contradictions, tensions, and inconsistencies. Distinguish between:
- Hard contradictions: logically cannot both be true
- Soft tensions: in tension but could both be true under different conditions
- Apparent contradictions: seem contradictory but aren't (different contexts, definitions, or scopes)

Output JSON with: contradictions (list of claim_a/claim_b/type hard|soft|apparent/explanation/resolution_possible bool/resolution_path/severity critical|major|minor/which_is_likely_correct), meta.total_claims_analyzed, meta.consistency_score (0-1 where 1 is fully consistent), meta.most_critical_contradiction, meta.overall_coherence_assessment."""

CONTRADICTION_PROMPT = """Detect contradictions in these claims:

Domain: {domain}
Context: {context}

Claims:
{claims_text}

Find all contradictions and tensions. Return ONLY valid JSON."""

RECONCILE_SYSTEM = """You are a claim reconciliation expert. Given two contradictory claims, find the most likely resolution: which is correct, under what conditions each holds, or what synthesis resolves the tension.

Output JSON with: reconciliation.claim_a, reconciliation.claim_b, reconciliation.contradiction_type, reconciliation.resolution (synthesis/a_correct/b_correct/context_dependent/insufficient_evidence), reconciliation.reasoning, reconciliation.conditions_for_a (when claim A holds), reconciliation.conditions_for_b (when claim B holds), reconciliation.synthesis (if possible - a statement that subsumes both), reconciliation.confidence (0-1), reconciliation.evidence_needed (what would resolve this definitively)."""

RECONCILE_PROMPT = """Reconcile these contradictory claims:

Claim A: {claim_a}
Claim B: {claim_b}
Domain: {domain}

Context:
{context_text}

Find the resolution. Return ONLY valid JSON."""


class ContradictionDetectorService:
    """Detects and reconciles contradictions between claims."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claims: list[str],
        *,
        domain: str = "",
        context: str = "",
        dossier_id: str | None = None,
    ) -> dict:
        """Detect contradictions among a set of claims."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        claims_text = "\n".join(f"{i+1}. {c}" for i, c in enumerate(claims[:15]))

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CONTRADICTION_PROMPT.format(
                domain=domain or "research",
                context=context or "Academic research claims",
                claims_text=claims_text,
            ),
            system=CONTRADICTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        meta = data.get("meta", {})

        return {
            "contradictions": data.get("contradictions", []),
            "total_analyzed": meta.get("total_claims_analyzed", len(claims)),
            "consistency_score": meta.get("consistency_score", 0),
            "most_critical": meta.get("most_critical_contradiction", ""),
            "coherence_assessment": meta.get("overall_coherence_assessment", ""),
        }

    async def reconcile(
        self,
        claim_a: str,
        claim_b: str,
        *,
        domain: str = "",
        context: str = "",
        dossier_id: str | None = None,
    ) -> dict:
        """Reconcile two contradictory claims."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        extra = await self._gather_context(f"{claim_a} {claim_b}", dossier_id)
        context_text = context or "\n".join(f"- {e}" for e in extra[:5]) or "General"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=RECONCILE_PROMPT.format(
                claim_a=claim_a,
                claim_b=claim_b,
                domain=domain or "research",
                context_text=context_text,
            ),
            system=RECONCILE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        rec = data.get("reconciliation", data)

        return {
            "claim_a": claim_a,
            "claim_b": claim_b,
            "resolution": rec.get("resolution", ""),
            "reasoning": rec.get("reasoning", ""),
            "conditions_for_a": rec.get("conditions_for_a", ""),
            "conditions_for_b": rec.get("conditions_for_b", ""),
            "synthesis": rec.get("synthesis", ""),
            "confidence": rec.get("confidence", 0),
            "evidence_needed": rec.get("evidence_needed", ""),
        }

    async def _gather_context(self, query: str, dossier_id: str | None) -> list[str]:
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=query[:100], top_k=4)
            return [r.get("payload", {}).get("text", "")[:120] for r in results]
        except Exception:
            return []
