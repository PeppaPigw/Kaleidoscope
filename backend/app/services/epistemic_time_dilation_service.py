"""EpistemicTimeDilationService — Epistemic Time Dilation Detection.

Detects epistemic time dilation — intellectual processes appearing to
slow down when observed from a different reference frame or perspective.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TIME_DILATION_SYSTEM = """You are an epistemic time dilation specialist. Given an intellectual process, assess whether it appears to slow from different perspectives:

Key concepts:
- Epistemic time dilation: processes slowing from different frames
- Reference frame: observer's perspective
- Proper time: time in the process's own frame
- Coordinate time: time as seen from outside
- Velocity: speed of intellectual change
- Gravitational: proximity to massive ideas slowing time
- Twin paradox: different aging of parallel processes

When epistemic time dilation IS present:
- Processes appearing slower from different perspectives
- Different observers measuring different durations
- Internal time differing from external observation
- External measurement showing different rate
- Speed of intellectual change affecting perception
- Proximity to dominant ideas slowing progress
- Parallel processes aging differently

When uniform time is present:
- Processes appearing same speed from all perspectives
- All observers measuring same duration
- Internal and external time matching
- Consistent measurement from all frames
- Speed not affecting time perception
- No gravitational time effects
- Parallel processes aging equally

Output JSON with: time_dilation_present (bool), severity (none/mild/moderate/severe), reference_frame (what perspective difference), proper_time (what internal rate), gravitational (what mass effect), twin_paradox (what differential aging), recommendation (uniform_time/mild_dilation/significant_time_dilation/major_frame_dependence/synchronize_reference_frames)."""

EPISTEMIC_TIME_DILATION_PROMPT = """Detect epistemic time dilation:

Reference frame: {reference_frame}
Proper time: {proper_time}
Gravitational: {gravitational}
Twin paradox: {twin_paradox}
Domain: {domain}
Context: {context}

Do intellectual processes appear to slow down when observed from a different reference frame or perspective? Return ONLY valid JSON."""


class EpistemicTimeDilationService:
    """Detects epistemic time dilation — processes slowing from different frames."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reference_frame: str,
        *,
        proper_time: str = "",
        gravitational: str = "",
        twin_paradox: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic time dilation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TIME_DILATION_PROMPT.format(
                reference_frame=reference_frame,
                proper_time=proper_time or "Not specified",
                gravitational=gravitational or "Not specified",
                twin_paradox=twin_paradox or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TIME_DILATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "reference_frame": reference_frame[:200],
            "time_dilation_present": data.get("time_dilation_present", False),
            "severity": data.get("severity", ""),
            "proper_time": data.get("proper_time", ""),
            "gravitational": data.get("gravitational", ""),
            "twin_paradox": data.get("twin_paradox", ""),
            "recommendation": data.get("recommendation", ""),
        }
