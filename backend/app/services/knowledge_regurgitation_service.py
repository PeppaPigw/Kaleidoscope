"""KnowledgeRegurgitationService — Knowledge Regurgitation Detection.

Detects knowledge regurgitation — repeating knowledge without
digesting or understanding it, parroting without comprehension.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

KNOWLEDGE_REGURGITATION_SYSTEM = """You are a knowledge regurgitation specialist. Given a knowledge demonstration, assess whether knowledge is being repeated without understanding:

Key concepts:
- Knowledge regurgitation: repeating without understanding
- Parroting: repeating words without comprehension
- Surface reproduction: reproducing surface without depth
- Memorization without understanding: memorized but not understood
- Rote repetition: repeating by rote without engagement
- Echo without comprehension: echoing without grasping
- Form without understanding: reproducing form without function

When knowledge regurgitation IS present:
- Knowledge repeated without understanding
- Words parroted without comprehension
- Surface reproduced without depth
- Memorized content without understanding
- Rote repetition without engagement
- Echoing without genuine grasp
- Form reproduced without understanding function

When genuine understanding is present:
- Knowledge expressed with comprehension
- Ideas articulated with understanding
- Depth matching surface expression
- Content understood not just memorized
- Engagement with ideas not just words
- Genuine grasp demonstrated
- Function understood alongside form

Output JSON with: regurgitation_present (bool), severity (none/mild/moderate/severe), demonstration (what is demonstrated), surface_reproduction (what surface is reproduced), understanding_gap (what understanding is missing), indicators (what indicates regurgitation), recommendation (genuine_understanding/mild_surface_level/significant_regurgitation/major_parroting/develop_genuine_understanding)."""

KNOWLEDGE_REGURGITATION_PROMPT = """Detect knowledge regurgitation:

Demonstration: {demonstration}
Surface reproduction: {surface}
Understanding indicators: {understanding}
Depth: {depth}
Domain: {domain}
Context: {context}

Is knowledge being repeated without genuine understanding? Return ONLY valid JSON."""


class KnowledgeRegurgitationService:
    """Detects knowledge regurgitation — repeating without understanding."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        demonstration: str,
        *,
        surface: str = "",
        understanding: str = "",
        depth: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect knowledge regurgitation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=KNOWLEDGE_REGURGITATION_PROMPT.format(
                demonstration=demonstration,
                surface=surface or "Not specified",
                understanding=understanding or "Not specified",
                depth=depth or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=KNOWLEDGE_REGURGITATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "demonstration": demonstration[:200],
            "regurgitation_present": data.get("regurgitation_present", False),
            "severity": data.get("severity", ""),
            "surface_reproduction": data.get("surface_reproduction", ""),
            "understanding_gap": data.get("understanding_gap", ""),
            "indicators": data.get("indicators", ""),
            "recommendation": data.get("recommendation", ""),
        }
