"""EpistemicManufacturedConsensusService — Epistemic Manufactured Consensus Detection.

Detects epistemic manufactured consensus — consensus manufactured through
social pressure rather than genuine evidence-based agreement.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MANUFACTURED_CONSENSUS_SYSTEM = """You are an epistemic manufactured consensus specialist. Given consensus manufactured through pressure, assess manufactured consensus:

Key concepts:
- Epistemic manufactured consensus: consensus through pressure not evidence
- Social pressure: pressure to agree rather than genuine agreement
- Bandwagon manufacturing: creating appearance of bandwagon
- Astroturfing: fake grassroots consensus
- Repetition as proof: repeating claim until it seems consensus
- Authority imposition: authority imposing consensus
- Dissent cost: making dissent too costly

When epistemic manufactured consensus IS present:
- Consensus manufactured not genuine
- Social pressure creating agreement
- Bandwagon manufactured
- Grassroots faked
- Repetition creating illusion
- Authority imposing
- Dissent made costly

When no manufactured consensus:
- Consensus genuine
- Agreement evidence-based
- Bandwagon organic
- Grassroots real
- Claims supported by evidence
- Authority earned
- Dissent welcomed

Output JSON with: manufactured_consensus_detected (bool), severity (none/mild/moderate/severe), social_pressure (what pressure applied), bandwagon_manufacturing (what bandwagon manufactured), authority_imposition (what authority imposed), dissent_cost (what cost of dissent), recommendation (no_manufactured_consensus/mild_pressure_awareness/significant_independence_recovery/major_intensive_consensus_deconstruction/emergency_complete_manufactured_consensus)."""

EPISTEMIC_MANUFACTURED_CONSENSUS_PROMPT = """Detect epistemic manufactured consensus:

Social pressure: {social_pressure}
Bandwagon manufacturing: {bandwagon_manufacturing}
Authority imposition: {authority_imposition}
Dissent cost: {dissent_cost}
Domain: {domain}
Context: {context}

Is consensus being manufactured through pressure rather than evidence? Return ONLY valid JSON."""


class EpistemicManufacturedConsensusService:
    """Detects epistemic manufactured consensus — pressure not evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        social_pressure: str,
        *,
        bandwagon_manufacturing: str = "",
        authority_imposition: str = "",
        dissent_cost: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic manufactured consensus."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MANUFACTURED_CONSENSUS_PROMPT.format(
                social_pressure=social_pressure,
                bandwagon_manufacturing=bandwagon_manufacturing or "Not specified",
                authority_imposition=authority_imposition or "Not specified",
                dissent_cost=dissent_cost or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MANUFACTURED_CONSENSUS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "social_pressure": social_pressure[:200],
            "manufactured_consensus_detected": data.get("manufactured_consensus_detected", False),
            "severity": data.get("severity", ""),
            "bandwagon_manufacturing": data.get("bandwagon_manufacturing", ""),
            "authority_imposition": data.get("authority_imposition", ""),
            "dissent_cost": data.get("dissent_cost", ""),
            "recommendation": data.get("recommendation", ""),
        }
