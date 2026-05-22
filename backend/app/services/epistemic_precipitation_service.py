"""EpistemicPrecipitationService — Epistemic Precipitation Detection.

Detects epistemic precipitation — dissolved assumptions suddenly
becoming visible and falling out of solution.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PRECIPITATION_SYSTEM = """You are an epistemic precipitation specialist. Given a belief system, assess whether dissolved assumptions are suddenly becoming visible:

Key concepts:
- Epistemic precipitation: dissolved assumptions becoming visible
- Assumption revelation: hidden assumptions suddenly revealed
- Solution saturation: belief system saturated with assumptions
- Crystallization trigger: trigger causing assumptions to precipitate
- Visibility shift: invisible assumptions becoming visible
- Falling out: assumptions falling out of background
- Supersaturation: system holding more assumptions than stable

When epistemic precipitation IS present:
- Dissolved assumptions suddenly becoming visible
- Hidden assumptions suddenly revealed
- Belief system saturated and precipitating assumptions
- Trigger causing assumptions to become visible
- Previously invisible assumptions becoming visible
- Assumptions falling out of background into foreground
- System holding more assumptions than it can sustain

When stable solution is present:
- Assumptions appropriately integrated
- Assumptions visible and acknowledged
- Belief system at stable capacity
- No sudden revelations needed
- Assumptions already visible
- Background assumptions appropriate
- System at sustainable capacity

Output JSON with: precipitation_present (bool), severity (none/mild/moderate/severe), assumptions (what assumptions precipitate), trigger (what triggers precipitation), visibility (what becomes visible), saturation (how saturated the system was), recommendation (stable_solution/mild_revelation/significant_precipitation/major_assumption_cascade/examine_precipitated_assumptions)."""

EPISTEMIC_PRECIPITATION_PROMPT = """Detect epistemic precipitation:

Assumptions: {assumptions}
Trigger: {trigger}
Visibility: {visibility}
Saturation: {saturation}
Domain: {domain}
Context: {context}

Are dissolved assumptions suddenly becoming visible and falling out of solution? Return ONLY valid JSON."""


class EpistemicPrecipitationService:
    """Detects epistemic precipitation — dissolved assumptions becoming visible."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        assumptions: str,
        *,
        trigger: str = "",
        visibility: str = "",
        saturation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic precipitation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PRECIPITATION_PROMPT.format(
                assumptions=assumptions,
                trigger=trigger or "Not specified",
                visibility=visibility or "Not specified",
                saturation=saturation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PRECIPITATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "assumptions": assumptions[:200],
            "precipitation_present": data.get("precipitation_present", False),
            "severity": data.get("severity", ""),
            "trigger": data.get("trigger", ""),
            "visibility": data.get("visibility", ""),
            "saturation": data.get("saturation", ""),
            "recommendation": data.get("recommendation", ""),
        }
