"""EpistemicOvertrainingService — Epistemic Overtraining Detection.

Detects epistemic overtraining — intellectual systems pushed beyond recovery
capacity, leading to performance decline despite continued effort.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_OVERTRAINING_SYSTEM = """You are an epistemic overtraining specialist. Given intellectual systems pushed beyond recovery, assess overtraining:

Key concepts:
- Epistemic overtraining: pushed beyond recovery capacity
- Performance paradox: more effort yielding worse results
- Recovery deficit: insufficient rest between efforts
- Sympathetic overload: stress response stuck on
- Parasympathetic: exhaustion and withdrawal phase
- Periodization: structured variation in intensity
- Deload: planned reduction in intellectual load

When epistemic overtraining IS present:
- Pushed beyond recovery capacity
- More effort yielding worse results
- Insufficient rest between efforts
- Stress response stuck on
- Exhaustion and withdrawal
- No structured variation
- No planned load reduction

When no overtraining:
- Within recovery capacity
- Effort yielding results
- Adequate rest periods
- Normal stress response
- Energized and engaged
- Structured variation present
- Appropriate load management

Output JSON with: overtraining_detected (bool), severity (none/mild/moderate/severe), performance_trend (what output trajectory), recovery_status (what rest adequacy), stress_markers (what overload signs), periodization_status (what variation), recommendation (no_overtraining/mild_overreaching/significant_overtraining/major_burnout/emergency_complete_rest)."""

EPISTEMIC_OVERTRAINING_PROMPT = """Detect epistemic overtraining:

Performance trend: {performance_trend}
Recovery status: {recovery_status}
Stress markers: {stress_markers}
Periodization status: {periodization_status}
Domain: {domain}
Context: {context}

Is the intellectual system pushed beyond recovery capacity? Return ONLY valid JSON."""


class EpistemicOvertrainingService:
    """Detects epistemic overtraining — pushed beyond recovery capacity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        performance_trend: str,
        *,
        recovery_status: str = "",
        stress_markers: str = "",
        periodization_status: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic overtraining."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_OVERTRAINING_PROMPT.format(
                performance_trend=performance_trend,
                recovery_status=recovery_status or "Not specified",
                stress_markers=stress_markers or "Not specified",
                periodization_status=periodization_status or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_OVERTRAINING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "performance_trend": performance_trend[:200],
            "overtraining_detected": data.get("overtraining_detected", False),
            "severity": data.get("severity", ""),
            "recovery_status": data.get("recovery_status", ""),
            "stress_markers": data.get("stress_markers", ""),
            "periodization_status": data.get("periodization_status", ""),
            "recommendation": data.get("recommendation", ""),
        }
