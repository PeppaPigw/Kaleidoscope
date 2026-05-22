"""EpistemicExpertisePerformanceService — Epistemic Expertise Performance Detection.

Detects epistemic expertise performance — performing expertise rather
than genuinely exercising it, prioritizing appearance over substance.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EXPERTISE_PERFORMANCE_SYSTEM = """You are an epistemic expertise performance specialist. Given performing expertise rather than exercising it, assess expertise performance:

Key concepts:
- Epistemic expertise performance: performing expertise rather than genuinely exercising it
- Appearance over substance: prioritizing looking expert over being expert
- Jargon deployment: using jargon to signal expertise rather than communicate
- Complexity theater: making things complex to appear expert
- Certainty performance: performing certainty when uncertain
- Authority display: displaying authority rather than demonstrating competence
- Knowledge signaling: signaling knowledge rather than applying it

When epistemic expertise performance IS present:
- Expertise performed not exercised
- Appearance prioritized over substance
- Jargon deployed for signaling
- Complexity theatrical
- Certainty performed
- Authority displayed
- Knowledge signaled not applied

When no expertise performance:
- Expertise genuinely exercised
- Substance over appearance
- Language communicates clearly
- Complexity proportionate
- Uncertainty acknowledged
- Competence demonstrated
- Knowledge applied

Output JSON with: expertise_performance_detected (bool), severity (none/mild/moderate/severe), appearance_over_substance (what appearance prioritized), jargon_deployment (what jargon deployed), complexity_theater (what complexity theatrical), certainty_performance (what certainty performed), recommendation (no_expertise_performance/mild_authenticity_practice/significant_substance_recovery/major_intensive_genuine_expertise/emergency_complete_expertise_performance)."""

EPISTEMIC_EXPERTISE_PERFORMANCE_PROMPT = """Detect epistemic expertise performance:

Appearance over substance: {appearance_over_substance}
Jargon deployment: {jargon_deployment}
Complexity theater: {complexity_theater}
Certainty performance: {certainty_performance}
Domain: {domain}
Context: {context}

Is expertise being performed rather than genuinely exercised? Return ONLY valid JSON."""


class EpistemicExpertisePerformanceService:
    """Detects epistemic expertise performance — appearance over substance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        appearance_over_substance: str,
        *,
        jargon_deployment: str = "",
        complexity_theater: str = "",
        certainty_performance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic expertise performance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EXPERTISE_PERFORMANCE_PROMPT.format(
                appearance_over_substance=appearance_over_substance,
                jargon_deployment=jargon_deployment or "Not specified",
                complexity_theater=complexity_theater or "Not specified",
                certainty_performance=certainty_performance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EXPERTISE_PERFORMANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "appearance_over_substance": appearance_over_substance[:200],
            "expertise_performance_detected": data.get("expertise_performance_detected", False),
            "severity": data.get("severity", ""),
            "jargon_deployment": data.get("jargon_deployment", ""),
            "complexity_theater": data.get("complexity_theater", ""),
            "certainty_performance": data.get("certainty_performance", ""),
            "recommendation": data.get("recommendation", ""),
        }
