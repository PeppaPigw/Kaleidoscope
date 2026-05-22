"""EpistemicSleepApneaService — Epistemic Sleep Apnea Detection.

Detects epistemic sleep apnea — repeated interruptions of thought flow
causing fragmented intellectual processing and oxygen-like deprivation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SLEEP_APNEA_SYSTEM = """You are an epistemic sleep apnea specialist. Given interrupted thought flow, assess apnea patterns:

Key concepts:
- Epistemic sleep apnea: repeated interruptions of thought flow
- Obstructive: external factors blocking thought
- Central: brain failing to signal thought continuation
- Hypopnea: reduced thought flow without complete stop
- Desaturation: intellectual oxygen deprivation
- Arousal: brief awakening disrupting thought depth
- CPAP equivalent: continuous positive intellectual pressure

When epistemic sleep apnea IS present:
- Repeated thought interruptions
- External factors blocking thought
- Brain failing to continue
- Reduced thought flow
- Intellectual deprivation
- Brief disruptions of depth
- Continuous pressure needed

When no apnea:
- Uninterrupted thought flow
- No external blocking
- Normal thought continuation
- Full thought flow
- Adequate intellectual oxygen
- Sustained depth
- No pressure needed

Output JSON with: apnea_detected (bool), severity (none/mild/moderate/severe), interruption_pattern (what stops thought), obstruction_type (what blocks flow), desaturation_level (what deprivation), arousal_frequency (what disruptions), recommendation (no_apnea/mild_positional_change/significant_cpap_equivalent/major_intensive_intervention/emergency_severe_deprivation)."""

EPISTEMIC_SLEEP_APNEA_PROMPT = """Detect epistemic sleep apnea:

Interruption pattern: {interruption_pattern}
Obstruction type: {obstruction_type}
Desaturation level: {desaturation_level}
Arousal frequency: {arousal_frequency}
Domain: {domain}
Context: {context}

Are there repeated interruptions of thought flow causing fragmented processing? Return ONLY valid JSON."""


class EpistemicSleepApneaService:
    """Detects epistemic sleep apnea — repeated thought flow interruptions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        interruption_pattern: str,
        *,
        obstruction_type: str = "",
        desaturation_level: str = "",
        arousal_frequency: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic sleep apnea."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SLEEP_APNEA_PROMPT.format(
                interruption_pattern=interruption_pattern,
                obstruction_type=obstruction_type or "Not specified",
                desaturation_level=desaturation_level or "Not specified",
                arousal_frequency=arousal_frequency or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SLEEP_APNEA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "interruption_pattern": interruption_pattern[:200],
            "apnea_detected": data.get("apnea_detected", False),
            "severity": data.get("severity", ""),
            "obstruction_type": data.get("obstruction_type", ""),
            "desaturation_level": data.get("desaturation_level", ""),
            "arousal_frequency": data.get("arousal_frequency", ""),
            "recommendation": data.get("recommendation", ""),
        }
