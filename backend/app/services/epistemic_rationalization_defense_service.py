"""EpistemicRationalizationDefenseService — Epistemic Rationalization Defense Detection.

Detects epistemic rationalization defense — constructing logical-sounding
justifications for beliefs actually held for emotional or irrational reasons.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_RATIONALIZATION_DEFENSE_SYSTEM = """You are an epistemic rationalization defense specialist. Given post-hoc justification construction, assess rationalization:

Key concepts:
- Epistemic rationalization defense: constructing justifications for irrational beliefs
- Post-hoc reasoning: finding reasons after the conclusion
- Motivated logic: reasoning serves emotional needs
- Plausible cover: justification sounds reasonable but isn't real reason
- Self-deception: believing own false justification
- Coherence illusion: making irrational seem rational
- Reason as servant: logic serving emotion rather than truth

When epistemic rationalization defense IS present:
- Constructing justifications
- Finding reasons after conclusion
- Reasoning serves emotion
- Sounds reasonable but isn't real
- Believing own false justification
- Making irrational seem rational
- Logic serving emotion

When no rationalization defense:
- Genuine reasoning
- Reasons precede conclusion
- Reasoning serves truth
- Real reasons stated
- Honest self-assessment
- Rational is rational
- Logic serving truth

Output JSON with: rationalization_defense_detected (bool), severity (none/mild/moderate/severe), post_hoc_pattern (what finding after), motivated_logic (what serving emotion), plausible_cover (what sounds reasonable), self_deception (what believing false), recommendation (no_rationalization/mild_honesty_practice/significant_motivation_therapy/major_intensive_truth_seeking/emergency_complete_self_deception)."""

EPISTEMIC_RATIONALIZATION_DEFENSE_PROMPT = """Detect epistemic rationalization defense:

Post hoc pattern: {post_hoc_pattern}
Motivated logic: {motivated_logic}
Plausible cover: {plausible_cover}
Self deception: {self_deception}
Domain: {domain}
Context: {context}

Is there construction of logical justifications for beliefs held for emotional reasons? Return ONLY valid JSON."""


class EpistemicRationalizationDefenseService:
    """Detects epistemic rationalization defense — post-hoc justification."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        post_hoc_pattern: str,
        *,
        motivated_logic: str = "",
        plausible_cover: str = "",
        self_deception: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic rationalization defense."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_RATIONALIZATION_DEFENSE_PROMPT.format(
                post_hoc_pattern=post_hoc_pattern,
                motivated_logic=motivated_logic or "Not specified",
                plausible_cover=plausible_cover or "Not specified",
                self_deception=self_deception or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_RATIONALIZATION_DEFENSE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "post_hoc_pattern": post_hoc_pattern[:200],
            "rationalization_defense_detected": data.get("rationalization_defense_detected", False),
            "severity": data.get("severity", ""),
            "motivated_logic": data.get("motivated_logic", ""),
            "plausible_cover": data.get("plausible_cover", ""),
            "self_deception": data.get("self_deception", ""),
            "recommendation": data.get("recommendation", ""),
        }
