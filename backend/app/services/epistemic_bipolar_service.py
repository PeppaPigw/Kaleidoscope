"""EpistemicBipolarService — Epistemic Bipolar Detection.

Detects epistemic bipolar — cycling between intellectual mania
(grandiose overproduction) and depression (complete shutdown).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BIPOLAR_SYSTEM = """You are an epistemic bipolar specialist. Given intellectual mood cycling, assess bipolar:

Key concepts:
- Epistemic bipolar: cycling between mania and depression
- Mania: grandiose overproduction, racing thoughts, decreased need for rest
- Depression: complete intellectual shutdown, inability to produce
- Hypomania: milder elevation without full mania
- Rapid cycling: frequent switches between states
- Mood stabilizer: preventing extreme swings
- Mixed state: simultaneous manic and depressive features

When epistemic bipolar IS present:
- Cycling between overproduction and shutdown
- Grandiose intellectual output periods
- Complete shutdown periods
- Milder elevation episodes
- Frequent state switches
- Mood stabilization needed
- Simultaneous contradictory features

When no bipolar:
- Stable intellectual output
- No grandiose periods
- No shutdown periods
- Consistent energy levels
- No state switching
- No stabilization needed
- No contradictory features

Output JSON with: bipolar_detected (bool), severity (none/mild/moderate/severe), cycle_pattern (what switching), manic_features (what overproduction), depressive_features (what shutdown), current_phase (what state now), recommendation (no_bipolar/mild_monitoring/significant_mood_stabilizer/major_combination/emergency_acute_mania_or_suicidality)."""

EPISTEMIC_BIPOLAR_PROMPT = """Detect epistemic bipolar:

Cycle pattern: {cycle_pattern}
Manic features: {manic_features}
Depressive features: {depressive_features}
Current phase: {current_phase}
Domain: {domain}
Context: {context}

Is there cycling between intellectual mania and depression? Return ONLY valid JSON."""


class EpistemicBipolarService:
    """Detects epistemic bipolar — cycling between mania and depression."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        cycle_pattern: str,
        *,
        manic_features: str = "",
        depressive_features: str = "",
        current_phase: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic bipolar."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BIPOLAR_PROMPT.format(
                cycle_pattern=cycle_pattern,
                manic_features=manic_features or "Not specified",
                depressive_features=depressive_features or "Not specified",
                current_phase=current_phase or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BIPOLAR_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "cycle_pattern": cycle_pattern[:200],
            "bipolar_detected": data.get("bipolar_detected", False),
            "severity": data.get("severity", ""),
            "manic_features": data.get("manic_features", ""),
            "depressive_features": data.get("depressive_features", ""),
            "current_phase": data.get("current_phase", ""),
            "recommendation": data.get("recommendation", ""),
        }
