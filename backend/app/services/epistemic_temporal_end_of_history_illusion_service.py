"""EpistemicTemporalEndOfHistoryIllusionService - Epistemic Temporal End-of-History Illusion Detection.

Detects end-of-history illusion believing the current state is final.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TEMPORAL_END_OF_HISTORY_ILLUSION_SYSTEM = """You are an epistemic temporal end-of-history illusion specialist. Given change denial, assess belief that the current state is final:

Key concepts:
- Epistemic temporal end-of-history illusion: believing the current state is final
- Change denial: discounting future change despite past change
- Stability assumption: assuming current preferences, institutions, or conditions will persist
- Future self underestimation: underestimating future changes in oneself or groups
- Permanence bias: treating current arrangements as durable by default

When epistemic temporal end-of-history illusion IS present:
- Current state treated as final
- Future change denied or minimized
- Stability assumed without support
- Future self or group change underestimated
- Current arrangements treated as permanent

When no end-of-history illusion:
- Future change considered
- Current state treated as contingent
- Past change used to calibrate future change
- Future self or group evolution acknowledged
- Stability assumptions tested

Output JSON with: end_of_history_illusion_detected (bool), severity (none/mild/moderate/severe), stability_assumption (what stability assumed), future_self_underestimation (what future change underestimated), permanence_bias (what treated as permanent), recommendation (no_end_of_history_illusion/mild_change_awareness/significant_future_scenario_testing/major_temporal_recalibration/emergency_complete_stability_reset)."""

EPISTEMIC_TEMPORAL_END_OF_HISTORY_ILLUSION_PROMPT = """Detect epistemic temporal end-of-history illusion:

Change denial: {change_denial}
Stability assumption: {stability_assumption}
Future self underestimation: {future_self_underestimation}
Permanence bias: {permanence_bias}
Domain: {domain}
Context: {context}

Is the current state being treated as final? Return ONLY valid JSON."""


class EpistemicTemporalEndOfHistoryIllusionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        change_denial: str,
        *,
        stability_assumption: str = "",
        future_self_underestimation: str = "",
        permanence_bias: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TEMPORAL_END_OF_HISTORY_ILLUSION_PROMPT.format(
                change_denial=change_denial,
                stability_assumption=stability_assumption or "Not specified",
                future_self_underestimation=future_self_underestimation or "Not specified",
                permanence_bias=permanence_bias or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TEMPORAL_END_OF_HISTORY_ILLUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "change_denial": change_denial[:200],
            "end_of_history_illusion_detected": data.get("end_of_history_illusion_detected", False),
            "severity": data.get("severity", ""),
            "stability_assumption": data.get("stability_assumption", ""),
            "future_self_underestimation": data.get("future_self_underestimation", ""),
            "permanence_bias": data.get("permanence_bias", ""),
            "recommendation": data.get("recommendation", ""),
        }
