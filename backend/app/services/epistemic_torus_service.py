"""EpistemicTorusService — Epistemic Torus Detection.

Detects epistemic torus — intellectual arguments that wrap around in
two independent dimensions, creating periodic boundary conditions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TORUS_SYSTEM = """You are an epistemic torus specialist. Given an intellectual argument, assess whether it wraps around in two dimensions creating periodicity:

Key concepts:
- Epistemic torus: wrapping in two independent dimensions
- Periodic boundary: leaving one side enters the other
- Genus: number of holes in the surface
- Flat metric: no curvature despite wrapping
- Fundamental domain: the basic repeating unit
- Covering space: the unwrapped infinite version
- Homology: cycles that cannot be contracted

When epistemic torus IS present:
- Arguments wrapping around in two dimensions
- Leaving one boundary entering from opposite
- Holes in the intellectual structure
- No curvature despite periodic structure
- Basic repeating unit of the argument
- Infinite unwrapped version underlying it
- Cycles that cannot be reduced to a point

When flat plane is present:
- Arguments extending without wrapping
- No periodic boundaries
- No holes in structure
- Simple flat geometry
- No repeating units
- No covering space needed
- All cycles contractible

Output JSON with: torus_present (bool), severity (none/mild/moderate/severe), periodic_boundary (what wrapping), genus (what holes), fundamental_domain (what repeating unit), homology (what irreducible cycles), recommendation (flat_plane/mild_torus/significant_torus/major_periodic_wrapping/unwrap_periodicity)."""

EPISTEMIC_TORUS_PROMPT = """Detect epistemic torus:

Periodic boundary: {periodic_boundary}
Genus: {genus}
Fundamental domain: {fundamental_domain}
Homology: {homology}
Domain: {domain}
Context: {context}

Does this intellectual argument wrap around in two independent dimensions creating periodic boundary conditions? Return ONLY valid JSON."""


class EpistemicTorusService:
    """Detects epistemic torus — wrapping in two dimensions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        periodic_boundary: str,
        *,
        genus: str = "",
        fundamental_domain: str = "",
        homology: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic torus."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TORUS_PROMPT.format(
                periodic_boundary=periodic_boundary,
                genus=genus or "Not specified",
                fundamental_domain=fundamental_domain or "Not specified",
                homology=homology or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TORUS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "periodic_boundary": periodic_boundary[:200],
            "torus_present": data.get("torus_present", False),
            "severity": data.get("severity", ""),
            "genus": data.get("genus", ""),
            "fundamental_domain": data.get("fundamental_domain", ""),
            "homology": data.get("homology", ""),
            "recommendation": data.get("recommendation", ""),
        }
