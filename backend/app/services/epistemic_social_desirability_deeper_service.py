"""EpistemicSocialDesirabilityDeeperService — Epistemic Social Desirability Detection.

Detects epistemic social desirability — shaping beliefs to be socially
acceptable rather than truthful.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SOCIAL_DESIRABILITY_DEEPER_SYSTEM = """You are an epistemic social desirability specialist. Given shaping beliefs for social acceptability, assess social desirability:

Key concepts:
- Epistemic social desirability: shaping beliefs to be socially acceptable
- Belief sanitization: sanitizing beliefs for public consumption
- Opinion management: managing opinions for social approval
- Thought policing: self-policing thoughts for acceptability
- Palatability bias: biasing toward palatable conclusions
- Respectability filter: filtering beliefs through respectability
- Audience pleasing: shaping beliefs to please audience

When epistemic social desirability IS present:
- Beliefs shaped for acceptability
- Beliefs sanitized for public
- Opinions managed for approval
- Thoughts self-policed
- Conclusions biased toward palatable
- Beliefs filtered through respectability
- Beliefs shaped to please

When no social desirability:
- Beliefs shaped by evidence
- Beliefs expressed honestly
- Opinions held genuinely
- Thoughts free
- Conclusions follow evidence
- Beliefs unfiltered
- Beliefs independent of audience

Output JSON with: social_desirability_detected (bool), severity (none/mild/moderate/severe), belief_sanitization (what beliefs sanitized), opinion_management (what opinions managed), thought_policing (what thoughts policed), palatability_bias (what biased toward palatable), recommendation (no_social_desirability/mild_honesty_practice/significant_authenticity_recovery/major_intensive_truth_commitment/emergency_complete_social_desirability)."""

EPISTEMIC_SOCIAL_DESIRABILITY_DEEPER_PROMPT = """Detect epistemic social desirability:

Belief sanitization: {belief_sanitization}
Opinion management: {opinion_management}
Thought policing: {thought_policing}
Palatability bias: {palatability_bias}
Domain: {domain}
Context: {context}

Are beliefs being shaped for social acceptability rather than truth? Return ONLY valid JSON."""


class EpistemicSocialDesirabilityDeeperService:
    """Detects epistemic social desirability — shaping beliefs for acceptability."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        belief_sanitization: str,
        *,
        opinion_management: str = "",
        thought_policing: str = "",
        palatability_bias: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic social desirability."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SOCIAL_DESIRABILITY_DEEPER_PROMPT.format(
                belief_sanitization=belief_sanitization,
                opinion_management=opinion_management or "Not specified",
                thought_policing=thought_policing or "Not specified",
                palatability_bias=palatability_bias or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SOCIAL_DESIRABILITY_DEEPER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "belief_sanitization": belief_sanitization[:200],
            "social_desirability_detected": data.get("social_desirability_detected", False),
            "severity": data.get("severity", ""),
            "opinion_management": data.get("opinion_management", ""),
            "thought_policing": data.get("thought_policing", ""),
            "palatability_bias": data.get("palatability_bias", ""),
            "recommendation": data.get("recommendation", ""),
        }
