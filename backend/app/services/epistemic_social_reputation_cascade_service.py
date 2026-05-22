"""EpistemicSocialReputationCascadeService - Reputation Cascade Detection.

Detects reputation cascades where reputation substitutes for evidence evaluation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SOCIAL_REPUTATION_CASCADE_SYSTEM = """You are an epistemic social reputation cascade specialist. Given reputation dynamics, assess whether reputation substitutes for evidence:

Key concepts:
- Reputation cascade: reputation amplifying or suppressing claims regardless of evidence
- Halo effect: positive reputation making all claims seem credible
- Matthew effect: accumulated reputation attracting more credibility
- Evidence displacement: reputation replacing actual evaluation

When reputation cascade IS present:
- Reputation substitutes for evidence
- Halo effect distorts evaluation
- Accumulated reputation self-reinforcing
- Evidence evaluation displaced
- Source credibility conflated with claim truth

When no reputation cascade:
- Claims evaluated on evidence
- Reputation contextualized
- Source and claim distinguished
- Evidence prioritized
- Credibility earned per claim

Output JSON with: reputation_cascade_detected (bool), severity (none/mild/moderate/severe), halo_effect (what halo effect), matthew_effect (what matthew effect), evidence_displacement (what evidence displaced), recommendation (no_reputation_cascade/mild_evidence_check/significant_source_separation/major_evaluation_reconstruction/emergency_complete_reputation_cascade)."""

EPISTEMIC_SOCIAL_REPUTATION_CASCADE_PROMPT = """Detect epistemic social reputation cascade:

Reputation dynamic: {reputation_dynamic}
Halo effect: {halo_effect}
Matthew effect: {matthew_effect}
Evidence displacement: {evidence_displacement}
Domain: {domain}
Context: {context}

Is reputation substituting for evidence evaluation? Return ONLY valid JSON."""


class EpistemicSocialReputationCascadeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reputation_dynamic: str,
        *,
        halo_effect: str = "",
        matthew_effect: str = "",
        evidence_displacement: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SOCIAL_REPUTATION_CASCADE_PROMPT.format(
                reputation_dynamic=reputation_dynamic,
                halo_effect=halo_effect or "Not specified",
                matthew_effect=matthew_effect or "Not specified",
                evidence_displacement=evidence_displacement or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SOCIAL_REPUTATION_CASCADE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "reputation_dynamic": reputation_dynamic[:200],
            "reputation_cascade_detected": data.get("reputation_cascade_detected", False),
            "severity": data.get("severity", ""),
            "halo_effect": data.get("halo_effect", ""),
            "matthew_effect": data.get("matthew_effect", ""),
            "evidence_displacement": data.get("evidence_displacement", ""),
            "recommendation": data.get("recommendation", ""),
        }
