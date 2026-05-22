"""EpistemicPolarizationFilterService — Epistemic Polarization Filter Detection.

Detects epistemic polarization filter — only allowing ideas vibrating
in one plane to pass while blocking all others.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_POLARIZATION_FILTER_SYSTEM = """You are an epistemic polarization filter specialist. Given an idea filtering pattern, assess whether only ideas in one plane are allowed through:

Key concepts:
- Epistemic polarization filter: only one plane of ideas passes
- Transmission axis: which orientation passes through
- Extinction: complete blocking of perpendicular ideas
- Malus's law: partial transmission at intermediate angles
- Cross-polarization: two filters blocking everything
- Depolarization: scrambling of idea orientation
- Birefringence: splitting ideas into two polarized beams

When epistemic polarization filter IS present:
- Only ideas vibrating in one plane allowed to pass
- Specific orientation determining what passes
- Complete blocking of perpendicular ideas
- Partial transmission of ideas at intermediate angles
- Multiple filters blocking everything
- Scrambling of idea orientation
- Ideas split into two polarized streams

When unpolarized transmission is present:
- All idea orientations passing equally
- No preferred orientation
- No blocking of any orientation
- Full transmission regardless of angle
- No cumulative filtering
- No scrambling needed
- Ideas remaining unified

Output JSON with: polarization_filter_present (bool), severity (none/mild/moderate/severe), axis (what orientation passes), extinction (what is completely blocked), cross (what multiple filters block), birefringence (what splitting occurs), recommendation (unpolarized_transmission/mild_filtering/significant_polarization/major_orientation_blocking/remove_filter)."""

EPISTEMIC_POLARIZATION_FILTER_PROMPT = """Detect epistemic polarization filter:

Axis: {axis}
Extinction: {extinction}
Cross: {cross}
Birefringence: {birefringence}
Domain: {domain}
Context: {context}

Are only ideas vibrating in one plane being allowed to pass while all others are blocked? Return ONLY valid JSON."""


class EpistemicPolarizationFilterService:
    """Detects epistemic polarization filter — only one plane passes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        axis: str,
        *,
        extinction: str = "",
        cross: str = "",
        birefringence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic polarization filter."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_POLARIZATION_FILTER_PROMPT.format(
                axis=axis,
                extinction=extinction or "Not specified",
                cross=cross or "Not specified",
                birefringence=birefringence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_POLARIZATION_FILTER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "axis": axis[:200],
            "polarization_filter_present": data.get("polarization_filter_present", False),
            "severity": data.get("severity", ""),
            "extinction": data.get("extinction", ""),
            "cross": data.get("cross", ""),
            "birefringence": data.get("birefringence", ""),
            "recommendation": data.get("recommendation", ""),
        }
