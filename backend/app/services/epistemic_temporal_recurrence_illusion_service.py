"""EpistemicTemporalRecurrenceIllusionService — Epistemic Temporal Recurrence Illusion Detection.

Detects epistemic temporal recurrence illusion — seeing cyclical patterns
where none exist, imposing false periodicity on events.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TEMPORAL_RECURRENCE_ILLUSION_SYSTEM = """You are an epistemic temporal recurrence illusion specialist. Given false cyclical patterns imposed on events, assess recurrence illusion:

Key concepts:
- Epistemic temporal recurrence illusion: seeing cycles where none exist
- False periodicity: imposing periodic structure on aperiodic events
- History repeats fallacy: assuming history must repeat
- Cycle hunting: actively seeking cycles in random data
- Pattern imposition: imposing cyclical pattern on noise
- Pendulum fallacy: assuming things must swing back
- Seasonal illusion: seeing seasonal patterns in non-seasonal data

When epistemic temporal recurrence illusion IS present:
- Cycles seen where none exist
- Periodicity imposed on aperiodic
- History assumed to repeat
- Cycles hunted in random data
- Patterns imposed on noise
- Pendulum assumed
- Seasons imposed on non-seasonal

When no recurrence illusion:
- Cycles verified statistically
- Periodicity tested
- History compared carefully
- Cycles tested against null
- Patterns validated
- Direction not assumed
- Seasonality tested

Output JSON with: temporal_recurrence_illusion_detected (bool), severity (none/mild/moderate/severe), false_periodicity (what false periodicity imposed), history_repeats_fallacy (what history assumed to repeat), cycle_hunting (what cycles hunted), pendulum_fallacy (what pendulum assumed), recommendation (no_recurrence_illusion/mild_cycle_skepticism/significant_statistical_testing/major_intensive_pattern_validation/emergency_complete_recurrence_illusion)."""

EPISTEMIC_TEMPORAL_RECURRENCE_ILLUSION_PROMPT = """Detect epistemic temporal recurrence illusion:

False periodicity: {false_periodicity}
History repeats fallacy: {history_repeats_fallacy}
Cycle hunting: {cycle_hunting}
Pendulum fallacy: {pendulum_fallacy}
Domain: {domain}
Context: {context}

Are cyclical patterns being seen where none actually exist? Return ONLY valid JSON."""


class EpistemicTemporalRecurrenceIllusionService:
    """Detects epistemic temporal recurrence illusion — false cycles."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        false_periodicity: str,
        *,
        history_repeats_fallacy: str = "",
        cycle_hunting: str = "",
        pendulum_fallacy: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic temporal recurrence illusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TEMPORAL_RECURRENCE_ILLUSION_PROMPT.format(
                false_periodicity=false_periodicity,
                history_repeats_fallacy=history_repeats_fallacy or "Not specified",
                cycle_hunting=cycle_hunting or "Not specified",
                pendulum_fallacy=pendulum_fallacy or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TEMPORAL_RECURRENCE_ILLUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "false_periodicity": false_periodicity[:200],
            "temporal_recurrence_illusion_detected": data.get("temporal_recurrence_illusion_detected", False),
            "severity": data.get("severity", ""),
            "history_repeats_fallacy": data.get("history_repeats_fallacy", ""),
            "cycle_hunting": data.get("cycle_hunting", ""),
            "pendulum_fallacy": data.get("pendulum_fallacy", ""),
            "recommendation": data.get("recommendation", ""),
        }
