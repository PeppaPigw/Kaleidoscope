"""EpistemicMentalizationFailureService — Epistemic Mentalization Failure Detection.

Detects epistemic mentalization failure — inability to understand others'
intellectual states, motivations, and perspectives.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MENTALIZATION_FAILURE_SYSTEM = """You are an epistemic mentalization failure specialist. Given inability to understand others' intellectual states, assess mentalization:

Key concepts:
- Epistemic mentalization failure: can't understand others' thinking
- Theory of mind deficit: unable to model others' intellectual states
- Perspective blindness: can't see from others' viewpoint
- Teleological mode: judging only by visible intellectual behavior
- Psychic equivalence: assuming others think same as self
- Pretend mode: intellectual discourse disconnected from reality
- Alien self: others' thinking feels incomprehensible

When epistemic mentalization failure IS present:
- Can't understand others' thinking
- Unable to model states
- Can't see others' viewpoint
- Judging only by behavior
- Assuming others think same
- Discourse disconnected
- Others incomprehensible

When no mentalization failure:
- Understanding others' thinking
- Modeling mental states
- Taking perspectives
- Understanding motivations
- Recognizing difference
- Connected discourse
- Others comprehensible

Output JSON with: mentalization_failure_detected (bool), severity (none/mild/moderate/severe), theory_of_mind_deficit (what can't model), perspective_blindness (what can't see), teleological_mode (what judging by), psychic_equivalence (what assuming same), recommendation (no_mentalization_failure/mild_perspective_practice/significant_mentalization_therapy/major_intensive_mbt/emergency_severe_failure)."""

EPISTEMIC_MENTALIZATION_FAILURE_PROMPT = """Detect epistemic mentalization failure:

Theory of mind deficit: {theory_of_mind_deficit}
Perspective blindness: {perspective_blindness}
Teleological mode: {teleological_mode}
Psychic equivalence: {psychic_equivalence}
Domain: {domain}
Context: {context}

Is there inability to understand others' intellectual states and perspectives? Return ONLY valid JSON."""


class EpistemicMentalizationFailureService:
    """Detects epistemic mentalization failure — can't understand others' thinking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        theory_of_mind_deficit: str,
        *,
        perspective_blindness: str = "",
        teleological_mode: str = "",
        psychic_equivalence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic mentalization failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MENTALIZATION_FAILURE_PROMPT.format(
                theory_of_mind_deficit=theory_of_mind_deficit,
                perspective_blindness=perspective_blindness or "Not specified",
                teleological_mode=teleological_mode or "Not specified",
                psychic_equivalence=psychic_equivalence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MENTALIZATION_FAILURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "theory_of_mind_deficit": theory_of_mind_deficit[:200],
            "mentalization_failure_detected": data.get("mentalization_failure_detected", False),
            "severity": data.get("severity", ""),
            "perspective_blindness": data.get("perspective_blindness", ""),
            "teleological_mode": data.get("teleological_mode", ""),
            "psychic_equivalence": data.get("psychic_equivalence", ""),
            "recommendation": data.get("recommendation", ""),
        }
