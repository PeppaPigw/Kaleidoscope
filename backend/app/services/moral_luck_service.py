"""MoralLuckService — Moral Luck Detection.

Detects moral luck — judging the morality of actions based on
outcomes rather than the decision quality at the time. Nagel
(1979). A drunk driver who gets home safely is judged less
harshly than one who hits someone, even though the decision
(to drive drunk) was equally wrong. Outcome shouldn't affect
moral judgment of the decision.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MORAL_LUCK_SYSTEM = """You are a moral luck specialist. Given a moral judgment, assess whether the judgment is inappropriately influenced by outcomes that were beyond the agent's control:

Key concepts (Nagel, 1979; Williams, 1981):
- Moral luck: moral judgment influenced by factors beyond agent's control
- Resultant luck: outcomes affecting moral assessment of identical decisions
- Circumstantial luck: circumstances one finds oneself in
- Constitutive luck: the kind of person one is (genetics, upbringing)
- Causal luck: how one's actions are determined by prior causes
- Outcome-independent evaluation: judging decisions by information available at the time
- Moral responsibility: should only attach to what's within one's control

When moral luck IS present:
- Judging identical decisions differently based on different outcomes
- "They got lucky" excusing the same risky behavior that's condemned when it fails
- Praising a decision that happened to work out despite being reckless
- Condemning a decision that was reasonable but had bad luck
- Hindsight moral judgment: "they should have known" when they couldn't have
- Different punishment for same action based on outcome severity

When outcome-based judgment IS appropriate:
- The outcome reveals information about the decision quality
- The person had control over the factors that led to the outcome
- The outcome was foreseeable given the decision
- Consequentialist ethics are being deliberately applied
- The judgment accounts for both decision quality and outcome

Output JSON with: moral_luck_present (bool), severity (none/mild/moderate/severe), action (what action is being judged), outcome (what outcome occurred), moral_judgment (how is the action being judged), decision_quality (was the decision reasonable given available information?), outcome_controllable (bool — was the outcome within the agent's control?), same_decision_different_outcome (would the judgment change with a different outcome?), information_available (what did the agent know at decision time?), recommendation (judgment_appropriate/mild_outcome_influence/significant_moral_luck/major_outcome_based_morality/judge_decision_not_outcome)."""

MORAL_LUCK_PROMPT = """Detect moral luck:

Action: {action}
Outcome: {outcome}
Judgment: {judgment}
Decision context: {decision_context}
Domain: {domain}
Context: {context}

Is the moral judgment inappropriately influenced by outcomes beyond the agent's control? Return ONLY valid JSON."""


class MoralLuckService:
    """Detects moral luck — judging morality based on outcomes rather than decisions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        action: str,
        *,
        outcome: str = "",
        judgment: str = "",
        decision_context: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect moral luck."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MORAL_LUCK_PROMPT.format(
                action=action,
                outcome=outcome or "Not specified",
                judgment=judgment or "Not specified",
                decision_context=decision_context or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MORAL_LUCK_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "action": action[:200],
            "moral_luck_present": data.get("moral_luck_present", False),
            "severity": data.get("severity", ""),
            "decision_quality": data.get("decision_quality", ""),
            "outcome_controllable": data.get("outcome_controllable", True),
            "same_decision_different_outcome": data.get("same_decision_different_outcome", ""),
            "information_available": data.get("information_available", ""),
            "recommendation": data.get("recommendation", ""),
        }
