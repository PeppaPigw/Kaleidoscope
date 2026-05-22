"""EpistemicDecompositionService — Epistemic Decomposition Detection.

Detects epistemic decomposition — knowledge breaking down through
intellectual decomposers, recycling components for new growth.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DECOMPOSITION_SYSTEM = """You are an epistemic decomposition specialist. Given a knowledge recycling pattern, assess whether decomposers are breaking down knowledge for reuse:

Key concepts:
- Epistemic decomposition: knowledge breaking down for recycling
- Decomposer: intellectual agents breaking down old knowledge
- Nutrient cycling: components being recycled for new growth
- Detritus: dead knowledge awaiting decomposition
- Humus: rich intellectual substrate from decomposed knowledge
- Decay rate: how fast knowledge decomposes
- Succession: new ideas growing on decomposed substrate

When epistemic decomposition IS present:
- Old knowledge being broken down by intellectual decomposers
- Components being recycled for new intellectual growth
- Dead knowledge accumulating as detritus
- Rich intellectual substrate forming from decomposed knowledge
- Knowledge decaying at observable rate
- New ideas growing on decomposed substrate
- Active recycling of intellectual components

When preserved knowledge is present:
- Knowledge maintained without decomposition
- No recycling of components needed
- No dead knowledge accumulating
- No substrate forming from decay
- Knowledge remaining in original form
- No new growth from decomposed material
- Knowledge preserved as-is

Output JSON with: decomposition_present (bool), severity (none/mild/moderate/severe), knowledge (what knowledge decomposes), decomposers (what breaks it down), nutrients (what components are recycled), succession (what new growth results), recommendation (preserved_knowledge/mild_decay/significant_decomposition/major_breakdown/guide_recycling_for_new_growth)."""

EPISTEMIC_DECOMPOSITION_PROMPT = """Detect epistemic decomposition:

Knowledge: {knowledge}
Decomposers: {decomposers}
Nutrients: {nutrients}
Succession: {succession}
Domain: {domain}
Context: {context}

Is knowledge being broken down by intellectual decomposers for recycling into new growth? Return ONLY valid JSON."""


class EpistemicDecompositionService:
    """Detects epistemic decomposition — knowledge recycling through breakdown."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge: str,
        *,
        decomposers: str = "",
        nutrients: str = "",
        succession: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic decomposition."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DECOMPOSITION_PROMPT.format(
                knowledge=knowledge,
                decomposers=decomposers or "Not specified",
                nutrients=nutrients or "Not specified",
                succession=succession or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DECOMPOSITION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge": knowledge[:200],
            "decomposition_present": data.get("decomposition_present", False),
            "severity": data.get("severity", ""),
            "decomposers": data.get("decomposers", ""),
            "nutrients": data.get("nutrients", ""),
            "succession": data.get("succession", ""),
            "recommendation": data.get("recommendation", ""),
        }
