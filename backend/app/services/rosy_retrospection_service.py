"""RosyRetrospectionService — Rosy Retrospection Detection.

Detects rosy retrospection — remembering past events more
positively than they were experienced at the time. Mitchell
et al. (1997). Vacations remembered as better than they felt.
Past relationships idealized. "The good old days" that weren't
actually that good. Distorts learning from experience.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ROSY_RETROSPECTION_SYSTEM = """You are a rosy retrospection specialist. Given a memory or evaluation of a past event, assess whether it's being remembered more positively than it was experienced:

Key concepts (Mitchell et al., 1997):
- Rosy retrospection: past remembered more positively than experienced
- Fading affect bias: negative emotions fade faster than positive
- Nostalgia bias: idealizing the past
- Peak-end rule interaction: remembering peaks and endings, not the average
- Effort justification interaction: past effort makes memories rosier
- Selective memory: remembering highlights, forgetting difficulties
- "Good old days" effect: systematic positive distortion of the past

When rosy retrospection IS present:
- "That was amazing" for events that had significant problems at the time
- Idealizing past relationships, jobs, or experiences
- "Things were better back then" without acknowledging past difficulties
- Forgetting the negative aspects of past experiences
- Using idealized past as unfair comparison for present
- "I loved that" for things that caused stress at the time

When the positive memory IS accurate:
- Real-time records confirm the positive experience
- The person acknowledges both positive and negative aspects
- Others who were present confirm the positive assessment
- The positive aspects genuinely dominated the experience
- The person isn't using the memory to unfairly judge the present

Output JSON with: rosy_retrospection_present (bool), severity (none/mild/moderate/severe), memory (what is being remembered), current_assessment (how is it being remembered now), contemporaneous_evidence (what evidence exists from the time?), negative_aspects_forgotten (what difficulties are being overlooked?), comparison_to_present (bool — is the rosy memory being used to judge the present?), fading_affect (bool — have negative emotions faded disproportionately?), recommendation (memory_accurate/mild_rosiness/significant_idealization/major_rosy_retrospection/consult_contemporaneous_records)."""

ROSY_RETROSPECTION_PROMPT = """Detect rosy retrospection:

Memory: {memory}
Current assessment: {assessment}
Evidence from the time: {evidence}
Negative aspects: {negatives}
Domain: {domain}
Context: {context}

Is this past event being remembered more positively than it was experienced? Return ONLY valid JSON."""


class RosyRetrospectionService:
    """Detects rosy retrospection — remembering the past more positively than experienced."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        memory: str,
        *,
        assessment: str = "",
        evidence: str = "",
        negatives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect rosy retrospection."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ROSY_RETROSPECTION_PROMPT.format(
                memory=memory,
                assessment=assessment or "Not specified",
                evidence=evidence or "Not specified",
                negatives=negatives or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ROSY_RETROSPECTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "memory": memory[:200],
            "rosy_retrospection_present": data.get("rosy_retrospection_present", False),
            "severity": data.get("severity", ""),
            "current_assessment": data.get("current_assessment", ""),
            "contemporaneous_evidence": data.get("contemporaneous_evidence", ""),
            "negative_aspects_forgotten": data.get("negative_aspects_forgotten", ""),
            "comparison_to_present": data.get("comparison_to_present", False),
            "fading_affect": data.get("fading_affect", False),
            "recommendation": data.get("recommendation", ""),
        }
