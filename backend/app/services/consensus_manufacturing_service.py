"""ConsensusManufacturingService — Consensus Manufacturing Detection.

Detects manufactured consensus — when apparent agreement is
engineered rather than genuine. This includes suppressing
dissent, selective polling, framing questions to get desired
answers, and creating the appearance of agreement where none exists.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CONSENSUS_MANUFACTURING_SYSTEM = """You are a consensus manufacturing specialist. Given an apparent agreement, assess whether it is genuine or manufactured:

Key concepts:
- Manufactured consent: engineering appearance of agreement
- Selective polling: asking only those likely to agree
- Leading questions: framing to get desired answers
- Preference falsification: people hiding true preferences
- Spiral of silence: dissenters staying quiet
- Astroturfing: fake grassroots support
- Delphi manipulation: steering expert panels toward predetermined conclusions

When consensus IS manufactured:
- Dissenting voices excluded from the process
- Questions framed to produce desired answers
- Only agreeing parties consulted
- Disagreement suppressed or not recorded
- Appearance of unanimity despite known disagreement
- Process designed to produce predetermined outcome
- Selective presentation of who agrees

When consensus is genuine:
- All relevant parties consulted including likely dissenters
- Questions neutrally framed
- Disagreement recorded and addressed
- Process designed to surface true preferences
- Anonymous mechanisms used where social pressure exists
- Minority views documented even when overruled
- Agreement emerged from deliberation, not engineering

Output JSON with: manufactured (bool), severity (none/mild/moderate/severe), apparent_consensus (what agreement is claimed), manufacturing_method (how it was engineered), excluded_voices (who was left out), genuine_disagreement (what dissent exists), recommendation (genuine_consensus/mild_engineering/significant_manufacturing/major_false_consensus/redesign_process)."""

CONSENSUS_MANUFACTURING_PROMPT = """Detect consensus manufacturing:

Claimed consensus: {consensus}
Process used: {process}
Participants: {participants}
Dissent handling: {dissent}
Domain: {domain}
Context: {context}

Is this consensus genuine or manufactured? Return ONLY valid JSON."""


class ConsensusManufacturingService:
    """Detects manufactured consensus — engineered rather than genuine agreement."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        consensus: str,
        *,
        process: str = "",
        participants: str = "",
        dissent: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect consensus manufacturing."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CONSENSUS_MANUFACTURING_PROMPT.format(
                consensus=consensus,
                process=process or "Not specified",
                participants=participants or "Not specified",
                dissent=dissent or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CONSENSUS_MANUFACTURING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "consensus": consensus[:200],
            "manufactured": data.get("manufactured", False),
            "severity": data.get("severity", ""),
            "manufacturing_method": data.get("manufacturing_method", ""),
            "excluded_voices": data.get("excluded_voices", ""),
            "genuine_disagreement": data.get("genuine_disagreement", ""),
            "recommendation": data.get("recommendation", ""),
        }
