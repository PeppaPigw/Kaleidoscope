"""AnthropicBiasService — Anthropic Bias Detection.

Detects anthropic bias — projecting human-like qualities, intentions,
or experiences onto non-human entities such as AI systems, animals,
organizations, or natural processes.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ANTHROPIC_BIAS_SYSTEM = """You are an anthropic bias specialist. Given a description or claim, assess whether human qualities are being inappropriately projected onto non-human entities:

Key concepts:
- Anthropic bias: projecting human qualities onto non-human entities
- Anthropomorphism: attributing human traits to non-humans
- Intentional stance overextension: seeing intentions where none exist
- Agency attribution: attributing agency to non-agents
- Emotional projection: projecting emotions onto entities that don't have them
- Teleological attribution: seeing purpose in purposeless processes
- Theory of mind overextension: assuming mental states in non-minds

When anthropic bias IS present:
- Human emotions attributed to non-sentient entities
- Intentions projected onto systems without goals
- Human-like reasoning assumed in non-reasoning systems
- Organizational behavior described as if organization has feelings
- Natural processes described as having purposes
- AI systems described as wanting, feeling, or believing
- Complex systems treated as having unified consciousness

When human-like description is appropriate:
- Entity genuinely has relevant cognitive capacities
- Metaphor explicitly acknowledged as metaphor
- Functional analogy used with clear limits
- Intentional stance used as useful predictive tool
- Anthropomorphism serves communication without misleading
- Degree of sentience/agency genuinely uncertain
- Description hedged appropriately

Output JSON with: bias_present (bool), severity (none/mild/moderate/severe), description (what is described), entity (what entity is anthropomorphized), projected_qualities (what human qualities are projected), actual_nature (what the entity actually is), recommendation (appropriate_description/mild_anthropomorphism/significant_projection/major_anthropic_bias/describe_actual_nature)."""

ANTHROPIC_BIAS_PROMPT = """Detect anthropic bias:

Description: {description}
Entity: {entity}
Qualities attributed: {qualities}
Actual nature: {nature}
Domain: {domain}
Context: {context}

Are human qualities being inappropriately projected onto a non-human entity? Return ONLY valid JSON."""


class AnthropicBiasService:
    """Detects anthropic bias — projecting human qualities onto non-human entities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        description: str,
        *,
        entity: str = "",
        qualities: str = "",
        nature: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect anthropic bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ANTHROPIC_BIAS_PROMPT.format(
                description=description,
                entity=entity or "Not specified",
                qualities=qualities or "Not specified",
                nature=nature or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ANTHROPIC_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "description": description[:200],
            "bias_present": data.get("bias_present", False),
            "severity": data.get("severity", ""),
            "entity": data.get("entity", ""),
            "projected_qualities": data.get("projected_qualities", ""),
            "actual_nature": data.get("actual_nature", ""),
            "recommendation": data.get("recommendation", ""),
        }
