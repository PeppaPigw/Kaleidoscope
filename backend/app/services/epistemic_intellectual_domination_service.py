"""EpistemicIntellectualDominationService — Epistemic Intellectual Domination Detection.

Detects epistemic intellectual domination — using knowledge to dominate
and control others in intellectual exchanges.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INTELLECTUAL_DOMINATION_SYSTEM = """You are an epistemic intellectual domination specialist. Given using knowledge to dominate, assess intellectual domination:

Key concepts:
- Epistemic intellectual domination: using knowledge to control others
- Knowledge as power: wielding understanding as dominance tool
- Intellectual intimidation: using expertise to cow others
- Discussion control: steering all exchanges to maintain power
- Answer monopoly: insisting on being the authority
- Question suppression: preventing others from challenging
- Intellectual coercion: forcing agreement through knowledge pressure

When epistemic intellectual domination IS present:
- Using knowledge to control
- Wielding understanding as power
- Using expertise to intimidate
- Steering exchanges for power
- Insisting on being authority
- Preventing challenges
- Forcing agreement

When no intellectual domination:
- Knowledge shared freely
- Understanding as gift
- Expertise as invitation
- Collaborative exchanges
- Shared authority
- Welcoming challenges
- Earning agreement

Output JSON with: intellectual_domination_detected (bool), severity (none/mild/moderate/severe), knowledge_as_power (what wielding), intellectual_intimidation (what intimidating with), discussion_control (what steering), question_suppression (what preventing), recommendation (no_intellectual_domination/mild_sharing_practice/significant_collaboration_work/major_intensive_power_processing/emergency_active_coercion)."""

EPISTEMIC_INTELLECTUAL_DOMINATION_PROMPT = """Detect epistemic intellectual domination:

Knowledge as power: {knowledge_as_power}
Intellectual intimidation: {intellectual_intimidation}
Discussion control: {discussion_control}
Question suppression: {question_suppression}
Domain: {domain}
Context: {context}

Is there using knowledge to dominate and control others? Return ONLY valid JSON."""


class EpistemicIntellectualDominationService:
    """Detects epistemic intellectual domination — using knowledge to control others."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge_as_power: str,
        *,
        intellectual_intimidation: str = "",
        discussion_control: str = "",
        question_suppression: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic intellectual domination."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INTELLECTUAL_DOMINATION_PROMPT.format(
                knowledge_as_power=knowledge_as_power,
                intellectual_intimidation=intellectual_intimidation or "Not specified",
                discussion_control=discussion_control or "Not specified",
                question_suppression=question_suppression or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INTELLECTUAL_DOMINATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge_as_power": knowledge_as_power[:200],
            "intellectual_domination_detected": data.get("intellectual_domination_detected", False),
            "severity": data.get("severity", ""),
            "intellectual_intimidation": data.get("intellectual_intimidation", ""),
            "discussion_control": data.get("discussion_control", ""),
            "question_suppression": data.get("question_suppression", ""),
            "recommendation": data.get("recommendation", ""),
        }
