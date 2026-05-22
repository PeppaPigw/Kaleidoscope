"""BackfireEffectService — Backfire Effect Detection.

Detects the backfire effect — when corrections or contradicting
evidence actually strengthens the original misconception rather
than weakening it. Nyhan & Reifler (2010). People double down
on beliefs when challenged, especially on identity-relevant
topics. Related to belief perseverance but specifically about
the paradoxical strengthening from correction attempts.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

BACKFIRE_SYSTEM = """You are a backfire effect specialist. Given a correction attempt and its outcome, assess whether the backfire effect is strengthening the misconception:

Key concepts (Nyhan & Reifler, 2010):
- Backfire effect: corrections strengthen rather than weaken the misconception
- Worldview backfire: corrections that threaten worldview are rejected and belief strengthens
- Familiarity backfire: repeating the myth to correct it makes the myth more familiar
- Overkill backfire: too many counterarguments trigger suspicion
- Identity-protective cognition: beliefs tied to identity resist correction
- Motivated reasoning overlap: desire to maintain belief overrides evidence

When the backfire effect IS likely:
- The belief is tied to political/religious/cultural identity
- Correction threatens the person's worldview or self-concept
- The correction repeats the myth prominently
- The person has publicly committed to the belief
- The correction comes from an out-group source
- Emotional investment in the belief is high

When correction IS likely to work:
- The belief is not identity-relevant
- The correction comes from a trusted in-group source
- The person hasn't publicly committed to the belief
- The correction provides an alternative narrative (not just "you're wrong")
- The person's self-worth isn't threatened by being wrong
- The correction is delivered in a non-confrontational way

Output JSON with: backfire_risk (bool), severity (none/mild/moderate/severe), misconception (what belief is being corrected), correction_attempted (how the correction was delivered), identity_relevance (how tied to identity is the belief?), worldview_threat (bool — does correction threaten worldview?), familiarity_backfire_risk (bool — does correction repeat the myth?), source_credibility (is the corrector trusted by the believer?), public_commitment (bool — has the person publicly stated the belief?), emotional_investment (how emotionally invested in the belief?), alternative_narrative (bool — does the correction offer a replacement story?), self_affirmation (bool — is the person's self-worth protected?), likely_outcome (will the correction help, be neutral, or backfire?), better_approach (how to correct without triggering backfire), recommendation (correction_likely_effective/mild_backfire_risk/significant_backfire_risk/high_backfire_risk/use_alternative_approach)."""

BACKFIRE_PROMPT = """Detect backfire effect risk:

Misconception: {misconception}
Correction attempted: {correction}
Audience: {audience}
Response observed: {response}
Domain: {domain}
Context: {context}

Is the correction likely to backfire and strengthen the misconception? Return ONLY valid JSON."""


class BackfireEffectService:
    """Detects backfire effect — corrections strengthening misconceptions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        misconception: str,
        *,
        correction: str = "",
        audience: str = "",
        response: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect backfire effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BACKFIRE_PROMPT.format(
                misconception=misconception,
                correction=correction or "Not specified",
                audience=audience or "Not specified",
                response=response or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=BACKFIRE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "misconception": misconception[:200],
            "backfire_risk": data.get("backfire_risk", False),
            "severity": data.get("severity", ""),
            "correction_attempted": data.get("correction_attempted", ""),
            "identity_relevance": data.get("identity_relevance", ""),
            "worldview_threat": data.get("worldview_threat", False),
            "familiarity_backfire_risk": data.get("familiarity_backfire_risk", False),
            "source_credibility": data.get("source_credibility", ""),
            "public_commitment": data.get("public_commitment", False),
            "emotional_investment": data.get("emotional_investment", ""),
            "alternative_narrative": data.get("alternative_narrative", False),
            "self_affirmation": data.get("self_affirmation", False),
            "likely_outcome": data.get("likely_outcome", ""),
            "better_approach": data.get("better_approach", ""),
            "recommendation": data.get("recommendation", ""),
        }
