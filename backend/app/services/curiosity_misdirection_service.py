"""CuriosityMisdirectionService — Curiosity Misdirection Detection.

Detects curiosity misdirection — curiosity directed toward entertaining
or novel questions rather than important ones, where intellectual
interest substitutes for epistemic priority.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CURIOSITY_MISDIRECTION_SYSTEM = """You are a curiosity misdirection specialist. Given an inquiry pattern, assess whether curiosity is directed away from important questions:

Key concepts:
- Curiosity misdirection: curiosity toward entertaining not important
- Intellectual entertainment: pursuing interesting over significant
- Priority inversion: fascinating questions displacing urgent ones
- Novelty-driven inquiry: new questions preferred over important ones
- Difficulty avoidance: easy interesting questions over hard important ones
- Intellectual tourism: broad shallow curiosity avoiding depth
- Distraction by fascination: interesting tangents displacing core inquiry

When curiosity misdirection IS present:
- Curiosity directed at entertaining not important questions
- Fascinating tangents displacing core inquiry
- Novel questions preferred over significant ones
- Easy interesting questions chosen over hard important ones
- Intellectual entertainment substituting for serious inquiry
- Broad shallow exploration avoiding necessary depth
- Curiosity serving distraction not understanding

When curiosity direction is appropriate:
- Curiosity aligned with important questions
- Interesting and important questions overlap
- Tangential exploration bounded and purposeful
- Depth pursued where needed
- Novelty serving genuine knowledge gaps
- Curiosity proportionate to question importance
- Intellectual interest serving epistemic goals

Output JSON with: misdirection_present (bool), severity (none/mild/moderate/severe), inquiry (what inquiry is pursued), entertaining_focus (what entertaining questions dominate), important_neglected (what important questions are neglected), displacement (how importance is displaced), recommendation (appropriate_curiosity/mild_entertainment_preference/significant_curiosity_misdirection/major_importance_avoidance/redirect_curiosity_to_important_questions)."""

CURIOSITY_MISDIRECTION_PROMPT = """Detect curiosity misdirection:

Inquiry focus: {inquiry}
Entertaining questions: {entertaining}
Important questions: {important}
Allocation: {allocation}
Domain: {domain}
Context: {context}

Is curiosity directed toward entertaining rather than important questions? Return ONLY valid JSON."""


class CuriosityMisdirectionService:
    """Detects curiosity misdirection — curiosity toward entertaining not important."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        inquiry: str,
        *,
        entertaining: str = "",
        important: str = "",
        allocation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect curiosity misdirection."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CURIOSITY_MISDIRECTION_PROMPT.format(
                inquiry=inquiry,
                entertaining=entertaining or "Not specified",
                important=important or "Not specified",
                allocation=allocation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CURIOSITY_MISDIRECTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "inquiry": inquiry[:200],
            "misdirection_present": data.get("misdirection_present", False),
            "severity": data.get("severity", ""),
            "entertaining_focus": data.get("entertaining_focus", ""),
            "important_neglected": data.get("important_neglected", ""),
            "displacement": data.get("displacement", ""),
            "recommendation": data.get("recommendation", ""),
        }
