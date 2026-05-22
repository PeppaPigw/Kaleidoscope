"""HindsightReconstructionService — Hindsight Reconstruction Detection.

Detects hindsight reconstruction — reconstructing the past to make
outcomes seem inevitable, rewriting history so that what happened
appears to have been the only possible outcome.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

HINDSIGHT_RECONSTRUCTION_SYSTEM = """You are a hindsight reconstruction specialist. Given a historical narrative, assess whether the past is being reconstructed to make outcomes seem inevitable:

Key concepts:
- Hindsight reconstruction: rewriting past to make outcome inevitable
- Inevitability narrative: what happened had to happen
- Path erasure: alternative paths deleted from narrative
- Contingency denial: denying role of chance or choice
- Teleological history: history told as if aimed at present
- Outcome-driven narrative: story shaped by known ending
- Deterministic reframing: choices reframed as necessities

When hindsight reconstruction IS present:
- Past reconstructed to make outcome seem inevitable
- Alternative paths erased from narrative
- Contingency and chance denied or minimized
- History told as if aimed at the known outcome
- Decisions reframed as if no alternatives existed
- Complexity of past situation simplified by known outcome
- Warning signs emphasized, uncertainty minimized

When historical analysis is appropriate:
- Contingency and alternatives acknowledged
- Multiple possible paths recognized
- Uncertainty of past actors respected
- Outcome not treated as inevitable
- Causal analysis distinguishes from inevitability
- Hindsight explicitly managed
- Past complexity preserved

Output JSON with: reconstruction_present (bool), severity (none/mild/moderate/severe), narrative (what narrative is told), outcome (what outcome is made inevitable), alternatives_erased (what alternatives are ignored), contingency_denied (what contingency is denied), recommendation (appropriate_historical_analysis/mild_hindsight_coloring/significant_reconstruction/major_inevitability_narrative/preserve_past_contingency)."""

HINDSIGHT_RECONSTRUCTION_PROMPT = """Detect hindsight reconstruction:

Narrative: {narrative}
Outcome described: {outcome}
Alternatives mentioned: {alternatives}
Contingency acknowledged: {contingency}
Domain: {domain}
Context: {context}

Is the past being reconstructed to make the outcome seem inevitable? Return ONLY valid JSON."""


class HindsightReconstructionService:
    """Detects hindsight reconstruction — making outcomes seem inevitable."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        narrative: str,
        *,
        outcome: str = "",
        alternatives: str = "",
        contingency: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect hindsight reconstruction."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=HINDSIGHT_RECONSTRUCTION_PROMPT.format(
                narrative=narrative,
                outcome=outcome or "Not specified",
                alternatives=alternatives or "Not specified",
                contingency=contingency or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=HINDSIGHT_RECONSTRUCTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "narrative": narrative[:200],
            "reconstruction_present": data.get("reconstruction_present", False),
            "severity": data.get("severity", ""),
            "alternatives_erased": data.get("alternatives_erased", ""),
            "contingency_denied": data.get("contingency_denied", ""),
            "recommendation": data.get("recommendation", ""),
        }
