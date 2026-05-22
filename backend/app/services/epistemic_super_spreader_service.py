"""EpistemicSuperSpreaderService — Epistemic Super-Spreader Detection.

Detects epistemic super-spreaders — individuals or institutions with
outsized capacity to spread harmful epistemic content.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SUPER_SPREADER_SYSTEM = """You are an epistemic super-spreader specialist. Given an influence pattern, assess whether an entity has outsized capacity to spread harmful epistemic content:

Key concepts:
- Epistemic super-spreader: entity with outsized harmful spread capacity
- Influence amplification: amplifying harmful content beyond normal reach
- Network centrality: central position enabling wide distribution
- Trust exploitation: exploiting trust for harmful content spread
- Platform leverage: using platform position for harmful spread
- Audience capture: captured audience receiving harmful content
- Credibility laundering: using credibility to spread harmful ideas

When epistemic super-spreader IS present:
- Entity with outsized capacity to spread harmful content
- Amplifying harmful content far beyond normal reach
- Central network position enabling wide harmful distribution
- Exploiting established trust for harmful content spread
- Using platform position to spread harmful ideas
- Captured audience receiving harmful epistemic content
- Using credibility to launder harmful ideas

When legitimate influence is present:
- Influence used for beneficial content spread
- Amplification proportionate to content quality
- Network position used for beneficial distribution
- Trust maintained through quality content
- Platform used for beneficial purposes
- Audience served with valuable content
- Credibility earned through accuracy

Output JSON with: super_spreader_present (bool), severity (none/mild/moderate/severe), entity (what entity is super-spreading), capacity (what capacity they have), content (what harmful content spreads), trust_exploitation (how trust is exploited), recommendation (legitimate_influence/mild_amplification/significant_super_spreading/major_harmful_distribution/limit_harmful_amplification)."""

EPISTEMIC_SUPER_SPREADER_PROMPT = """Detect epistemic super-spreader:

Entity: {entity}
Capacity: {capacity}
Content: {content}
Trust exploitation: {trust_exploitation}
Domain: {domain}
Context: {context}

Does this entity have outsized capacity to spread harmful epistemic content? Return ONLY valid JSON."""


class EpistemicSuperSpreaderService:
    """Detects epistemic super-spreaders — entities with outsized harmful spread capacity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        entity: str,
        *,
        capacity: str = "",
        content: str = "",
        trust_exploitation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic super-spreader."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SUPER_SPREADER_PROMPT.format(
                entity=entity,
                capacity=capacity or "Not specified",
                content=content or "Not specified",
                trust_exploitation=trust_exploitation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SUPER_SPREADER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "entity": entity[:200],
            "super_spreader_present": data.get("super_spreader_present", False),
            "severity": data.get("severity", ""),
            "capacity": data.get("capacity", ""),
            "content": data.get("content", ""),
            "trust_exploitation": data.get("trust_exploitation", ""),
            "recommendation": data.get("recommendation", ""),
        }
