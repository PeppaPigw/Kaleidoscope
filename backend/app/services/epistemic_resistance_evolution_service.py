"""EpistemicResistanceEvolutionService — Epistemic Resistance Evolution Detection.

Detects epistemic resistance evolution — harmful ideas evolving
resistance to criticism and correction.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_RESISTANCE_EVOLUTION_SYSTEM = """You are an epistemic resistance evolution specialist. Given a belief pattern, assess whether harmful ideas have evolved resistance to criticism:

Key concepts:
- Resistance evolution: harmful ideas evolving resistance to criticism
- Criticism immunity: developing immunity to specific criticisms
- Adaptive defense: defenses adapting to overcome challenges
- Mutation under pressure: idea mutating to survive criticism
- Selection pressure response: responding to selection pressure
- Evolved unfalsifiability: evolving to become unfalsifiable
- Defensive adaptation: adapting defenses to new attacks

When resistance evolution IS present:
- Harmful ideas evolving resistance to criticism
- Developing immunity to specific criticisms over time
- Defenses adapting to overcome new challenges
- Idea mutating to survive criticism while maintaining core harm
- Responding to selection pressure by becoming harder to challenge
- Evolving toward unfalsifiability
- Adapting defenses specifically to counter new attacks

When genuine refinement is present:
- Ideas improving through legitimate criticism
- Responding to criticism by becoming more accurate
- Refinement making ideas more testable
- Evolution toward greater precision and falsifiability
- Improvement through genuine engagement with challenges
- Becoming more nuanced through criticism
- Legitimate intellectual development

Output JSON with: resistance_present (bool), severity (none/mild/moderate/severe), idea (what idea evolves resistance), criticism (what criticism it resists), adaptation (how it adapts), unfalsifiability (degree of unfalsifiability), recommendation (genuine_refinement/mild_defensiveness/significant_resistance/major_evolved_immunity/restore_falsifiability)."""

EPISTEMIC_RESISTANCE_EVOLUTION_PROMPT = """Detect epistemic resistance evolution:

Idea: {idea}
Criticism: {criticism}
Adaptation: {adaptation}
Unfalsifiability: {unfalsifiability}
Domain: {domain}
Context: {context}

Has this harmful idea evolved resistance to criticism and correction? Return ONLY valid JSON."""


class EpistemicResistanceEvolutionService:
    """Detects epistemic resistance evolution — ideas evolving resistance to criticism."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        idea: str,
        *,
        criticism: str = "",
        adaptation: str = "",
        unfalsifiability: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic resistance evolution."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_RESISTANCE_EVOLUTION_PROMPT.format(
                idea=idea,
                criticism=criticism or "Not specified",
                adaptation=adaptation or "Not specified",
                unfalsifiability=unfalsifiability or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_RESISTANCE_EVOLUTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "idea": idea[:200],
            "resistance_present": data.get("resistance_present", False),
            "severity": data.get("severity", ""),
            "criticism": data.get("criticism", ""),
            "adaptation": data.get("adaptation", ""),
            "unfalsifiability": data.get("unfalsifiability", ""),
            "recommendation": data.get("recommendation", ""),
        }
