"""EpistemicRunawayService — Epistemic Runaway Detection.

Detects epistemic runaway — positive feedback causing intellectual
positions to accelerate away from equilibrium without bound.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_RUNAWAY_SYSTEM = """You are an epistemic runaway specialist. Given an intellectual feedback pattern, assess whether positive feedback causes unbounded acceleration:

Key concepts:
- Epistemic runaway: positive feedback causing unbounded acceleration
- Positive feedback: output reinforcing input
- Gain margin: how much gain before instability
- Phase margin: how much phase shift before instability
- Saturation: physical limits preventing true infinity
- Thermal runaway: self-reinforcing heating
- Exponential growth: doubling time getting shorter

When epistemic runaway IS present:
- Positive feedback causing acceleration away from equilibrium
- Output reinforcing and amplifying input
- System approaching instability margins
- Phase relationships promoting instability
- Physical or logical limits being approached
- Self-reinforcing intensification
- Growth rate itself increasing

When stable feedback is present:
- Negative feedback maintaining equilibrium
- Output opposing and dampening input
- System well within stability margins
- Phase relationships promoting stability
- Far from any limits
- Self-correcting tendencies
- Constant or decreasing growth rate

Output JSON with: runaway_present (bool), severity (none/mild/moderate/severe), positive_feedback (what reinforcement), gain_margin (what instability distance), saturation (what limits), exponential (what growth pattern), recommendation (stable_feedback/mild_runaway/significant_runaway/major_positive_feedback/add_negative_feedback)."""

EPISTEMIC_RUNAWAY_PROMPT = """Detect epistemic runaway:

Positive feedback: {positive_feedback}
Gain margin: {gain_margin}
Saturation: {saturation}
Exponential: {exponential}
Domain: {domain}
Context: {context}

Is positive feedback causing intellectual positions to accelerate away from equilibrium without bound? Return ONLY valid JSON."""


class EpistemicRunawayService:
    """Detects epistemic runaway — positive feedback causing unbounded acceleration."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        positive_feedback: str,
        *,
        gain_margin: str = "",
        saturation: str = "",
        exponential: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic runaway."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_RUNAWAY_PROMPT.format(
                positive_feedback=positive_feedback,
                gain_margin=gain_margin or "Not specified",
                saturation=saturation or "Not specified",
                exponential=exponential or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_RUNAWAY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "positive_feedback": positive_feedback[:200],
            "runaway_present": data.get("runaway_present", False),
            "severity": data.get("severity", ""),
            "gain_margin": data.get("gain_margin", ""),
            "saturation": data.get("saturation", ""),
            "exponential": data.get("exponential", ""),
            "recommendation": data.get("recommendation", ""),
        }
