"""AudienceCaptureService — Audience Capture Detection.

Detects audience capture — when a communicator's message is shaped
by their audience's expectations rather than truth or their own
genuine beliefs, leading to performative rather than authentic communication.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

AUDIENCE_CAPTURE_SYSTEM = """You are an audience capture specialist. Given a communication, assess whether the message is shaped by audience expectations rather than truth:

Key concepts:
- Audience capture: message shaped by audience, not truth
- Performative communication: saying what audience wants to hear
- Feedback loop: audience rewards drive message evolution
- Authenticity erosion: genuine beliefs replaced by popular ones
- Platform incentives: engagement metrics driving content
- Echo chamber amplification: extreme positions rewarded
- Audience-pleasing: prioritizing approval over accuracy

When audience capture IS present:
- Message shaped by what audience wants to hear
- Truth sacrificed for audience approval
- Positions evolving toward audience preferences
- Engagement metrics driving content choices
- Authentic beliefs replaced by popular ones
- Extreme positions adopted for audience reaction
- Communication performative rather than genuine

When audience awareness is appropriate:
- Message adapted for audience understanding (not beliefs)
- Audience considered for communication style, not content
- Truth maintained while making accessible
- Audience feedback improves clarity, not changes substance
- Platform used strategically without compromising truth
- Audience awareness serves communication, not approval
- Adaptation is pedagogical, not performative

Output JSON with: capture_present (bool), severity (none/mild/moderate/severe), communication (what is communicated), audience_pressure (what audience expects), authentic_position (what genuine position might be), adaptation (how message is adapted), recommendation (appropriate_audience_awareness/mild_audience_pleasing/significant_audience_capture/major_authenticity_loss/communicate_authentically)."""

AUDIENCE_CAPTURE_PROMPT = """Detect audience capture:

Communication: {communication}
Audience: {audience}
Incentives: {incentives}
Authentic position: {authentic}
Domain: {domain}
Context: {context}

Is the message being shaped by audience expectations rather than truth? Return ONLY valid JSON."""


class AudienceCaptureService:
    """Detects audience capture — message shaped by audience rather than truth."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        communication: str,
        *,
        audience: str = "",
        incentives: str = "",
        authentic: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect audience capture."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=AUDIENCE_CAPTURE_PROMPT.format(
                communication=communication,
                audience=audience or "Not specified",
                incentives=incentives or "Not specified",
                authentic=authentic or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=AUDIENCE_CAPTURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "communication": communication[:200],
            "capture_present": data.get("capture_present", False),
            "severity": data.get("severity", ""),
            "audience_pressure": data.get("audience_pressure", ""),
            "authentic_position": data.get("authentic_position", ""),
            "adaptation": data.get("adaptation", ""),
            "recommendation": data.get("recommendation", ""),
        }
