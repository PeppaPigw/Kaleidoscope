"""EpistemicImpulsiveCognitionService — Epistemic Impulsive Cognition Detection.

Detects epistemic impulsive cognition — making intellectual decisions
impulsively without adequate reflection or consideration.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_IMPULSIVE_COGNITION_SYSTEM = """You are an epistemic impulsive cognition specialist. Given impulsive intellectual decisions, assess impulsivity:

Key concepts:
- Epistemic impulsive cognition: deciding without reflecting
- Premature closure: jumping to conclusions too fast
- Action without thought: intellectual leaps without checking
- Regret pattern: frequently regretting intellectual commitments
- Urgency drive: feeling must decide NOW intellectually
- Reflection deficit: inability to pause and consider
- Consequence blindness: not seeing intellectual implications

When epistemic impulsive cognition IS present:
- Deciding without reflecting
- Jumping to conclusions
- Intellectual leaps without checking
- Frequently regretting commitments
- Must decide NOW
- Unable to pause and consider
- Not seeing implications

When no impulsive cognition:
- Reflective decision-making
- Appropriate deliberation
- Checked conclusions
- Satisfied with commitments
- Comfortable with timing
- Able to pause
- Seeing implications

Output JSON with: impulsive_cognition_detected (bool), severity (none/mild/moderate/severe), premature_closure (what jumping to), urgency_drive (what rushing), reflection_deficit (what not pausing), consequence_blindness (what not seeing), recommendation (no_impulsive_cognition/mild_pause_practice/significant_reflection_building/major_intensive_impulse_management/emergency_severe_impulsivity)."""

EPISTEMIC_IMPULSIVE_COGNITION_PROMPT = """Detect epistemic impulsive cognition:

Premature closure: {premature_closure}
Urgency drive: {urgency_drive}
Reflection deficit: {reflection_deficit}
Consequence blindness: {consequence_blindness}
Domain: {domain}
Context: {context}

Is there impulsive intellectual decision-making without adequate reflection? Return ONLY valid JSON."""


class EpistemicImpulsiveCognitionService:
    """Detects epistemic impulsive cognition — deciding without reflecting."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        premature_closure: str,
        *,
        urgency_drive: str = "",
        reflection_deficit: str = "",
        consequence_blindness: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic impulsive cognition."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_IMPULSIVE_COGNITION_PROMPT.format(
                premature_closure=premature_closure,
                urgency_drive=urgency_drive or "Not specified",
                reflection_deficit=reflection_deficit or "Not specified",
                consequence_blindness=consequence_blindness or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_IMPULSIVE_COGNITION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "premature_closure": premature_closure[:200],
            "impulsive_cognition_detected": data.get("impulsive_cognition_detected", False),
            "severity": data.get("severity", ""),
            "urgency_drive": data.get("urgency_drive", ""),
            "reflection_deficit": data.get("reflection_deficit", ""),
            "consequence_blindness": data.get("consequence_blindness", ""),
            "recommendation": data.get("recommendation", ""),
        }
