"""EpistemicEmotionalReasoningService — Epistemic Emotional Reasoning Detection.

Detects epistemic emotional reasoning — using emotional states as evidence
for beliefs about the world.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EMOTIONAL_REASONING_SYSTEM = """You are an epistemic emotional reasoning specialist. Given using emotions as evidence for beliefs, assess emotional reasoning:

Key concepts:
- Epistemic emotional reasoning: using emotional states as evidence for beliefs
- Feeling as fact: treating feelings as facts about the world
- Anxiety as danger: treating anxiety as evidence of danger
- Guilt as wrongdoing: treating guilt as evidence of wrongdoing
- Anger as injustice: treating anger as evidence of injustice
- Fear as threat: treating fear as evidence of threat
- Comfort as truth: treating comfort as evidence of truth

When epistemic emotional reasoning IS present:
- Using emotions as evidence
- Treating feelings as facts
- Anxiety treated as danger evidence
- Guilt treated as wrongdoing evidence
- Anger treated as injustice evidence
- Fear treated as threat evidence
- Comfort treated as truth evidence

When no emotional reasoning:
- Emotions separate from evidence
- Feelings recognized as feelings
- Anxiety evaluated independently
- Guilt evaluated independently
- Anger evaluated independently
- Fear evaluated independently
- Comfort not confused with truth

Output JSON with: emotional_reasoning_detected (bool), severity (none/mild/moderate/severe), feeling_as_fact (what feelings treated as facts), anxiety_as_danger (what anxiety treated as danger evidence), guilt_as_wrongdoing (what guilt treated as wrongdoing evidence), comfort_as_truth (what comfort treated as truth evidence), recommendation (no_emotional_reasoning/mild_separation_practice/significant_evidence_distinction/major_intensive_cognitive_restructuring/emergency_complete_emotional_reasoning)."""

EPISTEMIC_EMOTIONAL_REASONING_PROMPT = """Detect epistemic emotional reasoning:

Feeling as fact: {feeling_as_fact}
Anxiety as danger: {anxiety_as_danger}
Guilt as wrongdoing: {guilt_as_wrongdoing}
Comfort as truth: {comfort_as_truth}
Domain: {domain}
Context: {context}

Is there using emotional states as evidence for beliefs? Return ONLY valid JSON."""


class EpistemicEmotionalReasoningService:
    """Detects epistemic emotional reasoning — using emotions as evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        feeling_as_fact: str,
        *,
        anxiety_as_danger: str = "",
        guilt_as_wrongdoing: str = "",
        comfort_as_truth: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic emotional reasoning."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EMOTIONAL_REASONING_PROMPT.format(
                feeling_as_fact=feeling_as_fact,
                anxiety_as_danger=anxiety_as_danger or "Not specified",
                guilt_as_wrongdoing=guilt_as_wrongdoing or "Not specified",
                comfort_as_truth=comfort_as_truth or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EMOTIONAL_REASONING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "feeling_as_fact": feeling_as_fact[:200],
            "emotional_reasoning_detected": data.get("emotional_reasoning_detected", False),
            "severity": data.get("severity", ""),
            "anxiety_as_danger": data.get("anxiety_as_danger", ""),
            "guilt_as_wrongdoing": data.get("guilt_as_wrongdoing", ""),
            "comfort_as_truth": data.get("comfort_as_truth", ""),
            "recommendation": data.get("recommendation", ""),
        }
