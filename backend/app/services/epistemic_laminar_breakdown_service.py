"""EpistemicLaminarBreakdownService — Epistemic Laminar Breakdown Detection.

Detects epistemic laminar breakdown — smooth knowledge flow breaking
into chaotic turbulence at critical thresholds.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LAMINAR_BREAKDOWN_SYSTEM = """You are an epistemic laminar breakdown specialist. Given a knowledge flow transition, assess whether smooth flow is breaking into chaos:

Key concepts:
- Epistemic laminar breakdown: smooth flow transitioning to chaos
- Critical threshold: point where orderly flow breaks down
- Transition zone: unstable zone between order and chaos
- Perturbation sensitivity: small disturbances causing breakdown
- Flow rate excess: too much information for orderly processing
- Stability loss: losing the stability that maintained order
- Cascade failure: breakdown cascading through the system

When laminar breakdown IS present:
- Previously smooth knowledge flow breaking into chaos
- Critical threshold being exceeded
- System in unstable transition zone
- Small disturbances causing disproportionate breakdown
- Too much information for orderly processing
- Stability mechanisms failing
- Breakdown cascading through the system

When stable flow is present:
- Knowledge flow remaining smooth and orderly
- Well within processing capacity
- System in stable operating zone
- Disturbances absorbed without breakdown
- Information rate within processing capacity
- Stability mechanisms functioning
- No cascade risk

Output JSON with: breakdown_present (bool), severity (none/mild/moderate/severe), flow (what flow is breaking down), threshold (what threshold is exceeded), trigger (what triggers breakdown), cascade (how breakdown cascades), recommendation (stable_flow/mild_instability/significant_breakdown/major_cascade/reduce_flow_rate)."""

EPISTEMIC_LAMINAR_BREAKDOWN_PROMPT = """Detect epistemic laminar breakdown:

Flow: {flow}
Threshold: {threshold}
Trigger: {trigger}
Cascade: {cascade}
Domain: {domain}
Context: {context}

Is smooth knowledge flow breaking into chaotic turbulence? Return ONLY valid JSON."""


class EpistemicLaminarBreakdownService:
    """Detects epistemic laminar breakdown — smooth flow breaking into chaos."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        flow: str,
        *,
        threshold: str = "",
        trigger: str = "",
        cascade: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic laminar breakdown."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LAMINAR_BREAKDOWN_PROMPT.format(
                flow=flow,
                threshold=threshold or "Not specified",
                trigger=trigger or "Not specified",
                cascade=cascade or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LAMINAR_BREAKDOWN_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "flow": flow[:200],
            "breakdown_present": data.get("breakdown_present", False),
            "severity": data.get("severity", ""),
            "threshold": data.get("threshold", ""),
            "trigger": data.get("trigger", ""),
            "cascade": data.get("cascade", ""),
            "recommendation": data.get("recommendation", ""),
        }
