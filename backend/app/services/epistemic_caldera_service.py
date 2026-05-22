"""EpistemicCalderaService — Epistemic Caldera Detection.

Detects epistemic calderas — massive intellectual collapses that leave
behind vast empty craters where towering structures once stood.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CALDERA_SYSTEM = """You are an epistemic caldera specialist. Given an intellectual collapse, assess whether massive collapse has left vast empty craters:

Key concepts:
- Epistemic caldera: massive collapse leaving empty crater
- Collapse: towering intellectual structure falling inward
- Crater: vast empty space where structure once stood
- Magma chamber: underlying support that was depleted
- Resurgence: new growth eventually filling the caldera
- Scale: caldera proportional to size of collapsed structure
- Warning signs: precursors to caldera-forming collapse

When epistemic caldera IS present:
- Massive intellectual collapse leaving vast empty space
- Towering intellectual structures falling inward
- Vast empty space where impressive structures once stood
- Underlying support depleted causing collapse
- Potential for new growth eventually filling the void
- Scale of collapse proportional to former structure
- Warning signs that preceded the collapse

When standing structures are present:
- Intellectual structures remaining intact
- No inward collapse occurring
- Structures occupying their space fully
- Underlying support remaining strong
- No void needing to be filled
- Structures proportional and stable
- No warning signs of collapse

Output JSON with: caldera_present (bool), severity (none/mild/moderate/severe), structure (what structure collapsed), crater (what empty space remains), depletion (what support was depleted), resurgence (what new growth is possible), recommendation (standing_structures/mild_subsidence/significant_caldera/major_collapse/support_resurgence)."""

EPISTEMIC_CALDERA_PROMPT = """Detect epistemic caldera:

Structure: {structure}
Crater: {crater}
Depletion: {depletion}
Resurgence: {resurgence}
Domain: {domain}
Context: {context}

Has massive intellectual collapse left vast empty craters where towering structures once stood? Return ONLY valid JSON."""


class EpistemicCalderaService:
    """Detects epistemic calderas — massive collapses leaving empty craters."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        structure: str,
        *,
        crater: str = "",
        depletion: str = "",
        resurgence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic caldera."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CALDERA_PROMPT.format(
                structure=structure,
                crater=crater or "Not specified",
                depletion=depletion or "Not specified",
                resurgence=resurgence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CALDERA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "structure": structure[:200],
            "caldera_present": data.get("caldera_present", False),
            "severity": data.get("severity", ""),
            "crater": data.get("crater", ""),
            "depletion": data.get("depletion", ""),
            "resurgence": data.get("resurgence", ""),
            "recommendation": data.get("recommendation", ""),
        }
