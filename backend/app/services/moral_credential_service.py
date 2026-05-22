"""MoralCredentialService — Moral Credential Effect Detection.

Detects moral credential effect — past good behavior licensing
future bad behavior. Monin & Miller (2001). "I donated to
charity last week, so I can be selfish today." Past virtue
creates a psychological license to act less virtuously.
Leads to inconsistent ethical behavior and rationalized
transgressions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MORAL_CREDENTIAL_SYSTEM = """You are a moral credential effect specialist. Given a justification for behavior, assess whether past good actions are being used to license current questionable behavior:

Key concepts (Monin & Miller, 2001):
- Moral credentials: past good behavior creates license for future bad behavior
- Licensing effect: having established virtue, one feels free to transgress
- Moral bank account: treating ethics like a balance that can be drawn down
- Self-concept maintenance: "I'm a good person" allows occasional bad acts
- Compensatory ethics: "I already did my part" justifying inaction
- Progressive credentials: past progressive actions licensing current bias
- Moral self-licensing: the mechanism by which credentials enable transgression

When moral credentialing IS present:
- "I hired a diverse candidate last time, so I can go with my gut this time"
- Past charitable giving used to justify current selfishness
- Previous ethical behavior cited to excuse current questionable action
- "I've been good, so I deserve to..." followed by problematic behavior
- Using past sacrifices to justify current indulgence
- Treating ethics as a bank account rather than consistent principles

When the justification IS legitimate:
- Past behavior is genuinely relevant to current credibility
- The person is not using past good to excuse current bad
- The behavior being justified is actually acceptable on its own merits
- Past actions demonstrate genuine commitment, not just credential-building
- The person would justify the current action even without the past credential

Output JSON with: moral_credential_present (bool), severity (none/mild/moderate/severe), current_behavior (what is being justified), past_credential (what past good behavior is cited), licensing_mechanism (how does the past justify the present?), behavior_acceptable_independently (bool — is the current behavior OK on its own?), ethical_consistency (is the person being ethically consistent?), bank_account_thinking (bool — treating ethics as a balance?), who_is_affected (who is affected by the licensed behavior?), recommendation (justification_legitimate/mild_credentialing/significant_licensing/major_moral_credential/evaluate_behavior_independently)."""

MORAL_CREDENTIAL_PROMPT = """Detect moral credential effect:

Behavior: {behavior}
Justification: {justification}
Past actions: {past_actions}
Pattern: {pattern}
Domain: {domain}
Context: {context}

Is past good behavior being used to license current questionable behavior? Return ONLY valid JSON."""


class MoralCredentialService:
    """Detects moral credential effect — past virtue licensing current transgression."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        behavior: str,
        *,
        justification: str = "",
        past_actions: str = "",
        pattern: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect moral credential effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MORAL_CREDENTIAL_PROMPT.format(
                behavior=behavior,
                justification=justification or "Not specified",
                past_actions=past_actions or "Not specified",
                pattern=pattern or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MORAL_CREDENTIAL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "behavior": behavior[:200],
            "moral_credential_present": data.get("moral_credential_present", False),
            "severity": data.get("severity", ""),
            "current_behavior": data.get("current_behavior", ""),
            "past_credential": data.get("past_credential", ""),
            "licensing_mechanism": data.get("licensing_mechanism", ""),
            "behavior_acceptable_independently": data.get("behavior_acceptable_independently", True),
            "ethical_consistency": data.get("ethical_consistency", ""),
            "bank_account_thinking": data.get("bank_account_thinking", False),
            "who_is_affected": data.get("who_is_affected", ""),
            "recommendation": data.get("recommendation", ""),
        }
