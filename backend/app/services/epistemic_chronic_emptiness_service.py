"""EpistemicChronicEmptinessService — Epistemic Chronic Emptiness Detection.

Detects epistemic chronic emptiness — persistent sense of intellectual
void, meaninglessness, or absence of genuine intellectual engagement.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CHRONIC_EMPTINESS_SYSTEM = """You are an epistemic chronic emptiness specialist. Given persistent intellectual void, assess chronic emptiness:

Key concepts:
- Epistemic chronic emptiness: persistent intellectual void
- Meaning absence: nothing feels intellectually meaningful
- Engagement failure: unable to genuinely engage with ideas
- Hollowness: going through intellectual motions without substance
- Boredom depth: profound unstimulable intellectual boredom
- Connection void: no felt connection to knowledge
- Purpose absence: no intellectual direction or purpose

When epistemic chronic emptiness IS present:
- Persistent intellectual void
- Nothing feels meaningful
- Unable to genuinely engage
- Going through motions
- Profound unstimulable boredom
- No felt connection to knowledge
- No intellectual direction

When no chronic emptiness:
- Intellectual fullness
- Meaningful engagement
- Genuine interest
- Substantive participation
- Stimulated curiosity
- Connected to knowledge
- Clear intellectual purpose

Output JSON with: chronic_emptiness_detected (bool), severity (none/mild/moderate/severe), meaning_absence (what not meaningful), engagement_failure (what not engaging), hollowness_pattern (what going through motions), purpose_absence (what no direction), recommendation (no_chronic_emptiness/mild_meaning_exploration/significant_engagement_rebuilding/major_intensive_purpose_therapy/emergency_severe_void)."""

EPISTEMIC_CHRONIC_EMPTINESS_PROMPT = """Detect epistemic chronic emptiness:

Meaning absence: {meaning_absence}
Engagement failure: {engagement_failure}
Hollowness pattern: {hollowness_pattern}
Purpose absence: {purpose_absence}
Domain: {domain}
Context: {context}

Is there persistent sense of intellectual void or meaninglessness? Return ONLY valid JSON."""


class EpistemicChronicEmptinessService:
    """Detects epistemic chronic emptiness — persistent intellectual void."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        meaning_absence: str,
        *,
        engagement_failure: str = "",
        hollowness_pattern: str = "",
        purpose_absence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic chronic emptiness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CHRONIC_EMPTINESS_PROMPT.format(
                meaning_absence=meaning_absence,
                engagement_failure=engagement_failure or "Not specified",
                hollowness_pattern=hollowness_pattern or "Not specified",
                purpose_absence=purpose_absence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CHRONIC_EMPTINESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "meaning_absence": meaning_absence[:200],
            "chronic_emptiness_detected": data.get("chronic_emptiness_detected", False),
            "severity": data.get("severity", ""),
            "engagement_failure": data.get("engagement_failure", ""),
            "hollowness_pattern": data.get("hollowness_pattern", ""),
            "purpose_absence": data.get("purpose_absence", ""),
            "recommendation": data.get("recommendation", ""),
        }
