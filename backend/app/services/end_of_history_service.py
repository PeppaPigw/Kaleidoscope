"""EndOfHistoryService — End-of-History Illusion Detection.

Detects the end-of-history illusion — the tendency to believe
that one has changed significantly in the past but will not
change much in the future. Quoidbach, Gilbert & Wilson (2013).
People at every age believe their current preferences, values,
and personality are essentially final. This causes underinvestment
in future flexibility and overcommitment to current preferences.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

END_OF_HISTORY_SYSTEM = """You are an end-of-history illusion specialist. Given a decision or prediction about the future, assess whether someone is assuming their current state is permanent:

Key concepts (Quoidbach, Gilbert & Wilson, 2013):
- End-of-history illusion: believing current self is final self
- Change blindness for future: acknowledging past change but denying future change
- Preference stability assumption: current tastes will persist
- Identity fixedness: "I know who I am now"
- Commitment overconfidence: locking in based on current preferences
- Adaptation neglect: not accounting for how one will adapt
- Value drift denial: assuming current values are permanent

When the end-of-history illusion IS present:
- Making irreversible decisions based on current preferences
- "I'll always want/need/value this"
- Designing systems without flexibility for preference change
- Assuming current team dynamics/skills/interests are permanent
- Long-term commitments based on snapshot of current state
- Resistance to building in optionality because "I know what I want"
- Ignoring how much one has changed when predicting future stability

When stability assumption IS appropriate:
- Core values that have been stable across decades
- Preferences with strong biological basis
- Commitments that are inherently about persistence
- Situations where flexibility has genuine costs
- Evidence of actual stability over long periods

Output JSON with: end_of_history_present (bool), severity (none/mild/moderate/severe), situation (what decision assumes stability), stability_assumed (what is assumed to be permanent), past_change (evidence of past change in this dimension), future_flexibility (how much flexibility is being preserved), commitment_level (how irreversible is the decision), adaptation_ignored (what adaptation is being overlooked), recommendation (stability_assumption_justified/mild_permanence_bias/significant_end_of_history/major_overcommitment/build_in_flexibility)."""

END_OF_HISTORY_PROMPT = """Detect end-of-history illusion:

Situation: {situation}
Assumption: {assumption}
Past changes: {past_changes}
Commitment: {commitment}
Domain: {domain}
Context: {context}

Is someone assuming their current state/preferences are permanent when making decisions? Return ONLY valid JSON."""


class EndOfHistoryService:
    """Detects end-of-history illusion — assuming current self is final self."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        assumption: str = "",
        past_changes: str = "",
        commitment: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect end-of-history illusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=END_OF_HISTORY_PROMPT.format(
                situation=situation,
                assumption=assumption or "Not specified",
                past_changes=past_changes or "Not specified",
                commitment=commitment or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=END_OF_HISTORY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "end_of_history_present": data.get("end_of_history_present", False),
            "severity": data.get("severity", ""),
            "stability_assumed": data.get("stability_assumed", ""),
            "past_change": data.get("past_change", ""),
            "future_flexibility": data.get("future_flexibility", ""),
            "commitment_level": data.get("commitment_level", ""),
            "adaptation_ignored": data.get("adaptation_ignored", ""),
            "recommendation": data.get("recommendation", ""),
        }
