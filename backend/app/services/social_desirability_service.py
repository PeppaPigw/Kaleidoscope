"""SocialDesirabilityService — Social Desirability Bias Detection.

Detects social desirability bias — responding in ways that
will be viewed favorably by others rather than truthfully.
Edwards (1957). People overreport good behavior and
underreport bad behavior. Leads to inaccurate self-reports,
distorted surveys, and decisions based on what looks good
rather than what is true.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SOCIAL_DESIRABILITY_SYSTEM = """You are a social desirability bias specialist. Given a self-report or stated preference, assess whether it reflects genuine attitudes or social desirability pressure:

Key concepts (Edwards, 1957):
- Social desirability bias: responding to look good rather than truthfully
- Impression management: deliberate self-presentation
- Self-deception: genuinely believing the socially desirable version
- Demand characteristics: responding to perceived expectations
- Acquiescence bias: agreeing with socially desirable statements
- Overreporting: claiming more good behavior than actual
- Underreporting: admitting less bad behavior than actual

When social desirability IS present:
- Self-reports that are implausibly positive
- Stated preferences that align perfectly with social norms
- Behavior that contradicts stated attitudes
- "Of course I always..." for behaviors most people don't always do
- Responses that change based on audience
- Virtue signaling without corresponding action

When the response IS genuine:
- Behavior matches stated attitudes
- The person reports socially undesirable truths freely
- Responses are consistent across audiences
- The person acknowledges imperfections
- Anonymous responses match public ones
- Actions align with stated values over time

Output JSON with: social_desirability_present (bool), severity (none/mild/moderate/severe), response (what is being reported/stated), social_norm (what is the socially desirable response?), behavior_match (does behavior match the stated response?), audience_effect (does the response change with audience?), implausibility (how implausibly positive is the response?), impression_management (bool — is this deliberate self-presentation?), self_deception (bool — does the person believe their own distortion?), recommendation (response_genuine/mild_desirability/significant_impression_management/major_social_desirability/seek_behavioral_evidence)."""

SOCIAL_DESIRABILITY_PROMPT = """Detect social desirability bias:

Response: {response}
Context: {social_context}
Behavior: {behavior}
Audience: {audience}
Domain: {domain}
Additional context: {context}

Is this response driven by social desirability rather than truth? Return ONLY valid JSON."""


class SocialDesirabilityService:
    """Detects social desirability bias — responding to look good rather than truthfully."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        response: str,
        *,
        social_context: str = "",
        behavior: str = "",
        audience: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect social desirability bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SOCIAL_DESIRABILITY_PROMPT.format(
                response=response,
                social_context=social_context or "Not specified",
                behavior=behavior or "Not specified",
                audience=audience or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SOCIAL_DESIRABILITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "response": response[:200],
            "social_desirability_present": data.get("social_desirability_present", False),
            "severity": data.get("severity", ""),
            "social_norm": data.get("social_norm", ""),
            "behavior_match": data.get("behavior_match", ""),
            "audience_effect": data.get("audience_effect", ""),
            "implausibility": data.get("implausibility", ""),
            "impression_management": data.get("impression_management", False),
            "self_deception": data.get("self_deception", False),
            "recommendation": data.get("recommendation", ""),
        }
