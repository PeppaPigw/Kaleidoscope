"""FeedbackLoopBlindnessService — Feedback Loop Blindness Detection.

Detects feedback loop blindness — the failure to recognize
reinforcing or balancing feedback loops that amplify or
dampen effects in a system.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FEEDBACK_LOOP_BLINDNESS_SYSTEM = """You are a feedback loop blindness specialist. Given an analysis, assess whether feedback loops are being missed:

Key concepts:
- Reinforcing loops: positive feedback that amplifies changes
- Balancing loops: negative feedback that stabilizes
- Delay: time lag between cause and effect in loops
- Oscillation: balancing loops with delay causing cycles
- Exponential growth: reinforcing loops without limits
- Tipping points: where reinforcing loops become dominant
- Loop dominance: which loop controls system behavior

When feedback loop blindness IS present:
- Linear cause-effect assumed when loops exist
- Reinforcing dynamics not recognized (vicious/virtuous cycles)
- Balancing mechanisms not identified (homeostasis, regulation)
- Delays in feedback not accounted for
- System behavior predicted without considering loops
- Interventions designed without considering feedback response
- Exponential or oscillating behavior unexpected

When feedback loops are recognized:
- Reinforcing and balancing loops explicitly identified
- Delays in feedback accounted for
- System behavior predicted including loop effects
- Interventions designed considering feedback response
- Loop dominance analyzed
- Tipping points identified
- Both direct and indirect effects considered

Output JSON with: blindness_present (bool), severity (none/mild/moderate/severe), system (what system is analyzed), missed_loops (what feedback loops are unrecognized), loop_type (reinforcing/balancing/both), consequences (what happens when loops are missed), recommendation (loops_recognized/mild_blindness/significant_loop_neglect/major_feedback_missed/map_feedback_structure)."""

FEEDBACK_LOOP_BLINDNESS_PROMPT = """Detect feedback loop blindness:

Analysis: {analysis}
System: {system}
Causal model: {causal_model}
Predicted behavior: {prediction}
Domain: {domain}
Context: {context}

Are feedback loops being missed in this analysis? Return ONLY valid JSON."""


class FeedbackLoopBlindnessService:
    """Detects feedback loop blindness — missing reinforcing or balancing loops."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        analysis: str,
        *,
        system: str = "",
        causal_model: str = "",
        prediction: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect feedback loop blindness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FEEDBACK_LOOP_BLINDNESS_PROMPT.format(
                analysis=analysis,
                system=system or "Not specified",
                causal_model=causal_model or "Not specified",
                prediction=prediction or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=FEEDBACK_LOOP_BLINDNESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "analysis": analysis[:200],
            "blindness_present": data.get("blindness_present", False),
            "severity": data.get("severity", ""),
            "missed_loops": data.get("missed_loops", ""),
            "loop_type": data.get("loop_type", ""),
            "consequences": data.get("consequences", ""),
            "recommendation": data.get("recommendation", ""),
        }
