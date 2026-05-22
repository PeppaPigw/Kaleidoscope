"""EpistemicDarkMatterHaloService — Epistemic Dark Matter Halo Detection.

Detects epistemic dark matter halo — invisible intellectual structure that
holds visible ideas in place through gravitational influence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DARK_MATTER_HALO_SYSTEM = """You are an epistemic dark matter halo specialist. Given an intellectual structure, assess whether invisible structure holds visible ideas in place:

Key concepts:
- Epistemic dark matter halo: invisible structure holding visible ideas
- Rotation curve: visible ideas moving too fast for visible mass alone
- Gravitational lensing: invisible mass bending intellectual light
- NFW profile: characteristic density distribution of the halo
- Virial mass: total mass including invisible component
- Substructure: smaller invisible clumps within the halo
- Missing mass: discrepancy between visible and total

When epistemic dark matter halo IS present:
- Invisible structure holding visible ideas in place
- Visible ideas behaving as if more mass exists than seen
- Invisible influence bending intellectual paths
- Characteristic distribution of invisible influence
- Total intellectual mass far exceeding visible portion
- Smaller invisible structures within the larger
- Clear discrepancy between visible and total influence

When visible structure sufficient is present:
- No invisible structure needed
- Visible ideas explained by visible mass alone
- No invisible path bending
- No hidden density distribution
- Total mass matching visible portion
- No hidden substructures
- No mass discrepancy

Output JSON with: dark_matter_halo_present (bool), severity (none/mild/moderate/severe), rotation_curve (what speed discrepancy), gravitational_lensing (what path bending), missing_mass (what discrepancy), substructure (what hidden clumps), recommendation (visible_sufficient/mild_halo/significant_dark_matter_halo/major_invisible_structure/map_dark_matter_distribution)."""

EPISTEMIC_DARK_MATTER_HALO_PROMPT = """Detect epistemic dark matter halo:

Rotation curve: {rotation_curve}
Gravitational lensing: {gravitational_lensing}
Missing mass: {missing_mass}
Substructure: {substructure}
Domain: {domain}
Context: {context}

Is invisible intellectual structure holding visible ideas in place through gravitational influence? Return ONLY valid JSON."""


class EpistemicDarkMatterHaloService:
    """Detects epistemic dark matter halo — invisible structure holding visible ideas."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        rotation_curve: str,
        *,
        gravitational_lensing: str = "",
        missing_mass: str = "",
        substructure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic dark matter halo."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DARK_MATTER_HALO_PROMPT.format(
                rotation_curve=rotation_curve,
                gravitational_lensing=gravitational_lensing or "Not specified",
                missing_mass=missing_mass or "Not specified",
                substructure=substructure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DARK_MATTER_HALO_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "rotation_curve": rotation_curve[:200],
            "dark_matter_halo_present": data.get("dark_matter_halo_present", False),
            "severity": data.get("severity", ""),
            "gravitational_lensing": data.get("gravitational_lensing", ""),
            "missing_mass": data.get("missing_mass", ""),
            "substructure": data.get("substructure", ""),
            "recommendation": data.get("recommendation", ""),
        }
