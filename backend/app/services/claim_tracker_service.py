"""ClaimTrackerService — Unified Claim Status Dashboard.

Provides a unified view of all claims in a research context: their current
evidence status, what's needed to resolve them, priority for investigation,
and how they relate to each other. The "project management" layer for claims.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ASSESS_SYSTEM = """You are a claim assessment expert. Given a set of claims with their evidence, assess each claim's current status and what's needed to move it forward.

For each claim, determine:
- Status: established (strong evidence) | supported (moderate evidence) | contested (conflicting evidence) | speculative (weak/no evidence) | refuted (evidence against)
- Evidence gap: what specific evidence would resolve this claim
- Priority: how important is resolving this claim for the overall research question
- Dependencies: which other claims depend on this one being true

Output JSON with: assessment.claims (list of claim/status/confidence 0-1/evidence_strength 0-1/evidence_gap/priority critical|high|medium|low/depends_on list of claim indices/blocks list of claim indices), assessment.overall_knowledge_state (how well-supported is the overall picture), assessment.critical_path (ordered list of claims to resolve first for maximum knowledge gain), assessment.weakest_claims (claims most in need of evidence), assessment.strongest_claims (claims with best evidence)."""

ASSESS_PROMPT = """Assess claim status:

Research question: {question}
Domain: {domain}

Claims to assess:
{claims_text}

Available evidence:
{evidence_text}

Assess each claim's status. Return ONLY valid JSON."""


class ClaimTrackerService:
    """Tracks and assesses claim status across research."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assess_claims(
        self,
        question: str,
        claims: list[str],
        *,
        evidence: list[str] | None = None,
        domain: str = "",
        dossier_id: str | None = None,
    ) -> dict:
        """Assess the status of multiple claims."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        claims_text = "\n".join(f"{i+1}. {c}" for i, c in enumerate(claims[:12]))
        extra = await self._gather_context(question, dossier_id)
        all_evidence = (evidence or []) + extra
        evidence_text = "\n".join(f"- {e}" for e in all_evidence[:10]) or "Limited evidence available"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ASSESS_PROMPT.format(
                question=question,
                domain=domain or "research",
                claims_text=claims_text,
                evidence_text=evidence_text,
            ),
            system=ASSESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        assessment = data.get("assessment", data)

        return {
            "question": question,
            "claims": assessment.get("claims", []),
            "overall_knowledge_state": assessment.get("overall_knowledge_state", ""),
            "critical_path": assessment.get("critical_path", []),
            "weakest_claims": assessment.get("weakest_claims", []),
            "strongest_claims": assessment.get("strongest_claims", []),
        }

    async def _gather_context(self, query: str, dossier_id: str | None) -> list[str]:
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=query[:100], top_k=5)
            return [r.get("payload", {}).get("text", "")[:120] for r in results]
        except Exception:
            return []
