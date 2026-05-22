"""EpistemicCompassDriftService — Epistemic Compass Drift Detection.

Detects epistemic compass drift — orientation tools gradually
becoming unreliable without the user noticing.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMPASS_DRIFT_SYSTEM = """You are an epistemic compass drift specialist. Given an orientation tool, assess whether it is gradually becoming unreliable:

Key concepts:
- Epistemic compass drift: orientation tools gradually becoming unreliable
- Gradual unreliability: tools becoming less reliable over time
- Unnoticed drift: drift happening too slowly to notice
- Calibration loss: tools losing their calibration
- False north: tools pointing to false reference points
- Trust inertia: continuing to trust tools that have drifted
- Recalibration needed: tools needing recalibration

When compass drift IS present:
- Orientation tools gradually becoming unreliable
- Tools becoming less reliable without being noticed
- Drift happening too slowly to detect
- Tools losing their calibration over time
- Tools pointing to false reference points
- Continuing to trust tools that have drifted
- Tools needing recalibration but not getting it

When reliable orientation is present:
- Orientation tools maintaining reliability
- Tools regularly checked for accuracy
- Any drift detected promptly
- Tools maintaining calibration
- Tools pointing to true reference points
- Trust in tools warranted by their accuracy
- Tools regularly recalibrated

Output JSON with: compass_drift (bool), severity (none/mild/moderate/severe), tool (what orientation tool is drifting), drift (how it has drifted), unnoticed (why drift is unnoticed), false_north (what false reference it points to), recommendation (reliable_orientation/mild_drift/significant_compass_drift/major_false_north/recalibrate_tools)."""

EPISTEMIC_COMPASS_DRIFT_PROMPT = """Detect epistemic compass drift:

Tool: {tool}
Drift: {drift}
Unnoticed: {unnoticed}
False north: {false_north}
Domain: {domain}
Context: {context}

Are orientation tools gradually becoming unreliable without being noticed? Return ONLY valid JSON."""


class EpistemicCompassDriftService:
    """Detects epistemic compass drift — orientation tools becoming unreliable."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        tool: str,
        *,
        drift: str = "",
        unnoticed: str = "",
        false_north: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic compass drift."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMPASS_DRIFT_PROMPT.format(
                tool=tool,
                drift=drift or "Not specified",
                unnoticed=unnoticed or "Not specified",
                false_north=false_north or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMPASS_DRIFT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "tool": tool[:200],
            "compass_drift": data.get("compass_drift", False),
            "severity": data.get("severity", ""),
            "drift": data.get("drift", ""),
            "unnoticed": data.get("unnoticed", ""),
            "false_north": data.get("false_north", ""),
            "recommendation": data.get("recommendation", ""),
        }
