"""EpistemicCompetitiveKnowingService — Epistemic Competitive Knowing Detection.

Detects epistemic competitive knowing — knowing motivated by competition
rather than genuine inquiry.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMPETITIVE_KNOWING_SYSTEM = """You are an epistemic competitive knowing specialist. Given knowing motivated by competition, assess competitive knowing:

Key concepts:
- Epistemic competitive knowing: knowing motivated by competition not inquiry
- Knowledge race: learning to beat others not to understand
- Intellectual one-upmanship: knowing more to feel superior
- Debate winning: learning to win arguments not find truth
- Citation counting: measuring knowledge by quantity not quality
- First-to-know: racing to know before others
- Intellectual scorekeeping: tracking who knows more

When epistemic competitive knowing IS present:
- Knowing motivated by competition
- Learning to beat others
- Knowing more to feel superior
- Learning to win not find truth
- Measuring by quantity not quality
- Racing to know first
- Tracking who knows more

When no competitive knowing:
- Knowing for understanding
- Learning for growth
- Knowing for its own sake
- Learning to find truth
- Quality over quantity
- Pace of genuine interest
- Collaborative knowing

Output JSON with: competitive_knowing_detected (bool), severity (none/mild/moderate/severe), knowledge_race (what learning to beat others about), intellectual_one_upmanship (what knowing more to feel superior about), debate_winning (what learning to win about), intellectual_scorekeeping (what tracking who knows more about), recommendation (no_competitive_knowing/mild_collaboration_practice/significant_motivation_shift/major_intensive_cooperation_work/emergency_complete_knowledge_warfare)."""

EPISTEMIC_COMPETITIVE_KNOWING_PROMPT = """Detect epistemic competitive knowing:

Knowledge race: {knowledge_race}
Intellectual one-upmanship: {intellectual_one_upmanship}
Debate winning: {debate_winning}
Intellectual scorekeeping: {intellectual_scorekeeping}
Domain: {domain}
Context: {context}

Is there knowing motivated by competition rather than genuine inquiry? Return ONLY valid JSON."""


class EpistemicCompetitiveKnowingService:
    """Detects epistemic competitive knowing — knowing motivated by competition."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge_race: str,
        *,
        intellectual_one_upmanship: str = "",
        debate_winning: str = "",
        intellectual_scorekeeping: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic competitive knowing."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMPETITIVE_KNOWING_PROMPT.format(
                knowledge_race=knowledge_race,
                intellectual_one_upmanship=intellectual_one_upmanship or "Not specified",
                debate_winning=debate_winning or "Not specified",
                intellectual_scorekeeping=intellectual_scorekeeping or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMPETITIVE_KNOWING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge_race": knowledge_race[:200],
            "competitive_knowing_detected": data.get("competitive_knowing_detected", False),
            "severity": data.get("severity", ""),
            "intellectual_one_upmanship": data.get("intellectual_one_upmanship", ""),
            "debate_winning": data.get("debate_winning", ""),
            "intellectual_scorekeeping": data.get("intellectual_scorekeeping", ""),
            "recommendation": data.get("recommendation", ""),
        }
