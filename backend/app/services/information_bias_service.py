"""InformationBiasService — Information Bias Detection.

Detects information bias — seeking additional information even
when it cannot affect the decision or action. Baron, Beattie
& Hershey (1988). More information feels better even when it's
irrelevant to the decision. Leads to analysis paralysis,
unnecessary testing, and delayed action. "Let's gather more
data" when the decision is already clear.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

INFORMATION_SYSTEM = """You are an information bias specialist. Given a decision-making situation, assess whether additional information seeking is genuinely useful or just delaying action:

Key concepts (Baron, Beattie & Hershey, 1988):
- Information bias: seeking information that cannot affect the decision
- Analysis paralysis: gathering data instead of acting
- Pseudodiagnosticity: seeking information that feels relevant but isn't
- Value of information: information only has value if it could change the decision
- Satisficing vs. maximizing: when is "enough" information enough?
- Decision avoidance: using "need more data" to avoid commitment

When information bias IS present:
- Seeking data that won't change the decision regardless of outcome
- "Let's do more research" when the answer is already clear
- Requesting tests/studies whose results won't affect the action plan
- Delaying decisions to gather information that's irrelevant to the choice
- Confusing feeling informed with being better positioned to decide
- Analysis paralysis disguised as thoroughness

When more information IS genuinely needed:
- The information could genuinely change the optimal decision
- The cost of being wrong exceeds the cost of delay
- Key uncertainties remain that the information would resolve
- The decision is irreversible and the information is obtainable
- Previous information was insufficient for the decision's stakes

Output JSON with: information_bias_present (bool), severity (none/mild/moderate/severe), decision (what decision is being delayed), information_sought (what additional information is being requested), decision_sensitivity (would the information actually change the decision?), cost_of_delay (what is lost by waiting for more information?), cost_of_wrong_decision (what is lost by deciding incorrectly?), current_confidence (how confident should the decision-maker already be?), irreversibility (can the decision be reversed if wrong?), avoidance_motive (bool — is information-seeking avoiding commitment?), diminishing_returns (bool — has additional info stopped adding value?), recommendation (information_needed/mild_information_bias/significant_analysis_paralysis/major_decision_avoidance/decide_now)."""

INFORMATION_PROMPT = """Detect information bias:

Decision: {decision}
Information sought: {information}
Current evidence: {evidence}
Delay cost: {delay}
Domain: {domain}
Context: {context}

Is additional information seeking genuinely useful or just delaying action? Return ONLY valid JSON."""


class InformationBiasService:
    """Detects information bias — seeking irrelevant information that delays decisions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        information: str = "",
        evidence: str = "",
        delay: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect information bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=INFORMATION_PROMPT.format(
                decision=decision,
                information=information or "Not specified",
                evidence=evidence or "Not specified",
                delay=delay or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=INFORMATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "information_bias_present": data.get("information_bias_present", False),
            "severity": data.get("severity", ""),
            "information_sought": data.get("information_sought", ""),
            "decision_sensitivity": data.get("decision_sensitivity", ""),
            "cost_of_delay": data.get("cost_of_delay", ""),
            "cost_of_wrong_decision": data.get("cost_of_wrong_decision", ""),
            "current_confidence": data.get("current_confidence", ""),
            "irreversibility": data.get("irreversibility", ""),
            "avoidance_motive": data.get("avoidance_motive", False),
            "diminishing_returns": data.get("diminishing_returns", False),
            "recommendation": data.get("recommendation", ""),
        }
