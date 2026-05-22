"""CertaintyEffectService — Certainty Effect Detection.

Detects certainty effect — overweighting outcomes that are
considered certain relative to outcomes that are merely
probable. Kahneman & Tversky (1979). People prefer a sure
$3000 over an 80% chance of $4000 (EV=$3200). The jump
from 99% to 100% feels much larger than from 60% to 61%.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CERTAINTY_EFFECT_SYSTEM = """You are a certainty effect specialist. Given a decision under uncertainty, assess whether the certainty effect is distorting probability weighting:

Key concepts (Kahneman & Tversky, 1979):
- Certainty effect: overweighting certain outcomes vs probable ones
- Probability weighting: non-linear transformation of probabilities
- Allais paradox: violations of expected utility due to certainty preference
- Possibility effect: overweighting small probabilities (lottery tickets)
- Sure thing preference: choosing certainty even at lower expected value
- Risk elimination premium: paying disproportionately to eliminate last bit of risk
- Pseudo-certainty: treating high probability as certainty

When certainty effect IS present:
- Choosing a sure $X over a higher-EV gamble
- Paying a premium to eliminate the last 1% of risk
- "I'd rather have the guaranteed outcome"
- Preferring certain small gains over probable large gains
- Overvaluing insurance that provides complete coverage
- Rejecting positive-EV opportunities because outcome isn't guaranteed
- The jump from "almost certain" to "certain" driving the decision

When the preference IS rational:
- The person genuinely cannot afford the downside
- Utility is concave enough to justify the certainty premium
- There are real costs to uncertainty (planning, stress)
- The certain option has other advantages beyond certainty
- The probabilities are genuinely uncertain (ambiguity)

Output JSON with: certainty_effect_present (bool), severity (none/mild/moderate/severe), decision (what decision is being made), certain_option (what is the certain option), uncertain_option (what is the uncertain option), expected_values (EV comparison), probability_weight (how is probability being weighted), certainty_premium (how much is being paid for certainty), rational_justification (is there a rational reason for certainty preference?), recommendation (preference_rational/mild_certainty_effect/significant_certainty_premium/major_probability_distortion/compare_expected_values)."""

CERTAINTY_EFFECT_PROMPT = """Detect certainty effect:

Decision: {decision}
Certain option: {certain}
Uncertain option: {uncertain}
Probabilities: {probabilities}
Domain: {domain}
Context: {context}

Is the certainty effect distorting probability weighting? Return ONLY valid JSON."""


class CertaintyEffectService:
    """Detects certainty effect — overweighting certain outcomes vs probable ones."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        certain: str = "",
        uncertain: str = "",
        probabilities: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect certainty effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CERTAINTY_EFFECT_PROMPT.format(
                decision=decision,
                certain=certain or "Not specified",
                uncertain=uncertain or "Not specified",
                probabilities=probabilities or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CERTAINTY_EFFECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "certainty_effect_present": data.get("certainty_effect_present", False),
            "severity": data.get("severity", ""),
            "certain_option": data.get("certain_option", ""),
            "uncertain_option": data.get("uncertain_option", ""),
            "expected_values": data.get("expected_values", ""),
            "probability_weight": data.get("probability_weight", ""),
            "certainty_premium": data.get("certainty_premium", ""),
            "rational_justification": data.get("rational_justification", ""),
            "recommendation": data.get("recommendation", ""),
        }
