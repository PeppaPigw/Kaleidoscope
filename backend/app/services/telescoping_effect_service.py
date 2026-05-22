"""TelescopingEffectService — Telescoping Effect Detection.

Detects telescoping effect — perceiving recent events as more
distant (forward telescoping) or distant events as more recent
(backward telescoping). Leads to distorted time perception,
inaccurate frequency estimates, and poor temporal planning.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TELESCOPING_SYSTEM = """You are a telescoping effect specialist. Given a temporal judgment, assess whether the person's perception of when events occurred is distorted:

Key concepts:
- Forward telescoping: recent events perceived as more distant than they are
- Backward telescoping: distant events perceived as more recent than they are
- Temporal compression: time periods feel shorter in retrospect
- Temporal expansion: time periods feel longer in retrospect
- Landmark events: significant events anchor temporal perception
- Frequency estimation: telescoping distorts "how often" judgments
- Duration neglect: poor estimation of how long things took

When telescoping IS present:
- "That was ages ago" for something that happened recently
- "That just happened" for something from years ago
- Inaccurate frequency estimates based on distorted time perception
- Planning based on wrong assumptions about how long things take
- "We haven't done X in forever" when it was recent
- Significant events seeming more recent than they are

When the temporal judgment IS accurate:
- The person has checked dates/records
- The time estimate is consistent with documented timelines
- Others confirm the temporal assessment
- The person acknowledges uncertainty in their time estimates
- Calendar or records support the claimed timing

Output JSON with: telescoping_present (bool), severity (none/mild/moderate/severe), event (what event's timing is being judged), perceived_timing (when does the person think it happened), actual_timing (when did it actually happen), direction (forward or backward telescoping), distortion_magnitude (how far off is the perception?), impact_on_decisions (how does this affect decisions?), frequency_distortion (bool — does this distort frequency estimates?), recommendation (timing_accurate/mild_telescoping/significant_temporal_distortion/major_telescoping/verify_with_records)."""

TELESCOPING_PROMPT = """Detect telescoping effect:

Event: {event}
Perceived timing: {perceived}
Actual timing: {actual}
Impact: {impact}
Domain: {domain}
Context: {context}

Is the person's perception of when this event occurred distorted? Return ONLY valid JSON."""


class TelescopingEffectService:
    """Detects telescoping effect — distorted perception of when events occurred."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        event: str,
        *,
        perceived: str = "",
        actual: str = "",
        impact: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect telescoping effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TELESCOPING_PROMPT.format(
                event=event,
                perceived=perceived or "Not specified",
                actual=actual or "Not specified",
                impact=impact or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=TELESCOPING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "event": event[:200],
            "telescoping_present": data.get("telescoping_present", False),
            "severity": data.get("severity", ""),
            "perceived_timing": data.get("perceived_timing", ""),
            "actual_timing": data.get("actual_timing", ""),
            "direction": data.get("direction", ""),
            "distortion_magnitude": data.get("distortion_magnitude", ""),
            "impact_on_decisions": data.get("impact_on_decisions", ""),
            "frequency_distortion": data.get("frequency_distortion", False),
            "recommendation": data.get("recommendation", ""),
        }
