"""EpistemicInsulinResistanceService — Epistemic Insulin Resistance Detection.

Detects epistemic insulin resistance — intellectual cells no longer responding
to regulatory signals despite abundance of those signals.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INSULIN_RESISTANCE_SYSTEM = """You are an epistemic insulin resistance specialist. Given intellectual signal resistance, assess:

Key concepts:
- Epistemic insulin resistance: cells not responding to regulatory signals
- Hyperinsulinemia: excess signals produced to compensate
- Glucose intolerance: inability to process intellectual fuel
- Metabolic syndrome: cluster of resistance-related problems
- Sensitizer therapy: restoring signal responsiveness
- Beta cell exhaustion: signal-producing cells burning out
- Downstream effects: cascading failures from resistance

When epistemic insulin resistance IS present:
- Cells not responding to regulatory signals
- Excess signals produced to compensate
- Unable to process intellectual fuel
- Cluster of resistance-related problems
- Signal responsiveness lost
- Signal-producing capacity exhausting
- Cascading failures occurring

When no insulin resistance:
- Normal signal responsiveness
- Appropriate signal levels
- Fuel processed normally
- No resistance-related problems
- Full responsiveness maintained
- Signal production sustainable
- No cascading failures

Output JSON with: insulin_resistance_detected (bool), severity (none/mild/moderate/severe), signal_responsiveness (what reception), compensation_level (what over-production), fuel_processing (what metabolism), exhaustion_risk (what burnout), recommendation (no_resistance/mild_lifestyle/significant_sensitizer/major_combination_therapy/emergency_metabolic_crisis)."""

EPISTEMIC_INSULIN_RESISTANCE_PROMPT = """Detect epistemic insulin resistance:

Signal responsiveness: {signal_responsiveness}
Compensation level: {compensation_level}
Fuel processing: {fuel_processing}
Exhaustion risk: {exhaustion_risk}
Domain: {domain}
Context: {context}

Are intellectual cells no longer responding to regulatory signals despite abundance? Return ONLY valid JSON."""


class EpistemicInsulinResistanceService:
    """Detects epistemic insulin resistance — cells not responding to signals."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        signal_responsiveness: str,
        *,
        compensation_level: str = "",
        fuel_processing: str = "",
        exhaustion_risk: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic insulin resistance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INSULIN_RESISTANCE_PROMPT.format(
                signal_responsiveness=signal_responsiveness,
                compensation_level=compensation_level or "Not specified",
                fuel_processing=fuel_processing or "Not specified",
                exhaustion_risk=exhaustion_risk or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INSULIN_RESISTANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "signal_responsiveness": signal_responsiveness[:200],
            "insulin_resistance_detected": data.get("insulin_resistance_detected", False),
            "severity": data.get("severity", ""),
            "compensation_level": data.get("compensation_level", ""),
            "fuel_processing": data.get("fuel_processing", ""),
            "exhaustion_risk": data.get("exhaustion_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }
