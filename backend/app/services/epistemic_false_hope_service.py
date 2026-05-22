"""EpistemicFalseHopeService — Epistemic False Hope Detection.

Detects epistemic false hope — clinging to intellectually unjustified
hope that distorts assessment of evidence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FALSE_HOPE_SYSTEM = """You are an epistemic false hope specialist. Given clinging to unjustified hope, assess false hope:

Key concepts:
- Epistemic false hope: clinging to unjustified intellectual hope
- Evidence denial: ignoring evidence against hoped-for outcome
- Probability distortion: overestimating likelihood of desired outcome
- Selective attention: only seeing evidence supporting hope
- Wishful extrapolation: projecting desired outcomes without basis
- Sunk cost hope: hoping because of investment not evidence
- Desperation hope: hoping because alternative is unbearable

When epistemic false hope IS present:
- Clinging to unjustified hope
- Ignoring contrary evidence
- Overestimating likelihood
- Only seeing supporting evidence
- Projecting without basis
- Hoping from investment
- Hoping from desperation

When no false hope:
- Hope calibrated to evidence
- Acknowledging contrary evidence
- Realistic probability assessment
- Seeing all evidence
- Projecting from evidence
- Hope independent of investment
- Hope from genuine possibility

Output JSON with: false_hope_detected (bool), severity (none/mild/moderate/severe), evidence_denial (what ignoring), probability_distortion (what overestimating), selective_attention (what only seeing), desperation_hope (what hoping from desperation), recommendation (no_false_hope/mild_calibration_practice/significant_reality_testing/major_intensive_hope_processing/emergency_severe_denial)."""

EPISTEMIC_FALSE_HOPE_PROMPT = """Detect epistemic false hope:

Evidence denial: {evidence_denial}
Probability distortion: {probability_distortion}
Selective attention: {selective_attention}
Desperation hope: {desperation_hope}
Domain: {domain}
Context: {context}

Is there clinging to intellectually unjustified hope? Return ONLY valid JSON."""


class EpistemicFalseHopeService:
    """Detects epistemic false hope — clinging to unjustified intellectual hope."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        evidence_denial: str,
        *,
        probability_distortion: str = "",
        selective_attention: str = "",
        desperation_hope: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic false hope."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FALSE_HOPE_PROMPT.format(
                evidence_denial=evidence_denial,
                probability_distortion=probability_distortion or "Not specified",
                selective_attention=selective_attention or "Not specified",
                desperation_hope=desperation_hope or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FALSE_HOPE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "evidence_denial": evidence_denial[:200],
            "false_hope_detected": data.get("false_hope_detected", False),
            "severity": data.get("severity", ""),
            "probability_distortion": data.get("probability_distortion", ""),
            "selective_attention": data.get("selective_attention", ""),
            "desperation_hope": data.get("desperation_hope", ""),
            "recommendation": data.get("recommendation", ""),
        }
