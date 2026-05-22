"""EpistemicDampeningService — Epistemic Dampening Detection.

Detects epistemic dampening — knowledge being suppressed or
attenuated, losing strength before reaching its audience.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DAMPENING_SYSTEM = """You are an epistemic dampening specialist. Given a knowledge suppression pattern, assess whether knowledge is being attenuated:

Key concepts:
- Epistemic dampening: knowledge losing strength before reaching audience
- Signal attenuation: knowledge signal weakened during transmission
- Suppression mechanism: active mechanisms reducing knowledge strength
- Absorption: knowledge absorbed by intermediaries
- Friction loss: knowledge losing energy through friction
- Selective dampening: some knowledge dampened more than others
- Critical dampening: knowledge reduced below threshold of notice

When epistemic dampening IS present:
- Knowledge losing strength before reaching audience
- Signal weakened during transmission
- Active mechanisms reducing knowledge strength
- Knowledge absorbed by intermediaries
- Knowledge losing energy through institutional friction
- Some knowledge selectively dampened more
- Knowledge reduced below threshold of notice

When undampened transmission is present:
- Knowledge maintaining strength to audience
- Signal preserved during transmission
- No mechanisms reducing knowledge strength
- Knowledge passing through intermediaries intact
- No friction loss during transmission
- All knowledge transmitted equally
- Knowledge above threshold of notice

Output JSON with: dampening_present (bool), severity (none/mild/moderate/severe), knowledge (what knowledge is dampened), mechanism (what dampens it), attenuation (how much attenuation), selectivity (what is selectively dampened), recommendation (undampened_transmission/mild_attenuation/significant_dampening/major_suppression/remove_dampening_mechanisms)."""

EPISTEMIC_DAMPENING_PROMPT = """Detect epistemic dampening:

Knowledge: {knowledge}
Mechanism: {mechanism}
Attenuation: {attenuation}
Selectivity: {selectivity}
Domain: {domain}
Context: {context}

Is knowledge being suppressed or attenuated before reaching its audience? Return ONLY valid JSON."""


class EpistemicDampeningService:
    """Detects epistemic dampening — knowledge suppressed or attenuated."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge: str,
        *,
        mechanism: str = "",
        attenuation: str = "",
        selectivity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic dampening."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DAMPENING_PROMPT.format(
                knowledge=knowledge,
                mechanism=mechanism or "Not specified",
                attenuation=attenuation or "Not specified",
                selectivity=selectivity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DAMPENING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge": knowledge[:200],
            "dampening_present": data.get("dampening_present", False),
            "severity": data.get("severity", ""),
            "mechanism": data.get("mechanism", ""),
            "attenuation": data.get("attenuation", ""),
            "selectivity": data.get("selectivity", ""),
            "recommendation": data.get("recommendation", ""),
        }
