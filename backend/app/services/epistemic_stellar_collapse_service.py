"""EpistemicStellarCollapseService — Epistemic Stellar Collapse Detection.

Detects epistemic stellar collapse — knowledge systems collapsing
under their own weight when they grow too massive.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_STELLAR_COLLAPSE_SYSTEM = """You are an epistemic stellar collapse specialist. Given a knowledge system, assess whether it is collapsing under its own weight:

Key concepts:
- Epistemic stellar collapse: knowledge system collapsing under own weight
- Critical mass: system growing too massive to sustain itself
- Internal pressure failure: internal support mechanisms failing
- Gravitational collapse: weight of accumulated knowledge crushing structure
- Neutron star: collapsed into ultra-dense but inaccessible form
- Black hole: collapsed beyond point of information retrieval
- Chandrasekhar limit: maximum sustainable complexity

When stellar collapse IS present:
- Knowledge system collapsing under its own accumulated weight
- System grown too massive to sustain itself
- Internal support mechanisms failing under load
- Weight of accumulated knowledge crushing structure
- Knowledge collapsed into dense but inaccessible form
- Information becoming irretrievable after collapse
- Maximum sustainable complexity exceeded

When sustainable system is present:
- Knowledge system maintaining structure under its weight
- System at sustainable size
- Internal support mechanisms functioning
- Structure supporting accumulated knowledge
- Knowledge accessible and organized
- Information retrievable
- Complexity within sustainable limits

Output JSON with: stellar_collapse (bool), severity (none/mild/moderate/severe), system (what system is collapsing), mass (what accumulated weight), pressure_failure (what support fails), accessibility_loss (what becomes inaccessible), recommendation (sustainable_system/mild_strain/significant_collapse/major_black_hole/reduce_mass_or_add_support)."""

EPISTEMIC_STELLAR_COLLAPSE_PROMPT = """Detect epistemic stellar collapse:

System: {system}
Mass: {mass}
Pressure failure: {pressure_failure}
Accessibility loss: {accessibility_loss}
Domain: {domain}
Context: {context}

Is the knowledge system collapsing under its own accumulated weight? Return ONLY valid JSON."""


class EpistemicStellarCollapseService:
    """Detects epistemic stellar collapse — systems collapsing under own weight."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        system: str,
        *,
        mass: str = "",
        pressure_failure: str = "",
        accessibility_loss: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic stellar collapse."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_STELLAR_COLLAPSE_PROMPT.format(
                system=system,
                mass=mass or "Not specified",
                pressure_failure=pressure_failure or "Not specified",
                accessibility_loss=accessibility_loss or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_STELLAR_COLLAPSE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "system": system[:200],
            "stellar_collapse": data.get("stellar_collapse", False),
            "severity": data.get("severity", ""),
            "mass": data.get("mass", ""),
            "pressure_failure": data.get("pressure_failure", ""),
            "accessibility_loss": data.get("accessibility_loss", ""),
            "recommendation": data.get("recommendation", ""),
        }
