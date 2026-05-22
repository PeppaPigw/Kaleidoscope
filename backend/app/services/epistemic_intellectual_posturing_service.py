"""EpistemicIntellectualPosturingService — Epistemic Intellectual Posturing Detection.

Detects epistemic intellectual posturing — posturing expertise or
understanding one doesn't actually have.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INTELLECTUAL_POSTURING_SYSTEM = """You are an epistemic intellectual posturing specialist. Given posturing expertise not actually held, assess intellectual posturing:

Key concepts:
- Epistemic intellectual posturing: posturing expertise not actually held
- Knowledge bluffing: pretending to know more than one does
- Jargon deployment: using technical language to appear knowledgeable
- Citation dropping: referencing works not actually read
- Complexity performance: making simple things complex to appear smart
- Understanding theater: nodding along without genuine comprehension
- Expertise inflation: overstating one's actual knowledge level

When epistemic intellectual posturing IS present:
- Posturing expertise not held
- Pretending to know more
- Using jargon to appear knowledgeable
- Referencing unread works
- Making things complex to appear smart
- Nodding without comprehension
- Overstating knowledge level

When no intellectual posturing:
- Honest about expertise level
- Admitting knowledge gaps
- Using jargon appropriately
- Genuine citations
- Appropriate complexity
- Asking when not understanding
- Accurate self-assessment

Output JSON with: intellectual_posturing_detected (bool), severity (none/mild/moderate/severe), knowledge_bluffing (what pretending to know), jargon_deployment (what using to appear smart), complexity_performance (what making complex), understanding_theater (what pretending to understand), recommendation (no_intellectual_posturing/mild_honesty_practice/significant_humility_building/major_intensive_authenticity_work/emergency_complete_expertise_fabrication)."""

EPISTEMIC_INTELLECTUAL_POSTURING_PROMPT = """Detect epistemic intellectual posturing:

Knowledge bluffing: {knowledge_bluffing}
Jargon deployment: {jargon_deployment}
Complexity performance: {complexity_performance}
Understanding theater: {understanding_theater}
Domain: {domain}
Context: {context}

Is there posturing expertise or understanding not actually held? Return ONLY valid JSON."""


class EpistemicIntellectualPosturingService:
    """Detects epistemic intellectual posturing — posturing expertise not held."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge_bluffing: str,
        *,
        jargon_deployment: str = "",
        complexity_performance: str = "",
        understanding_theater: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic intellectual posturing."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INTELLECTUAL_POSTURING_PROMPT.format(
                knowledge_bluffing=knowledge_bluffing,
                jargon_deployment=jargon_deployment or "Not specified",
                complexity_performance=complexity_performance or "Not specified",
                understanding_theater=understanding_theater or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INTELLECTUAL_POSTURING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge_bluffing": knowledge_bluffing[:200],
            "intellectual_posturing_detected": data.get("intellectual_posturing_detected", False),
            "severity": data.get("severity", ""),
            "jargon_deployment": data.get("jargon_deployment", ""),
            "complexity_performance": data.get("complexity_performance", ""),
            "understanding_theater": data.get("understanding_theater", ""),
            "recommendation": data.get("recommendation", ""),
        }
