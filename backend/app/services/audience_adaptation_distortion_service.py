"""AudienceAdaptationDistortionService — Audience Adaptation Distortion Detection.

Detects audience adaptation distortion — distorting claims when adapting
for different audiences, where simplification or emphasis changes
the substance of what is communicated.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

AUDIENCE_ADAPTATION_DISTORTION_SYSTEM = """You are an audience adaptation distortion specialist. Given a communication adapted for an audience, assess whether adaptation has distorted the substance:

Key concepts:
- Audience adaptation distortion: substance changed for audience
- Simplification distortion: simplifying changes meaning
- Emphasis distortion: emphasis shifts changing substance
- Register distortion: changing register changes claims
- Palatability distortion: making palatable changes truth
- Framing for audience: audience-specific framing changing content
- Translation infidelity: adapting message unfaithfully

When audience adaptation distortion IS present:
- Simplification changes the substance of claims
- Emphasis shifts alter what is actually communicated
- Adapting for audience changes the truth of claims
- Making palatable changes what is actually said
- Different audiences receiving substantively different claims
- Translation between registers losing critical content
- Adaptation serving persuasion over accuracy

When appropriate adaptation is present:
- Simplification preserves core substance
- Emphasis appropriate to audience needs
- Adaptation changes form not substance
- Palatability achieved without distortion
- Different audiences receiving same substance differently expressed
- Register changes preserving meaning
- Adaptation serving communication not manipulation

Output JSON with: distortion_present (bool), severity (none/mild/moderate/severe), communication (what is communicated), original (original substance), adapted (adapted version), distortion (what is distorted), recommendation (appropriate_adaptation/mild_simplification_loss/significant_adaptation_distortion/major_substance_change/preserve_substance_across_adaptations)."""

AUDIENCE_ADAPTATION_DISTORTION_PROMPT = """Detect audience adaptation distortion:

Communication: {communication}
Original claim: {original}
Adapted version: {adapted}
Target audience: {audience}
Domain: {domain}
Context: {context}

Is audience adaptation distorting the substance of what is communicated? Return ONLY valid JSON."""


class AudienceAdaptationDistortionService:
    """Detects audience adaptation distortion — adaptation changing substance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        communication: str,
        *,
        original: str = "",
        adapted: str = "",
        audience: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect audience adaptation distortion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=AUDIENCE_ADAPTATION_DISTORTION_PROMPT.format(
                communication=communication,
                original=original or "Not specified",
                adapted=adapted or "Not specified",
                audience=audience or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=AUDIENCE_ADAPTATION_DISTORTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "communication": communication[:200],
            "distortion_present": data.get("distortion_present", False),
            "severity": data.get("severity", ""),
            "original": data.get("original", ""),
            "adapted": data.get("adapted", ""),
            "distortion": data.get("distortion", ""),
            "recommendation": data.get("recommendation", ""),
        }
