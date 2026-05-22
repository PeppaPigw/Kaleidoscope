"""EpistemicDroughtService — Epistemic Drought Detection.

Detects epistemic drought — prolonged absence of new ideas
or intellectual nourishment.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DROUGHT_SYSTEM = """You are an epistemic drought specialist. Given an intellectual environment, assess whether there is a prolonged absence of new ideas:

Key concepts:
- Epistemic drought: prolonged absence of new ideas
- Intellectual nourishment failure: lack of intellectual nourishment
- Idea scarcity: scarcity of new ideas
- Creative barrenness: barren intellectual landscape
- Innovation starvation: starved of innovation
- Inspiration failure: failure to find inspiration
- Intellectual desert: desert-like intellectual conditions

When epistemic drought IS present:
- Prolonged absence of new ideas
- Lack of intellectual nourishment
- Scarcity of genuinely new ideas
- Barren intellectual landscape
- Starved of innovation and novelty
- Failure to find inspiration
- Desert-like intellectual conditions

When productive consolidation is present:
- Pause in new ideas serving consolidation
- Intellectual nourishment from deepening existing ideas
- Scarcity reflecting selectivity not barrenness
- Landscape being cultivated not barren
- Innovation paused for integration
- Inspiration from deepening not novelty
- Conditions supporting depth over breadth

Output JSON with: drought_present (bool), severity (none/mild/moderate/severe), environment (what environment is affected), scarcity (what is scarce), duration (how long drought has lasted), impact (what impact results), recommendation (productive_consolidation/mild_scarcity/significant_drought/major_intellectual_desert/seek_new_sources)."""

EPISTEMIC_DROUGHT_PROMPT = """Detect epistemic drought:

Environment: {environment}
Scarcity: {scarcity}
Duration: {duration}
Impact: {impact}
Domain: {domain}
Context: {context}

Is there a prolonged absence of new ideas or intellectual nourishment? Return ONLY valid JSON."""


class EpistemicDroughtService:
    """Detects epistemic drought — prolonged absence of new ideas."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        environment: str,
        *,
        scarcity: str = "",
        duration: str = "",
        impact: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic drought."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DROUGHT_PROMPT.format(
                environment=environment,
                scarcity=scarcity or "Not specified",
                duration=duration or "Not specified",
                impact=impact or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DROUGHT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "environment": environment[:200],
            "drought_present": data.get("drought_present", False),
            "severity": data.get("severity", ""),
            "scarcity": data.get("scarcity", ""),
            "duration": data.get("duration", ""),
            "impact": data.get("impact", ""),
            "recommendation": data.get("recommendation", ""),
        }
