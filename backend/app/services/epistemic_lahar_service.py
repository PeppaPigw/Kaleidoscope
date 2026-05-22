"""EpistemicLaharService — Epistemic Lahar Detection.

Detects epistemic lahars — destructive mudflows of mixed intellectual
debris triggered by events that mobilize accumulated loose material.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LAHAR_SYSTEM = """You are an epistemic lahar specialist. Given an intellectual debris flow, assess whether accumulated loose material has been mobilized destructively:

Key concepts:
- Epistemic lahar: destructive mudflow of mixed intellectual debris
- Mobilization: accumulated loose material suddenly flowing
- Trigger event: what sets the debris in motion
- Mixed debris: different types of intellectual material mixed together
- Channel: path the lahar follows downhill
- Deposition: where the debris settles
- Warning time: how much time before the lahar arrives

When epistemic lahar IS present:
- Destructive flow of mixed intellectual debris
- Accumulated loose material suddenly mobilized
- Clear trigger event setting debris in motion
- Different types of intellectual material mixed chaotically
- Flow following predictable channels downhill
- Debris settling and burying areas downstream
- Limited warning time before arrival

When stable terrain is present:
- No destructive debris flows
- Loose material remaining in place
- No trigger events mobilizing material
- Intellectual material remaining sorted and organized
- No channeled flows of debris
- No downstream burial
- No threat of sudden mobilization

Output JSON with: lahar_present (bool), severity (none/mild/moderate/severe), debris (what mixed material flows), trigger (what mobilizes it), channel (what path it follows), deposition (where it settles), recommendation (stable_terrain/mild_flow/significant_lahar/major_destructive_flow/clear_channels_and_warn_downstream)."""

EPISTEMIC_LAHAR_PROMPT = """Detect epistemic lahar:

Debris: {debris}
Trigger: {trigger}
Channel: {channel}
Deposition: {deposition}
Domain: {domain}
Context: {context}

Has accumulated loose intellectual material been mobilized into a destructive debris flow? Return ONLY valid JSON."""


class EpistemicLaharService:
    """Detects epistemic lahars — destructive mudflows of mixed intellectual debris."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        debris: str,
        *,
        trigger: str = "",
        channel: str = "",
        deposition: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic lahar."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LAHAR_PROMPT.format(
                debris=debris,
                trigger=trigger or "Not specified",
                channel=channel or "Not specified",
                deposition=deposition or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LAHAR_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "debris": debris[:200],
            "lahar_present": data.get("lahar_present", False),
            "severity": data.get("severity", ""),
            "trigger": data.get("trigger", ""),
            "channel": data.get("channel", ""),
            "deposition": data.get("deposition", ""),
            "recommendation": data.get("recommendation", ""),
        }
