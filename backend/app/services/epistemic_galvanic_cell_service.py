"""EpistemicGalvanicCellService — Epistemic Galvanic Cell Detection.

Detects epistemic galvanic cell — two different intellectual metals in
contact generating a voltage that drives corrosion of the less noble one.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GALVANIC_CELL_SYSTEM = """You are an epistemic galvanic cell specialist. Given an intellectual corrosion pattern, assess whether contact between different ideas drives corrosion:

Key concepts:
- Epistemic galvanic cell: different ideas in contact driving corrosion
- Anode: the less noble idea that corrodes
- Cathode: the more noble idea that is protected
- Electrolyte: medium enabling the corrosion current
- Potential difference: voltage driving the corrosion
- Sacrificial anode: deliberately corroding to protect another
- Galvanic series: ranking of ideas by nobility

When epistemic galvanic cell IS present:
- Two different intellectual metals in contact causing corrosion
- Less noble idea being corroded by the contact
- More noble idea being protected at expense of other
- Medium enabling the corrosion current between them
- Voltage difference driving the corrosion process
- One idea deliberately sacrificed to protect another
- Ranking of ideas by their resistance to corrosion

When isolated ideas is present:
- Ideas not in corrosive contact
- No idea being corroded by contact
- No idea protected at another's expense
- No medium enabling corrosion
- No voltage difference between ideas
- No sacrificial relationships
- No nobility ranking relevant

Output JSON with: galvanic_cell_present (bool), severity (none/mild/moderate/severe), anode (what corrodes), cathode (what is protected), electrolyte (what medium enables), potential (what drives corrosion), recommendation (isolated_ideas/mild_galvanic/significant_galvanic_cell/major_corrosion_driving/separate_dissimilar_ideas)."""

EPISTEMIC_GALVANIC_CELL_PROMPT = """Detect epistemic galvanic cell:

Anode: {anode}
Cathode: {cathode}
Electrolyte: {electrolyte}
Potential: {potential}
Domain: {domain}
Context: {context}

Are two different intellectual metals in contact generating a voltage that drives corrosion of the less noble one? Return ONLY valid JSON."""


class EpistemicGalvanicCellService:
    """Detects epistemic galvanic cell — contact driving corrosion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        anode: str,
        *,
        cathode: str = "",
        electrolyte: str = "",
        potential: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic galvanic cell."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GALVANIC_CELL_PROMPT.format(
                anode=anode,
                cathode=cathode or "Not specified",
                electrolyte=electrolyte or "Not specified",
                potential=potential or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GALVANIC_CELL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "anode": anode[:200],
            "galvanic_cell_present": data.get("galvanic_cell_present", False),
            "severity": data.get("severity", ""),
            "cathode": data.get("cathode", ""),
            "electrolyte": data.get("electrolyte", ""),
            "potential": data.get("potential", ""),
            "recommendation": data.get("recommendation", ""),
        }
