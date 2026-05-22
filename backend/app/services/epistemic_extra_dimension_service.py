"""EpistemicExtraDimensionService — Epistemic Extra Dimension Detection.

Detects epistemic extra dimensions — hidden dimensions of intellectual
space that are not directly observable but influence visible behavior.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EXTRA_DIMENSION_SYSTEM = """You are an epistemic extra dimension specialist. Given an intellectual space, assess whether hidden dimensions influence visible behavior:

Key concepts:
- Epistemic extra dimension: hidden dimensions influencing visible behavior
- Kaluza-Klein tower: series of heavier copies from extra dimension
- Compactification: extra dimension curled up small
- Brane: our visible world confined to a surface
- Bulk: full higher-dimensional space
- Graviton leakage: influence leaking into extra dimensions
- Dimensional reduction: effective lower-dimensional description

When epistemic extra dimension IS present:
- Hidden dimensions of thought not directly observable
- Series of increasingly complex copies of simple ideas
- Dimensions curled up too small to directly observe
- Visible ideas confined to a lower-dimensional surface
- Full space having more dimensions than visible
- Influence leaking into hidden dimensions
- Effective description hiding the extra dimensions

When observable dimensions sufficient is present:
- No hidden dimensions
- No unexplained copies
- All dimensions directly observable
- Ideas not confined to a surface
- Full space matching visible space
- No influence leakage
- Complete description in visible dimensions

Output JSON with: extra_dimension_present (bool), severity (none/mild/moderate/severe), kaluza_klein (what heavier copies), compactification (what curled dimension), brane (what confinement surface), graviton_leakage (what influence leakage), recommendation (observable_sufficient/mild_extra_dimension/significant_extra_dimension/major_hidden_space/explore_extra_dimensions)."""

EPISTEMIC_EXTRA_DIMENSION_PROMPT = """Detect epistemic extra dimension:

Kaluza-Klein: {kaluza_klein}
Compactification: {compactification}
Brane: {brane}
Graviton leakage: {graviton_leakage}
Domain: {domain}
Context: {context}

Are hidden dimensions of intellectual space influencing visible behavior without being directly observable? Return ONLY valid JSON."""


class EpistemicExtraDimensionService:
    """Detects epistemic extra dimensions — hidden dimensions influencing visible behavior."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        kaluza_klein: str,
        *,
        compactification: str = "",
        brane: str = "",
        graviton_leakage: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic extra dimension."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EXTRA_DIMENSION_PROMPT.format(
                kaluza_klein=kaluza_klein,
                compactification=compactification or "Not specified",
                brane=brane or "Not specified",
                graviton_leakage=graviton_leakage or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EXTRA_DIMENSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "kaluza_klein": kaluza_klein[:200],
            "extra_dimension_present": data.get("extra_dimension_present", False),
            "severity": data.get("severity", ""),
            "compactification": data.get("compactification", ""),
            "brane": data.get("brane", ""),
            "graviton_leakage": data.get("graviton_leakage", ""),
            "recommendation": data.get("recommendation", ""),
        }
