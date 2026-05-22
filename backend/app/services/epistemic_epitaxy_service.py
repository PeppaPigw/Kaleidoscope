"""EpistemicEpitaxyService — Epistemic Epitaxy Detection.

Detects epistemic epitaxy — new ideas growing in alignment with the
crystal structure of the substrate they form on.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EPITAXY_SYSTEM = """You are an epistemic epitaxy specialist. Given an idea growth pattern, assess whether new ideas grow aligned with their substrate:

Key concepts:
- Epistemic epitaxy: new ideas growing aligned with substrate
- Substrate: existing intellectual structure ideas grow on
- Lattice matching: how well new ideas fit existing structure
- Strain: stress from mismatch between new and existing
- Homoepitaxy: same type growing on same type
- Heteroepitaxy: different type growing on different type
- Misfit dislocation: defects from lattice mismatch

When epistemic epitaxy IS present:
- New ideas growing in alignment with existing structure
- Existing intellectual structure determining growth direction
- New ideas fitting or not fitting existing structure
- Stress from mismatch between new and existing ideas
- Same type of ideas growing on same type
- Different ideas forced to align with different substrate
- Defects from mismatch between new and existing

When independent growth is present:
- New ideas growing independently of existing structure
- No existing structure determining direction
- New ideas forming their own structure
- No stress from mismatch
- Ideas growing in their natural form
- No forced alignment with substrate
- No mismatch defects

Output JSON with: epitaxy_present (bool), severity (none/mild/moderate/severe), substrate (what existing structure), lattice_matching (how well new fits), strain (what mismatch stress), misfit (what defects from mismatch), recommendation (independent_growth/mild_alignment/significant_epitaxy/major_substrate_dependence/allow_independent_structure)."""

EPISTEMIC_EPITAXY_PROMPT = """Detect epistemic epitaxy:

Substrate: {substrate}
Lattice matching: {lattice_matching}
Strain: {strain}
Misfit: {misfit}
Domain: {domain}
Context: {context}

Are new ideas growing in alignment with the crystal structure of the substrate they form on? Return ONLY valid JSON."""


class EpistemicEpitaxyService:
    """Detects epistemic epitaxy — new ideas growing aligned with substrate."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        substrate: str,
        *,
        lattice_matching: str = "",
        strain: str = "",
        misfit: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic epitaxy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EPITAXY_PROMPT.format(
                substrate=substrate,
                lattice_matching=lattice_matching or "Not specified",
                strain=strain or "Not specified",
                misfit=misfit or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EPITAXY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "substrate": substrate[:200],
            "epitaxy_present": data.get("epitaxy_present", False),
            "severity": data.get("severity", ""),
            "lattice_matching": data.get("lattice_matching", ""),
            "strain": data.get("strain", ""),
            "misfit": data.get("misfit", ""),
            "recommendation": data.get("recommendation", ""),
        }
