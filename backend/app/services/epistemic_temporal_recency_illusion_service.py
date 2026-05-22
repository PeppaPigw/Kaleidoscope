"""EpistemicTemporalRecencyIllusionService - Epistemic Temporal Recency Illusion Detection.

Detects recency illusion where recent observations are mistaken for new phenomena.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TEMPORAL_RECENCY_ILLUSION_SYSTEM = """You are an epistemic temporal recency illusion specialist. Given novelty misattribution, assess recency illusion:

Key concepts:
- Epistemic temporal recency illusion: mistaking recent observations for new phenomena
- Novelty misattribution: labeling newly noticed things as newly existing
- Historical ignorance: missing older examples and long-running patterns
- Frequency illusion: noticing something more after attention is primed
- Baader-Meinhof effect: recently learned items seeming suddenly ubiquitous

When epistemic temporal recency illusion IS present:
- Recent observations treated as new phenomena
- Historical examples ignored
- Noticing frequency confused with actual frequency
- Attention priming mistaken for objective increase
- Newly learned labels treated as newly emerging realities

When no recency illusion:
- Novelty checked against history
- Prior examples considered
- Observation frequency separated from real frequency
- Attention effects acknowledged
- Current visibility distinguished from actual emergence

Output JSON with: recency_illusion_detected (bool), severity (none/mild/moderate/severe), historical_ignorance (what history missed), frequency_illusion (what noticing confused with frequency), baader_meinhof (what attention priming distorted), recommendation (no_recency_illusion/mild_historical_checking/significant_frequency_validation/major_longitudinal_review/emergency_complete_recency_illusion)."""

EPISTEMIC_TEMPORAL_RECENCY_ILLUSION_PROMPT = """Detect epistemic temporal recency illusion:

Novelty misattribution: {novelty_misattribution}
Historical ignorance: {historical_ignorance}
Frequency illusion: {frequency_illusion}
Baader-Meinhof: {baader_meinhof}
Domain: {domain}
Context: {context}

Are recent observations being mistaken for new phenomena? Return ONLY valid JSON."""


class EpistemicTemporalRecencyIllusionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        novelty_misattribution: str,
        *,
        historical_ignorance: str = "",
        frequency_illusion: str = "",
        baader_meinhof: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TEMPORAL_RECENCY_ILLUSION_PROMPT.format(
                novelty_misattribution=novelty_misattribution,
                historical_ignorance=historical_ignorance or "Not specified",
                frequency_illusion=frequency_illusion or "Not specified",
                baader_meinhof=baader_meinhof or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TEMPORAL_RECENCY_ILLUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "novelty_misattribution": novelty_misattribution[:200],
            "recency_illusion_detected": data.get("recency_illusion_detected", False),
            "severity": data.get("severity", ""),
            "historical_ignorance": data.get("historical_ignorance", ""),
            "frequency_illusion": data.get("frequency_illusion", ""),
            "baader_meinhof": data.get("baader_meinhof", ""),
            "recommendation": data.get("recommendation", ""),
        }
