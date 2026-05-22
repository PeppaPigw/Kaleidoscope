"""EpistemicUrgencyService — Epistemic Urgency Manipulation Detection.

Detects epistemic urgency manipulation — creating false time
pressure to prevent careful reasoning, forcing decisions before
adequate evidence can be gathered or evaluated.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_URGENCY_SYSTEM = """You are an epistemic urgency manipulation specialist. Given a decision situation, assess whether false urgency is preventing careful reasoning:

Key concepts:
- Epistemic urgency manipulation: false time pressure on reasoning
- Manufactured deadline: artificial time constraints
- Deliberation prevention: urgency blocking careful thought
- Evidence gathering prevention: no time to verify
- Panic epistemology: fear-driven reasoning shortcuts
- Now-or-never framing: false binary of act now or lose
- Urgency as authority: time pressure as argument

When epistemic urgency manipulation IS present:
- Time pressure manufactured to prevent reasoning
- Deadlines artificial and serve persuasion
- Urgency prevents evidence gathering
- Panic used to bypass careful evaluation
- Now-or-never framing when alternatives exist
- Time pressure used as argument for conclusion
- Deliberation treated as dangerous delay

When genuine urgency exists:
- Time constraints real and externally imposed
- Urgency acknowledged but reasoning still valued
- Best available evidence used within constraints
- Time pressure doesn't determine conclusion
- Urgency doesn't prevent all evaluation
- Constraints transparent and verifiable
- Speed and quality balanced appropriately

Output JSON with: manipulation_present (bool), severity (none/mild/moderate/severe), situation (what situation exists), urgency_source (where urgency comes from), artificial (what is artificial about it), prevented (what reasoning is prevented), recommendation (genuine_time_constraint/mild_urgency_pressure/significant_urgency_manipulation/major_deliberation_prevention/allow_adequate_reasoning)."""

EPISTEMIC_URGENCY_PROMPT = """Detect epistemic urgency manipulation:

Situation: {situation}
Time pressure: {pressure}
Deadline source: {deadline}
What's prevented: {prevented}
Domain: {domain}
Context: {context}

Is false urgency being used to prevent careful reasoning? Return ONLY valid JSON."""


class EpistemicUrgencyService:
    """Detects epistemic urgency manipulation — false time pressure on reasoning."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        pressure: str = "",
        deadline: str = "",
        prevented: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic urgency manipulation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_URGENCY_PROMPT.format(
                situation=situation,
                pressure=pressure or "Not specified",
                deadline=deadline or "Not specified",
                prevented=prevented or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_URGENCY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "manipulation_present": data.get("manipulation_present", False),
            "severity": data.get("severity", ""),
            "urgency_source": data.get("urgency_source", ""),
            "artificial": data.get("artificial", ""),
            "prevented": data.get("prevented", ""),
            "recommendation": data.get("recommendation", ""),
        }
