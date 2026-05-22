"""AmbiguityEffectService — Ambiguity Effect Detection.

Detects the ambiguity effect — avoiding options where the
probability of a favorable outcome is unknown, even when the
expected value is higher. Ellsberg (1961). People prefer known
risks over unknown risks. A 50% known chance is preferred over
an unknown probability even if it might be 70%. Drives
excessive conservatism and missed opportunities.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

AMBIGUITY_SYSTEM = """You are an ambiguity effect specialist. Given a decision under uncertainty, assess whether ambiguity aversion is causing suboptimal choices:

Key concepts (Ellsberg, 1961):
- Ambiguity effect: preferring known probabilities over unknown ones
- Ellsberg paradox: violating expected utility theory due to ambiguity aversion
- Known unknowns vs. unknown unknowns: people handle the former better
- Competence hypothesis: people avoid domains where they feel less knowledgeable
- Home bias: preferring familiar investments over potentially better foreign ones
- Status quo bias overlap: the known option feels safer

When the ambiguity effect IS present:
- Choosing a known-probability option over a potentially better unknown one
- Avoiding new markets/technologies because outcomes are uncertain
- Preferring "the devil you know" when exploration might be better
- Excessive conservatism driven by discomfort with uncertainty
- Refusing to act because probabilities can't be precisely quantified
- "We don't know enough" as a reason to stick with inferior known options

When ambiguity avoidance IS rational:
- The stakes are catastrophic and uncertainty is genuinely dangerous
- The cost of being wrong is asymmetric (ruin risk)
- More information is cheaply available and worth waiting for
- The known option is genuinely good enough
- Regulatory or fiduciary duties require known-probability choices

Output JSON with: ambiguity_effect_present (bool), severity (none/mild/moderate/severe), decision (what choice is being made), known_option (the option with known probabilities), ambiguous_option (the option with unknown probabilities), known_expected_value (expected value of the known option), ambiguous_potential (potential value of the ambiguous option), information_available (what could be learned to reduce ambiguity?), cost_of_learning (how expensive is it to reduce the ambiguity?), stakes (how serious are the consequences?), reversibility (can the decision be reversed?), competence_factor (bool — is unfamiliarity driving the avoidance?), opportunity_cost (what is lost by avoiding the ambiguous option?), recommendation (avoidance_rational/mild_ambiguity_effect/significant_missed_opportunity/major_ambiguity_aversion/explore_the_unknown)."""

AMBIGUITY_PROMPT = """Detect ambiguity effect:

Decision: {decision}
Known option: {known}
Ambiguous option: {ambiguous}
Reasoning: {reasoning}
Domain: {domain}
Context: {context}

Is ambiguity aversion causing suboptimal choices? Return ONLY valid JSON."""


class AmbiguityEffectService:
    """Detects ambiguity effect — avoiding options with unknown probabilities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        known: str = "",
        ambiguous: str = "",
        reasoning: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect ambiguity effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=AMBIGUITY_PROMPT.format(
                decision=decision,
                known=known or "Not specified",
                ambiguous=ambiguous or "Not specified",
                reasoning=reasoning or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=AMBIGUITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "ambiguity_effect_present": data.get("ambiguity_effect_present", False),
            "severity": data.get("severity", ""),
            "known_option": data.get("known_option", ""),
            "ambiguous_option": data.get("ambiguous_option", ""),
            "known_expected_value": data.get("known_expected_value", ""),
            "ambiguous_potential": data.get("ambiguous_potential", ""),
            "information_available": data.get("information_available", ""),
            "cost_of_learning": data.get("cost_of_learning", ""),
            "stakes": data.get("stakes", ""),
            "reversibility": data.get("reversibility", ""),
            "competence_factor": data.get("competence_factor", False),
            "opportunity_cost": data.get("opportunity_cost", ""),
            "recommendation": data.get("recommendation", ""),
        }
