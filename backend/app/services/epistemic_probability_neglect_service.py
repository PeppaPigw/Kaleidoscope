"""EpistemicProbabilityNeglectService — Epistemic Probability Neglect Detection.

Detects epistemic probability neglect — ignoring probability entirely,
treating all possibilities as equally likely or as certainties.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PROBABILITY_NEGLECT_SYSTEM = """You are an epistemic probability neglect specialist. Given ignored probabilities, assess probability neglect:

Key concepts:
- Epistemic probability neglect: ignoring probability entirely
- Binary thinking: treating probabilities as 0 or 1
- Possibility-certainty confusion: treating possibility as certainty
- Equal probability assumption: assuming all outcomes equally likely
- Probability flattening: flattening probability distributions
- Worst case fixation: fixating on worst case regardless of probability
- Best case fixation: fixating on best case regardless of probability

When epistemic probability neglect IS present:
- Probabilities ignored
- Binary thinking applied
- Possibility treated as certainty
- Equal probability assumed
- Distributions flattened
- Worst case fixated on
- Best case fixated on

When no probability neglect:
- Probabilities considered
- Gradations acknowledged
- Possibility distinguished from certainty
- Probabilities estimated
- Distributions respected
- Cases weighted by probability
- Expected value considered

Output JSON with: probability_neglect_detected (bool), severity (none/mild/moderate/severe), binary_thinking (what binary thinking), possibility_certainty_confusion (what possibility-certainty confused), equal_probability_assumption (what equal probability assumed), worst_case_fixation (what worst case fixated), recommendation (no_probability_neglect/mild_probability_awareness/significant_probability_estimation/major_intensive_probabilistic_thinking/emergency_complete_probability_neglect)."""

EPISTEMIC_PROBABILITY_NEGLECT_PROMPT = """Detect epistemic probability neglect:

Binary thinking: {binary_thinking}
Possibility-certainty confusion: {possibility_certainty_confusion}
Equal probability assumption: {equal_probability_assumption}
Worst case fixation: {worst_case_fixation}
Domain: {domain}
Context: {context}

Is probability being ignored entirely in reasoning? Return ONLY valid JSON."""


class EpistemicProbabilityNeglectService:
    """Detects epistemic probability neglect — probabilities ignored."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        binary_thinking: str,
        *,
        possibility_certainty_confusion: str = "",
        equal_probability_assumption: str = "",
        worst_case_fixation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic probability neglect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PROBABILITY_NEGLECT_PROMPT.format(
                binary_thinking=binary_thinking,
                possibility_certainty_confusion=possibility_certainty_confusion or "Not specified",
                equal_probability_assumption=equal_probability_assumption or "Not specified",
                worst_case_fixation=worst_case_fixation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PROBABILITY_NEGLECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "binary_thinking": binary_thinking[:200],
            "probability_neglect_detected": data.get("probability_neglect_detected", False),
            "severity": data.get("severity", ""),
            "possibility_certainty_confusion": data.get("possibility_certainty_confusion", ""),
            "equal_probability_assumption": data.get("equal_probability_assumption", ""),
            "worst_case_fixation": data.get("worst_case_fixation", ""),
            "recommendation": data.get("recommendation", ""),
        }
