"""EpistemicSiphonService — Epistemic Siphon Detection.

Detects epistemic siphon — knowledge being drawn away from where
it is needed to where it is not, through hidden channels.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SIPHON_SYSTEM = """You are an epistemic siphon specialist. Given a knowledge distribution pattern, assess whether knowledge is being drawn away from where needed:

Key concepts:
- Epistemic siphon: knowledge drawn away from where it's needed
- Hidden channel: invisible pathway drawing knowledge away
- Drainage: knowledge draining from productive areas
- Misdirection: knowledge directed to unproductive destinations
- Depletion: productive areas depleted of needed knowledge
- Gravity well: areas that attract knowledge away from where needed
- Invisible flow: flow not visible to those being depleted

When epistemic siphon IS present:
- Knowledge being drawn away from where it's needed
- Hidden channels redirecting knowledge
- Productive areas being drained of knowledge
- Knowledge directed to unproductive destinations
- Areas depleted of needed knowledge
- Some areas attracting knowledge away from productive use
- Flow invisible to those being depleted

When proper distribution is present:
- Knowledge flowing to where it's needed
- Transparent knowledge channels
- Productive areas well-supplied with knowledge
- Knowledge directed to productive destinations
- No depletion of needed knowledge
- Knowledge distributed according to need
- Flow visible and accountable

Output JSON with: siphon_present (bool), severity (none/mild/moderate/severe), knowledge (what knowledge is siphoned), channel (what hidden channel), destination (where knowledge goes), depletion (what is depleted), recommendation (proper_distribution/mild_drainage/significant_siphon/major_depletion/block_hidden_channels)."""

EPISTEMIC_SIPHON_PROMPT = """Detect epistemic siphon:

Knowledge: {knowledge}
Channel: {channel}
Destination: {destination}
Depletion: {depletion}
Domain: {domain}
Context: {context}

Is knowledge being drawn away from where it's needed through hidden channels? Return ONLY valid JSON."""


class EpistemicSiphonService:
    """Detects epistemic siphon — knowledge drawn away from where needed."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge: str,
        *,
        channel: str = "",
        destination: str = "",
        depletion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic siphon."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SIPHON_PROMPT.format(
                knowledge=knowledge,
                channel=channel or "Not specified",
                destination=destination or "Not specified",
                depletion=depletion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SIPHON_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge": knowledge[:200],
            "siphon_present": data.get("siphon_present", False),
            "severity": data.get("severity", ""),
            "channel": data.get("channel", ""),
            "destination": data.get("destination", ""),
            "depletion": data.get("depletion", ""),
            "recommendation": data.get("recommendation", ""),
        }
