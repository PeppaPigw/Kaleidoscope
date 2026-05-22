"""EpistemicCompactificationService — Epistemic Compactification Detection.

Detects epistemic compactification — dimensions of thought curled up too
small to observe directly, but whose geometry shapes visible behavior.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMPACTIFICATION_SYSTEM = """You are an epistemic compactification specialist. Given an intellectual space, assess whether dimensions are curled up too small to observe:

Key concepts:
- Epistemic compactification: dimensions curled up too small to observe
- Calabi-Yau manifold: specific shape of curled dimensions
- Moduli: parameters controlling the shape
- Flux: field threading through the curled dimensions
- Landscape: vast number of possible shapes
- Stabilization: mechanism fixing the shape
- Decompactification: curled dimension opening up

When epistemic compactification IS present:
- Dimensions of thought curled up too small to observe
- Specific shape of the hidden dimensions
- Parameters controlling the hidden shape
- Fields threading through hidden dimensions
- Vast number of possible hidden shapes
- Mechanism fixing the hidden shape
- Risk of hidden dimensions opening up

When flat dimensions is present:
- All dimensions extended and observable
- No hidden shape
- No hidden parameters
- No threading fields
- Single geometry
- No stabilization needed
- No decompactification risk

Output JSON with: compactification_present (bool), severity (none/mild/moderate/severe), calabi_yau (what hidden shape), moduli (what shape parameters), flux (what threading field), stabilization (what fixing mechanism), recommendation (flat_dimensions/mild_compactification/significant_compactification/major_hidden_geometry/probe_compact_dimensions)."""

EPISTEMIC_COMPACTIFICATION_PROMPT = """Detect epistemic compactification:

Calabi-Yau: {calabi_yau}
Moduli: {moduli}
Flux: {flux}
Stabilization: {stabilization}
Domain: {domain}
Context: {context}

Are dimensions of thought curled up too small to observe directly, but shaping visible behavior through their geometry? Return ONLY valid JSON."""


class EpistemicCompactificationService:
    """Detects epistemic compactification — dimensions curled up too small to observe."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        calabi_yau: str,
        *,
        moduli: str = "",
        flux: str = "",
        stabilization: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic compactification."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMPACTIFICATION_PROMPT.format(
                calabi_yau=calabi_yau,
                moduli=moduli or "Not specified",
                flux=flux or "Not specified",
                stabilization=stabilization or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMPACTIFICATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "calabi_yau": calabi_yau[:200],
            "compactification_present": data.get("compactification_present", False),
            "severity": data.get("severity", ""),
            "moduli": data.get("moduli", ""),
            "flux": data.get("flux", ""),
            "stabilization": data.get("stabilization", ""),
            "recommendation": data.get("recommendation", ""),
        }
