"""ConjunctionEffectService — Conjunction Effect Detection.

Detects conjunction effect — judging the conjunction of two
events as more probable than either event alone. Tversky &
Kahneman (1983). The "Linda problem": Linda is more likely
to be a bank teller than a feminist bank teller, but people
judge the conjunction as more probable because it's more
representative.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CONJUNCTION_EFFECT_SYSTEM = """You are a conjunction effect specialist. Given a probability judgment involving compound events, assess whether the conjunction fallacy is present:

Key concepts (Tversky & Kahneman, 1983):
- Conjunction fallacy: P(A∧B) judged > P(A) or P(B)
- Representativeness: conjunctions can be more representative
- Narrative coherence: adding detail makes stories more compelling
- Unpacking effect: detailed scenarios seem more likely
- Scenario thinking: specific scenarios feel more probable than general
- Availability interaction: detailed events easier to imagine
- Planning fallacy connection: specific plans seem more achievable

When conjunction effect IS present:
- A specific scenario judged more likely than a general one it's part of
- Adding qualifying details increases perceived probability
- "She's probably a feminist bank teller" > "She's probably a bank teller"
- Detailed plans judged more likely to succeed than simple ones
- Specific causes judged more likely than general categories
- "The market will crash due to X" judged more likely than "the market will crash"

When the judgment IS appropriate:
- The person is correctly conditioning on additional information
- The "conjunction" is actually a conditional probability
- The more specific category is genuinely more likely given evidence
- The judgment is about typicality, not probability
- The person acknowledges the logical constraint

Output JSON with: conjunction_effect_present (bool), severity (none/mild/moderate/severe), judgment (what probability judgment is being made), conjunction (what conjunction is being evaluated), component (what single event is it being compared to), logical_constraint (P(A∧B) ≤ P(A)), representativeness (how representative is the conjunction), narrative_coherence (does the conjunction tell a better story?), recommendation (judgment_appropriate/mild_conjunction/significant_conjunction_fallacy/major_probability_violation/decompose_into_components)."""

CONJUNCTION_EFFECT_PROMPT = """Detect conjunction effect:

Judgment: {judgment}
Specific scenario: {specific}
General scenario: {general}
Reasoning: {reasoning}
Domain: {domain}
Context: {context}

Is a conjunction being judged more probable than its components? Return ONLY valid JSON."""


class ConjunctionEffectService:
    """Detects conjunction effect — conjunctions judged more probable than components."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        specific: str = "",
        general: str = "",
        reasoning: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect conjunction effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CONJUNCTION_EFFECT_PROMPT.format(
                judgment=judgment,
                specific=specific or "Not specified",
                general=general or "Not specified",
                reasoning=reasoning or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CONJUNCTION_EFFECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "conjunction_effect_present": data.get("conjunction_effect_present", False),
            "severity": data.get("severity", ""),
            "conjunction": data.get("conjunction", ""),
            "component": data.get("component", ""),
            "logical_constraint": data.get("logical_constraint", ""),
            "representativeness": data.get("representativeness", ""),
            "narrative_coherence": data.get("narrative_coherence", ""),
            "recommendation": data.get("recommendation", ""),
        }
