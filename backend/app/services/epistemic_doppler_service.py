"""EpistemicDopplerService — Epistemic Doppler Effect Detection.

Detects epistemic Doppler effect — the apparent frequency of ideas
shifting based on the relative motion between source and observer.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DOPPLER_SYSTEM = """You are an epistemic Doppler effect specialist. Given an idea frequency shift pattern, assess whether relative motion causes apparent frequency changes:

Key concepts:
- Epistemic Doppler effect: frequency shift from relative motion
- Blue shift: ideas appearing higher frequency when approaching
- Red shift: ideas appearing lower frequency when receding
- Relative velocity: speed of approach or recession
- Source frequency: actual frequency of the idea
- Observed frequency: apparent frequency to the observer
- Sonic boom: ideas arriving faster than their own propagation

When epistemic Doppler effect IS present:
- Apparent frequency of ideas shifting from relative motion
- Ideas appearing more urgent/important when approaching
- Ideas appearing less urgent/important when receding
- Speed of approach or recession affecting perception
- Actual importance different from perceived importance
- Apparent importance depending on observer's motion
- Ideas arriving faster than they can be processed

When stationary perception is present:
- Ideas perceived at their actual frequency
- No shift from approach or recession
- Importance not affected by motion
- No relative velocity effects
- Actual and perceived importance aligned
- Observer motion not affecting perception
- Ideas arriving at processable rate

Output JSON with: doppler_present (bool), severity (none/mild/moderate/severe), blue_shift (what appears more urgent), red_shift (what appears less urgent), velocity (what relative motion), sonic_boom (what arrives too fast), recommendation (stationary_perception/mild_shift/significant_doppler/major_frequency_distortion/account_for_relative_motion)."""

EPISTEMIC_DOPPLER_PROMPT = """Detect epistemic Doppler effect:

Blue shift: {blue_shift}
Red shift: {red_shift}
Velocity: {velocity}
Sonic boom: {sonic_boom}
Domain: {domain}
Context: {context}

Is the apparent frequency of ideas shifting based on the relative motion between source and observer? Return ONLY valid JSON."""


class EpistemicDopplerService:
    """Detects epistemic Doppler effect — frequency shift from relative motion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        blue_shift: str,
        *,
        red_shift: str = "",
        velocity: str = "",
        sonic_boom: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic Doppler effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DOPPLER_PROMPT.format(
                blue_shift=blue_shift,
                red_shift=red_shift or "Not specified",
                velocity=velocity or "Not specified",
                sonic_boom=sonic_boom or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DOPPLER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "blue_shift": blue_shift[:200],
            "doppler_present": data.get("doppler_present", False),
            "severity": data.get("severity", ""),
            "red_shift": data.get("red_shift", ""),
            "velocity": data.get("velocity", ""),
            "sonic_boom": data.get("sonic_boom", ""),
            "recommendation": data.get("recommendation", ""),
        }
