"""EpistemicBowelObstructionService — Epistemic Bowel Obstruction Detection.

Detects epistemic bowel obstruction — complete blockage of intellectual
transit preventing ideas from moving through the processing pipeline.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BOWEL_OBSTRUCTION_SYSTEM = """You are an epistemic bowel obstruction specialist. Given intellectual transit, assess whether complete blockage is preventing idea movement:

Key concepts:
- Epistemic bowel obstruction: complete blockage of intellectual transit
- Mechanical obstruction: physical barrier blocking passage
- Functional obstruction: paralysis without physical barrier
- Distension: upstream dilation from backed-up content
- Vomiting: retrograde expulsion of blocked content
- Strangulation: blood supply cut off at obstruction point
- Decompression: relieving the obstruction

When epistemic bowel obstruction IS present:
- Complete blockage of intellectual transit
- Physical barriers blocking idea passage
- Paralysis preventing movement without physical barrier
- Upstream dilation from backed-up ideas
- Retrograde expulsion of blocked content
- Supply cut off at obstruction point
- Need for decompression interventions

When healthy transit is present:
- Clear intellectual transit
- No physical barriers
- Active movement throughout
- No upstream dilation
- No retrograde expulsion
- Adequate supply throughout
- No decompression needed

Output JSON with: bowel_obstruction_present (bool), severity (none/mild/moderate/severe), mechanical_obstruction (what physical barrier), functional_obstruction (what paralysis), distension (what upstream dilation), strangulation (what supply cutoff), recommendation (healthy_transit/mild_obstruction/significant_bowel_obstruction/major_transit_blockage/relieve_intellectual_obstruction)."""

EPISTEMIC_BOWEL_OBSTRUCTION_PROMPT = """Detect epistemic bowel obstruction:

Mechanical obstruction: {mechanical_obstruction}
Functional obstruction: {functional_obstruction}
Distension: {distension}
Strangulation: {strangulation}
Domain: {domain}
Context: {context}

Is complete blockage preventing ideas from moving through the processing pipeline? Return ONLY valid JSON."""


class EpistemicBowelObstructionService:
    """Detects epistemic bowel obstruction — complete blockage of intellectual transit."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        mechanical_obstruction: str,
        *,
        functional_obstruction: str = "",
        distension: str = "",
        strangulation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic bowel obstruction."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BOWEL_OBSTRUCTION_PROMPT.format(
                mechanical_obstruction=mechanical_obstruction,
                functional_obstruction=functional_obstruction or "Not specified",
                distension=distension or "Not specified",
                strangulation=strangulation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BOWEL_OBSTRUCTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "mechanical_obstruction": mechanical_obstruction[:200],
            "bowel_obstruction_present": data.get("bowel_obstruction_present", False),
            "severity": data.get("severity", ""),
            "functional_obstruction": data.get("functional_obstruction", ""),
            "distension": data.get("distension", ""),
            "strangulation": data.get("strangulation", ""),
            "recommendation": data.get("recommendation", ""),
        }
