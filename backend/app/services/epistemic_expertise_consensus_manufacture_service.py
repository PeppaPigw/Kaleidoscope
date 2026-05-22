"""EpistemicExpertiseConsensusManufactureService — Epistemic Expertise Consensus Manufacture Detection.

Detects epistemic expertise consensus manufacture — manufacturing the appearance
of expert agreement where genuine consensus does not exist.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EXPERTISE_CONSENSUS_MANUFACTURE_SYSTEM = """You are an epistemic expertise consensus manufacture specialist. Given manufactured consensus, assess artificial agreement:

Key concepts:
- Epistemic consensus manufacture: creating false appearance of agreement
- Selective citation: citing only agreeing experts while ignoring dissenters
- Panel stacking: selecting panelists known to agree
- Consensus by exclusion: defining consensus by excluding disagreeing experts
- Authority amplification: amplifying few voices to seem like many
- Dissent suppression: actively suppressing or marginalizing disagreement
- Manufactured unanimity: creating appearance of no disagreement

When epistemic consensus manufacture IS present:
- False agreement manufactured
- Only agreeing experts cited
- Panels stacked
- Dissenters excluded from consensus
- Few voices amplified
- Dissent suppressed
- Unanimity manufactured

When no consensus manufacture:
- Agreement genuine
- Full range of expert opinion cited
- Panels representative
- Consensus includes dissenters
- Proportionate representation
- Dissent acknowledged
- Disagreement visible

Output JSON with: consensus_manufacture_detected (bool), severity (none/mild/moderate/severe), selective_citation (what selective citing), panel_stacking (what panels stacked), dissent_suppression (what dissent suppressed), manufactured_unanimity (what unanimity manufactured), recommendation (no_consensus_manufacture/mild_dissent_inclusion/significant_full_spectrum_representation/major_intensive_consensus_audit/emergency_complete_consensus_manufacture)."""

EPISTEMIC_EXPERTISE_CONSENSUS_MANUFACTURE_PROMPT = """Detect epistemic expertise consensus manufacture:

Selective citation: {selective_citation}
Panel stacking: {panel_stacking}
Dissent suppression: {dissent_suppression}
Manufactured unanimity: {manufactured_unanimity}
Domain: {domain}
Context: {context}

Is expert consensus being manufactured rather than genuine? Return ONLY valid JSON."""


class EpistemicExpertiseConsensusManufactureService:
    """Detects epistemic expertise consensus manufacture — artificial agreement."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        selective_citation: str,
        *,
        panel_stacking: str = "",
        dissent_suppression: str = "",
        manufactured_unanimity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic expertise consensus manufacture."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EXPERTISE_CONSENSUS_MANUFACTURE_PROMPT.format(
                selective_citation=selective_citation,
                panel_stacking=panel_stacking or "Not specified",
                dissent_suppression=dissent_suppression or "Not specified",
                manufactured_unanimity=manufactured_unanimity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EXPERTISE_CONSENSUS_MANUFACTURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "selective_citation": selective_citation[:200],
            "consensus_manufacture_detected": data.get("consensus_manufacture_detected", False),
            "severity": data.get("severity", ""),
            "panel_stacking": data.get("panel_stacking", ""),
            "dissent_suppression": data.get("dissent_suppression", ""),
            "manufactured_unanimity": data.get("manufactured_unanimity", ""),
            "recommendation": data.get("recommendation", ""),
        }
