"""EpistemicHypothyroidismService — Epistemic Hypothyroidism Detection.

Detects epistemic hypothyroidism — underactive intellectual metabolism
where everything slows down from insufficient signaling.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_HYPOTHYROIDISM_SYSTEM = """You are an epistemic hypothyroidism specialist. Given underactive intellectual metabolism, assess hypothyroidism:

Key concepts:
- Epistemic hypothyroidism: underactive intellectual metabolism
- Metabolic slowdown: all intellectual processes decelerating
- TSH elevation: compensatory signals increasing without effect
- Fatigue: intellectual exhaustion from insufficient energy
- Cold intolerance: inability to generate intellectual heat
- Weight gain: accumulation of unprocessed intellectual material
- Replacement therapy: supplementing missing signals

When epistemic hypothyroidism IS present:
- Intellectual metabolism underactive
- All processes decelerating
- Compensatory signals increasing without effect
- Intellectual exhaustion present
- Unable to generate intellectual energy
- Unprocessed material accumulating
- Signal supplementation needed

When no hypothyroidism:
- Normal intellectual metabolism
- Processes at appropriate speed
- Normal signal levels
- Adequate intellectual energy
- Normal energy generation
- Material processed normally
- No supplementation needed

Output JSON with: hypothyroidism_detected (bool), severity (none/mild/moderate/severe), metabolic_rate (what speed), signal_level (what hormone status), energy_status (what fatigue), accumulation (what buildup), recommendation (no_hypothyroidism/mild_monitoring/significant_low_dose_replacement/major_full_replacement/emergency_myxedema_crisis)."""

EPISTEMIC_HYPOTHYROIDISM_PROMPT = """Detect epistemic hypothyroidism:

Metabolic rate: {metabolic_rate}
Signal level: {signal_level}
Energy status: {energy_status}
Accumulation: {accumulation}
Domain: {domain}
Context: {context}

Is there underactive intellectual metabolism from insufficient signaling? Return ONLY valid JSON."""


class EpistemicHypothyroidismService:
    """Detects epistemic hypothyroidism — underactive intellectual metabolism."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        metabolic_rate: str,
        *,
        signal_level: str = "",
        energy_status: str = "",
        accumulation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic hypothyroidism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_HYPOTHYROIDISM_PROMPT.format(
                metabolic_rate=metabolic_rate,
                signal_level=signal_level or "Not specified",
                energy_status=energy_status or "Not specified",
                accumulation=accumulation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_HYPOTHYROIDISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "metabolic_rate": metabolic_rate[:200],
            "hypothyroidism_detected": data.get("hypothyroidism_detected", False),
            "severity": data.get("severity", ""),
            "signal_level": data.get("signal_level", ""),
            "energy_status": data.get("energy_status", ""),
            "accumulation": data.get("accumulation", ""),
            "recommendation": data.get("recommendation", ""),
        }
