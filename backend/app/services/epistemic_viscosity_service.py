"""EpistemicViscosityService — Epistemic Viscosity Detection.

Detects epistemic viscosity — knowledge too thick or resistant
to flow where it is needed.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_VISCOSITY_SYSTEM = """You are an epistemic viscosity specialist. Given a knowledge flow resistance pattern, assess whether knowledge is too thick to flow:

Key concepts:
- Epistemic viscosity: knowledge too thick to flow where needed
- Flow resistance: resistance to knowledge movement
- Thickness: knowledge encumbered with unnecessary complexity
- Shear stress: force needed to move knowledge
- Non-Newtonian: viscosity changing under pressure
- Clogging: knowledge too thick to pass through channels
- Thinning needed: knowledge needing to be made more accessible

When epistemic viscosity IS present:
- Knowledge too thick or complex to flow where needed
- High resistance to knowledge movement
- Knowledge encumbered with unnecessary complexity
- Excessive force needed to move knowledge
- Viscosity increasing under pressure
- Knowledge clogging communication channels
- Knowledge needing to be made more accessible

When appropriate fluidity is present:
- Knowledge flowing freely where needed
- Low resistance to knowledge movement
- Knowledge at appropriate complexity level
- Minimal force needed for knowledge transfer
- Viscosity appropriate to context
- Knowledge flowing through channels freely
- Knowledge at appropriate accessibility level

Output JSON with: viscosity_present (bool), severity (none/mild/moderate/severe), knowledge (what knowledge is too viscous), resistance (what resistance exists), thickness (what makes it thick), clogging (where it clogs), recommendation (appropriate_fluidity/mild_thickness/significant_viscosity/major_clogging/thin_and_simplify)."""

EPISTEMIC_VISCOSITY_PROMPT = """Detect epistemic viscosity:

Knowledge: {knowledge}
Resistance: {resistance}
Thickness: {thickness}
Clogging: {clogging}
Domain: {domain}
Context: {context}

Is knowledge too thick or resistant to flow where it is needed? Return ONLY valid JSON."""


class EpistemicViscosityService:
    """Detects epistemic viscosity — knowledge too thick to flow."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge: str,
        *,
        resistance: str = "",
        thickness: str = "",
        clogging: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic viscosity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_VISCOSITY_PROMPT.format(
                knowledge=knowledge,
                resistance=resistance or "Not specified",
                thickness=thickness or "Not specified",
                clogging=clogging or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_VISCOSITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge": knowledge[:200],
            "viscosity_present": data.get("viscosity_present", False),
            "severity": data.get("severity", ""),
            "resistance": data.get("resistance", ""),
            "thickness": data.get("thickness", ""),
            "clogging": data.get("clogging", ""),
            "recommendation": data.get("recommendation", ""),
        }
