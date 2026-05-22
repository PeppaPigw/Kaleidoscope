"""EpistemicParasiteService — Epistemic Parasite Detection.

Detects epistemic parasites — ideas that exploit host belief systems
for their own propagation rather than benefiting the host.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PARASITE_SYSTEM = """You are an epistemic parasite specialist. Given a belief system, assess whether ideas exploit the host for their own propagation:

Key concepts:
- Epistemic parasite: idea exploiting host belief system for propagation
- Host exploitation: idea benefits itself at host's expense
- Propagation drive: idea optimized for spreading not truth
- Cognitive hijacking: hijacking cognitive resources for propagation
- Memetic parasitism: parasitic relationship between idea and host
- Resource extraction: extracting cognitive resources without benefit
- Fitness mimicry: mimicking useful ideas while being parasitic

When epistemic parasite IS present:
- Ideas exploiting host belief system for propagation
- Idea benefits itself at host's cognitive expense
- Idea optimized for spreading rather than truth
- Hijacking cognitive resources for propagation
- Parasitic relationship between idea and host mind
- Extracting cognitive resources without providing benefit
- Mimicking useful ideas while being parasitic

When genuine useful ideas are present:
- Ideas that benefit the host mind
- Mutual benefit between idea and host
- Ideas optimized for truth and utility
- Cognitive resources used productively
- Symbiotic relationship between idea and host
- Ideas providing genuine cognitive benefit
- Genuinely useful ideas spreading on merit

Output JSON with: parasite_present (bool), severity (none/mild/moderate/severe), idea (what idea is parasitic), exploitation (how it exploits host), propagation (how it propagates), host_cost (cost to host), recommendation (genuine_utility/mild_exploitation/significant_parasitism/major_cognitive_hijacking/reject_parasitic_idea)."""

EPISTEMIC_PARASITE_PROMPT = """Detect epistemic parasite:

Idea: {idea}
Exploitation: {exploitation}
Propagation: {propagation}
Host cost: {host_cost}
Domain: {domain}
Context: {context}

Does this idea exploit the host belief system for its own propagation? Return ONLY valid JSON."""


class EpistemicParasiteService:
    """Detects epistemic parasites — ideas exploiting hosts for propagation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        idea: str,
        *,
        exploitation: str = "",
        propagation: str = "",
        host_cost: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic parasite."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PARASITE_PROMPT.format(
                idea=idea,
                exploitation=exploitation or "Not specified",
                propagation=propagation or "Not specified",
                host_cost=host_cost or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PARASITE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "idea": idea[:200],
            "parasite_present": data.get("parasite_present", False),
            "severity": data.get("severity", ""),
            "exploitation": data.get("exploitation", ""),
            "propagation": data.get("propagation", ""),
            "host_cost": data.get("host_cost", ""),
            "recommendation": data.get("recommendation", ""),
        }
