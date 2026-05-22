"""EpistemicCertaintyAddictionService — Epistemic Certainty Addiction Detection.

Detects epistemic certainty addiction — addictive need for intellectual
certainty, unable to tolerate ambiguity or uncertainty.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CERTAINTY_ADDICTION_SYSTEM = """You are an epistemic certainty addiction specialist. Given addictive need for certainty, assess addiction:

Key concepts:
- Epistemic certainty addiction: must have certainty at all costs
- Ambiguity intolerance: can't bear not knowing
- Premature closure: grabbing any answer to end uncertainty
- False certainty: pretending to know when don't
- Anxiety driver: uncertainty causes unbearable anxiety
- Rigidity: holding onto certainty despite counter-evidence
- Exploration avoidance: won't explore because might find uncertainty

When epistemic certainty addiction IS present:
- Must have certainty at all costs
- Can't bear not knowing
- Grabbing any answer
- Pretending to know
- Uncertainty causes anxiety
- Holding despite evidence
- Won't explore

When no certainty addiction:
- Comfortable with uncertainty
- Tolerating not knowing
- Waiting for good answers
- Honest about limits
- Calm with ambiguity
- Flexible with evidence
- Exploring freely

Output JSON with: certainty_addiction_detected (bool), severity (none/mild/moderate/severe), ambiguity_intolerance (what can't bear), premature_closure (what grabbing), false_certainty (what pretending), exploration_avoidance (what won't explore), recommendation (no_certainty_addiction/mild_uncertainty_tolerance/significant_ambiguity_practice/major_intensive_addiction_work/emergency_severe_rigidity)."""

EPISTEMIC_CERTAINTY_ADDICTION_PROMPT = """Detect epistemic certainty addiction:

Ambiguity intolerance: {ambiguity_intolerance}
Premature closure: {premature_closure}
False certainty: {false_certainty}
Exploration avoidance: {exploration_avoidance}
Domain: {domain}
Context: {context}

Is there addictive need for intellectual certainty unable to tolerate ambiguity? Return ONLY valid JSON."""


class EpistemicCertaintyAddictionService:
    """Detects epistemic certainty addiction — must have certainty at all costs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        ambiguity_intolerance: str,
        *,
        premature_closure: str = "",
        false_certainty: str = "",
        exploration_avoidance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic certainty addiction."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CERTAINTY_ADDICTION_PROMPT.format(
                ambiguity_intolerance=ambiguity_intolerance,
                premature_closure=premature_closure or "Not specified",
                false_certainty=false_certainty or "Not specified",
                exploration_avoidance=exploration_avoidance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CERTAINTY_ADDICTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "ambiguity_intolerance": ambiguity_intolerance[:200],
            "certainty_addiction_detected": data.get("certainty_addiction_detected", False),
            "severity": data.get("severity", ""),
            "premature_closure": data.get("premature_closure", ""),
            "false_certainty": data.get("false_certainty", ""),
            "exploration_avoidance": data.get("exploration_avoidance", ""),
            "recommendation": data.get("recommendation", ""),
        }
