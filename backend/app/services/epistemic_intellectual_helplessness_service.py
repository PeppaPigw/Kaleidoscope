"""EpistemicIntellectualHelplessnessService — Epistemic Intellectual Helplessness Detection.

Detects epistemic intellectual helplessness — believing one is incapable
of understanding or learning.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INTELLECTUAL_HELPLESSNESS_SYSTEM = """You are an epistemic intellectual helplessness specialist. Given believing incapable of understanding, assess intellectual helplessness:

Key concepts:
- Epistemic intellectual helplessness: believing incapable of understanding
- Comprehension despair: believing one can never understand
- Learning futility: believing effort to learn is wasted
- Cognitive self-doubt: doubting one's ability to think
- Intellectual inadequacy: feeling fundamentally not smart enough
- Understanding ceiling: believing one has hit maximum capacity
- Growth impossibility: believing intellectual growth is impossible

When epistemic intellectual helplessness IS present:
- Believing incapable of understanding
- Believing can never understand
- Believing effort wasted
- Doubting ability to think
- Feeling not smart enough
- Believing hit maximum
- Believing growth impossible

When no intellectual helplessness:
- Confident in ability
- Believing understanding possible
- Effort valued
- Trusting thinking ability
- Feeling capable
- Believing growth possible
- Growth expected

Output JSON with: intellectual_helplessness_detected (bool), severity (none/mild/moderate/severe), comprehension_despair (what believing can never understand), learning_futility (what believing effort wasted on), cognitive_self_doubt (what doubting ability about), understanding_ceiling (what believing hit maximum on), recommendation (no_intellectual_helplessness/mild_confidence_building/significant_capability_recovery/major_intensive_self_efficacy_work/emergency_complete_intellectual_helplessness)."""

EPISTEMIC_INTELLECTUAL_HELPLESSNESS_PROMPT = """Detect epistemic intellectual helplessness:

Comprehension despair: {comprehension_despair}
Learning futility: {learning_futility}
Cognitive self doubt: {cognitive_self_doubt}
Understanding ceiling: {understanding_ceiling}
Domain: {domain}
Context: {context}

Is there believing one is incapable of understanding or learning? Return ONLY valid JSON."""


class EpistemicIntellectualHelplessnessService:
    """Detects epistemic intellectual helplessness — believing incapable of understanding."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        comprehension_despair: str,
        *,
        learning_futility: str = "",
        cognitive_self_doubt: str = "",
        understanding_ceiling: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic intellectual helplessness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INTELLECTUAL_HELPLESSNESS_PROMPT.format(
                comprehension_despair=comprehension_despair,
                learning_futility=learning_futility or "Not specified",
                cognitive_self_doubt=cognitive_self_doubt or "Not specified",
                understanding_ceiling=understanding_ceiling or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INTELLECTUAL_HELPLESSNESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "comprehension_despair": comprehension_despair[:200],
            "intellectual_helplessness_detected": data.get("intellectual_helplessness_detected", False),
            "severity": data.get("severity", ""),
            "learning_futility": data.get("learning_futility", ""),
            "cognitive_self_doubt": data.get("cognitive_self_doubt", ""),
            "understanding_ceiling": data.get("understanding_ceiling", ""),
            "recommendation": data.get("recommendation", ""),
        }
