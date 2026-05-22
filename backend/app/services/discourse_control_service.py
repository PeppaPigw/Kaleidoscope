"""DiscourseControlService — Discourse Control Detection.

Detects discourse control — using power over language, framing,
and communication channels to shape what can be thought and said,
controlling the boundaries of acceptable discourse.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DISCOURSE_CONTROL_SYSTEM = """You are a discourse control specialist. Given a communication situation, assess whether discourse is being inappropriately controlled:

Key concepts:
- Discourse control: shaping what can be thought and said
- Framing power: controlling how issues are presented
- Overton window manipulation: shifting acceptable discourse
- Agenda setting: controlling what gets discussed
- Linguistic control: controlling available vocabulary
- Platform power: controlling who can speak where
- Narrative monopoly: controlling the dominant story

When discourse control IS present:
- Power used to shape what can be thought or said
- Framing controls how issues are understood
- Acceptable discourse boundaries manipulated
- Agenda set to exclude certain topics
- Language controlled to prevent certain thoughts
- Platform access used to silence perspectives
- Dominant narrative enforced through power

When discourse management is appropriate:
- Framing serves clarity and understanding
- Boundaries serve productive discussion
- Agenda reflects genuine priorities
- Language choices serve communication
- Platform rules serve quality discourse
- Multiple narratives can coexist
- Discourse norms transparent and fair

Output JSON with: control_present (bool), severity (none/mild/moderate/severe), situation (what situation exists), mechanism (what control mechanism operates), excluded (what discourse is excluded), beneficiary (who benefits from control), recommendation (appropriate_discourse_management/mild_framing_bias/significant_discourse_control/major_thought_control/open_discourse)."""

DISCOURSE_CONTROL_PROMPT = """Detect discourse control:

Situation: {situation}
Communication channel: {channel}
Framing used: {framing}
What's excluded: {excluded}
Domain: {domain}
Context: {context}

Is power being used to inappropriately control what can be thought and said? Return ONLY valid JSON."""


class DiscourseControlService:
    """Detects discourse control — shaping boundaries of acceptable discourse."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        channel: str = "",
        framing: str = "",
        excluded: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect discourse control."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DISCOURSE_CONTROL_PROMPT.format(
                situation=situation,
                channel=channel or "Not specified",
                framing=framing or "Not specified",
                excluded=excluded or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DISCOURSE_CONTROL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "control_present": data.get("control_present", False),
            "severity": data.get("severity", ""),
            "mechanism": data.get("mechanism", ""),
            "excluded": data.get("excluded", ""),
            "beneficiary": data.get("beneficiary", ""),
            "recommendation": data.get("recommendation", ""),
        }
