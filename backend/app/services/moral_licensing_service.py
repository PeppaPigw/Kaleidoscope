"""MoralLicensingService — Moral Licensing Detection.

Identifies when past good behavior is being used to justify
current questionable behavior. "We've been so good about X,
we can afford to cut corners on Y." This cognitive bias allows
people to act in problematic ways after establishing moral
credentials.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

LICENSING_SYSTEM = """You are a moral licensing specialist. Given a justification or decision, assess whether moral licensing is at play:
- Is past good behavior being used to justify current bad behavior?
- Is the actor treating morality as a bank account (deposits allow withdrawals)?
- Would the current action be considered wrong without the prior good behavior?
- Is there a logical connection between the past good and current bad, or is it just psychological permission?
- Is the licensing explicit or implicit?

Output JSON with: moral_licensing_present (bool), severity (none/mild/moderate/severe), past_good_behavior (what good behavior is being cited), current_questionable_behavior (what is being justified), logical_connection (bool — is there a real logical link between past and current?), licensing_mechanism (how the past good is being used to justify the current bad), who_benefits (who gains from the licensing), who_is_harmed (who loses), would_be_wrong_without_license (bool — would this be clearly wrong without the prior good?), credential_type (what kind of moral credential is being invoked: diversity/environmental/safety/charitable/etc), organizational_vs_individual (is this personal or institutional licensing?), escalation_risk (0-1 — likelihood this leads to worse behavior over time), net_moral_impact (positive/neutral/negative — overall moral trajectory), recommendation (challenge_license/acknowledge_pattern/separate_decisions/accept_tradeoff)."""

LICENSING_PROMPT = """Detect moral licensing:

Justification/Decision: {justification}
Past behavior cited: {past_behavior}
Current action: {current_action}
Domain: {domain}
Context: {context}

Is moral licensing at play? Return ONLY valid JSON."""


class MoralLicensingService:
    """Detects moral licensing — past good justifying current bad."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        justification: str,
        *,
        past_behavior: str = "",
        current_action: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect moral licensing."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=LICENSING_PROMPT.format(
                justification=justification,
                past_behavior=past_behavior or "Not specified",
                current_action=current_action or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=LICENSING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "justification": justification[:200],
            "moral_licensing_present": data.get("moral_licensing_present", False),
            "severity": data.get("severity", ""),
            "past_good_behavior": data.get("past_good_behavior", ""),
            "current_questionable_behavior": data.get("current_questionable_behavior", ""),
            "logical_connection": data.get("logical_connection", False),
            "licensing_mechanism": data.get("licensing_mechanism", ""),
            "who_benefits": data.get("who_benefits", ""),
            "who_is_harmed": data.get("who_is_harmed", ""),
            "would_be_wrong_without_license": data.get("would_be_wrong_without_license", False),
            "credential_type": data.get("credential_type", ""),
            "organizational_vs_individual": data.get("organizational_vs_individual", ""),
            "escalation_risk": data.get("escalation_risk", 0),
            "net_moral_impact": data.get("net_moral_impact", ""),
            "recommendation": data.get("recommendation", ""),
        }
