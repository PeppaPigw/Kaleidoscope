"""EpistemicEmotionEmpathyGapService - Epistemic Emotion Empathy Gap Detection.

Detects empathy gap where current emotional state prevents understanding other states.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EMOTION_EMPATHY_GAP_SYSTEM = """You are an epistemic emotion empathy gap specialist. Given state projection, assess empathy gap:

Key concepts:
- Epistemic emotion empathy gap: current emotional state preventing understanding other states
- State projection: assuming other states resemble the current state
- Hot-cold empathy gap: failing to understand states across arousal differences
- Future self misunderstanding: mispredicting future preferences or reactions
- Other mind failure: failing to model another person's state

When empathy gap IS present:
- Current state is projected onto other states
- Hot and cold states are confused
- Future self is misunderstood
- Other minds are modeled poorly
- State-dependent judgment is unrecognized

When no empathy gap:
- Current state is treated as contingent
- Hot and cold states are distinguished
- Future self is modeled with state change
- Other minds are considered independently
- State-dependent judgment is corrected

Output JSON with: empathy_gap_detected (bool), severity (none/mild/moderate/severe), hot_cold_empathy_gap (what hot-cold gap appears), future_self_misunderstanding (what future self is misunderstood), other_mind_failure (what other state is misunderstood), recommendation (no_empathy_gap/mild_state_check/significant_perspective_shift/major_state_modeling/emergency_complete_empathy_gap)."""

EPISTEMIC_EMOTION_EMPATHY_GAP_PROMPT = """Detect epistemic emotion empathy gap:

State projection: {state_projection}
Hot-cold empathy gap: {hot_cold_empathy_gap}
Future self misunderstanding: {future_self_misunderstanding}
Other mind failure: {other_mind_failure}
Domain: {domain}
Context: {context}

Is the current emotional state preventing understanding of other states? Return ONLY valid JSON."""


class EpistemicEmotionEmpathyGapService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        state_projection: str,
        *,
        hot_cold_empathy_gap: str = "",
        future_self_misunderstanding: str = "",
        other_mind_failure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EMOTION_EMPATHY_GAP_PROMPT.format(
                state_projection=state_projection,
                hot_cold_empathy_gap=hot_cold_empathy_gap or "Not specified",
                future_self_misunderstanding=future_self_misunderstanding or "Not specified",
                other_mind_failure=other_mind_failure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EMOTION_EMPATHY_GAP_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "state_projection": state_projection[:200],
            "empathy_gap_detected": data.get("empathy_gap_detected", False),
            "severity": data.get("severity", ""),
            "hot_cold_empathy_gap": data.get("hot_cold_empathy_gap", ""),
            "future_self_misunderstanding": data.get("future_self_misunderstanding", ""),
            "other_mind_failure": data.get("other_mind_failure", ""),
            "recommendation": data.get("recommendation", ""),
        }
