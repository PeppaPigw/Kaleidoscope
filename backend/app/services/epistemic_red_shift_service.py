"""EpistemicRedShiftService — Epistemic Red Shift Detection.

Detects epistemic red shift — ideas appearing to weaken or recede
as they move away from their origin context.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_RED_SHIFT_SYSTEM = """You are an epistemic red shift specialist. Given an idea transmission pattern, assess whether ideas weaken as they move from origin:

Key concepts:
- Epistemic red shift: ideas weakening as they move from origin context
- Distance decay: ideas losing energy with distance from source
- Context stretching: meaning stretching as context changes
- Origin dependence: ideas only strong near their origin
- Transmission loss: losing strength during transmission
- Wavelength stretching: meaning becoming more diffuse with distance
- Recession velocity: rate at which ideas recede from relevance

When red shift IS present:
- Ideas weakening as they move from origin context
- Ideas losing energy with distance from source
- Meaning stretching as context changes
- Ideas only strong near their origin
- Losing strength during transmission to new contexts
- Meaning becoming more diffuse with distance
- Ideas receding from relevance over time or distance

When stable transmission is present:
- Ideas maintaining strength across contexts
- No energy loss with distance from source
- Meaning preserved across context changes
- Ideas strong regardless of distance from origin
- Strength maintained during transmission
- Meaning remaining focused across distance
- Ideas maintaining relevance over time and distance

Output JSON with: red_shift_present (bool), severity (none/mild/moderate/severe), idea (what idea shows red shift), origin (what origin context), distance (how far from origin), weakening (how it weakens), recommendation (stable_transmission/mild_weakening/significant_red_shift/major_recession/anchor_to_new_context)."""

EPISTEMIC_RED_SHIFT_PROMPT = """Detect epistemic red shift:

Idea: {idea}
Origin: {origin}
Distance: {distance}
Weakening: {weakening}
Domain: {domain}
Context: {context}

Are ideas weakening or receding as they move away from their origin context? Return ONLY valid JSON."""


class EpistemicRedShiftService:
    """Detects epistemic red shift — ideas weakening with distance from origin."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        idea: str,
        *,
        origin: str = "",
        distance: str = "",
        weakening: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic red shift."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_RED_SHIFT_PROMPT.format(
                idea=idea,
                origin=origin or "Not specified",
                distance=distance or "Not specified",
                weakening=weakening or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_RED_SHIFT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "idea": idea[:200],
            "red_shift_present": data.get("red_shift_present", False),
            "severity": data.get("severity", ""),
            "origin": data.get("origin", ""),
            "distance": data.get("distance", ""),
            "weakening": data.get("weakening", ""),
            "recommendation": data.get("recommendation", ""),
        }
