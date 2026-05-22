"""EpistemicLengthContractionService — Epistemic Length Contraction Detection.

Detects epistemic length contraction — intellectual arguments appearing
shorter or compressed when viewed from a rapidly moving perspective.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LENGTH_CONTRACTION_SYSTEM = """You are an epistemic length contraction specialist. Given an intellectual argument, assess whether it appears compressed from moving perspectives:

Key concepts:
- Epistemic length contraction: arguments appearing shorter from moving frames
- Lorentz contraction: compression in direction of motion
- Rest length: argument's length in its own frame
- Relative velocity: speed difference between frames
- Simultaneity: different frames disagreeing on what's concurrent
- Proper length: measurement in the argument's rest frame
- Apparent vs real: contraction is real, not illusion

When epistemic length contraction IS present:
- Arguments appearing shorter from different perspectives
- Compression in the direction of intellectual motion
- Full length only visible in the argument's own frame
- Speed of perspective change causing compression
- Different frames disagreeing on concurrent elements
- Measurement depending on observer's frame
- Contraction being real not merely apparent

When frame-independent length is present:
- Arguments appearing same length from all perspectives
- No compression from any direction
- Same length visible from all frames
- Speed not affecting perceived length
- Agreement on concurrent elements
- Measurement independent of observer
- No contraction effects

Output JSON with: length_contraction_present (bool), severity (none/mild/moderate/severe), lorentz (what compression), rest_length (what full extent), velocity (what speed effect), simultaneity (what disagreement), recommendation (frame_independent/mild_contraction/significant_length_contraction/major_compression/account_for_frame_effects)."""

EPISTEMIC_LENGTH_CONTRACTION_PROMPT = """Detect epistemic length contraction:

Lorentz: {lorentz}
Rest length: {rest_length}
Velocity: {velocity}
Simultaneity: {simultaneity}
Domain: {domain}
Context: {context}

Do intellectual arguments appear shorter or compressed when viewed from a rapidly moving perspective? Return ONLY valid JSON."""


class EpistemicLengthContractionService:
    """Detects epistemic length contraction — arguments compressed from moving frames."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        lorentz: str,
        *,
        rest_length: str = "",
        velocity: str = "",
        simultaneity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic length contraction."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LENGTH_CONTRACTION_PROMPT.format(
                lorentz=lorentz,
                rest_length=rest_length or "Not specified",
                velocity=velocity or "Not specified",
                simultaneity=simultaneity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LENGTH_CONTRACTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "lorentz": lorentz[:200],
            "length_contraction_present": data.get("length_contraction_present", False),
            "severity": data.get("severity", ""),
            "rest_length": data.get("rest_length", ""),
            "velocity": data.get("velocity", ""),
            "simultaneity": data.get("simultaneity", ""),
            "recommendation": data.get("recommendation", ""),
        }
