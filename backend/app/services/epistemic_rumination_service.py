"""EpistemicRuminationService — Epistemic Rumination Detection.

Detects epistemic rumination — repetitive, passive focus on intellectual
distress and its causes without moving toward solutions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_RUMINATION_SYSTEM = """You are an epistemic rumination specialist. Given repetitive intellectual distress focus, assess rumination patterns:

Key concepts:
- Epistemic rumination: repetitive passive focus on intellectual distress
- Brooding: dwelling on intellectual failures without action
- Reflection vs rumination: productive analysis vs stuck cycling
- Thought loops: same intellectual concerns repeating endlessly
- Paralysis: rumination preventing forward progress
- Amplification: rumination making problems seem worse
- Metacognitive trap: thinking about thinking about thinking

When epistemic rumination IS present:
- Repetitive focus on intellectual distress
- Dwelling on failures without action
- Stuck cycling not productive analysis
- Same concerns repeating endlessly
- Preventing forward progress
- Making problems seem worse
- Trapped in meta-thinking

When no rumination:
- Productive reflection
- Moving past failures
- Constructive analysis
- New thoughts emerging
- Forward progress maintained
- Proportionate problem assessment
- Grounded thinking

Output JSON with: rumination_detected (bool), severity (none/mild/moderate/severe), loop_content (what repeating thoughts), duration_pattern (what time stuck), paralysis_level (what action prevention), amplification_effect (what distortion), recommendation (no_rumination/mild_thought_stopping/significant_metacognitive_therapy/major_intensive_intervention/emergency_complete_paralysis)."""

EPISTEMIC_RUMINATION_PROMPT = """Detect epistemic rumination:

Loop content: {loop_content}
Duration pattern: {duration_pattern}
Paralysis level: {paralysis_level}
Amplification effect: {amplification_effect}
Domain: {domain}
Context: {context}

Is there repetitive passive focus on intellectual distress without moving toward solutions? Return ONLY valid JSON."""


class EpistemicRuminationService:
    """Detects epistemic rumination — repetitive focus on intellectual distress."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        loop_content: str,
        *,
        duration_pattern: str = "",
        paralysis_level: str = "",
        amplification_effect: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic rumination."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_RUMINATION_PROMPT.format(
                loop_content=loop_content,
                duration_pattern=duration_pattern or "Not specified",
                paralysis_level=paralysis_level or "Not specified",
                amplification_effect=amplification_effect or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_RUMINATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "loop_content": loop_content[:200],
            "rumination_detected": data.get("rumination_detected", False),
            "severity": data.get("severity", ""),
            "duration_pattern": data.get("duration_pattern", ""),
            "paralysis_level": data.get("paralysis_level", ""),
            "amplification_effect": data.get("amplification_effect", ""),
            "recommendation": data.get("recommendation", ""),
        }
