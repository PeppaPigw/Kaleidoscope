"""EpistemicQuestionSubstitutionDeeperService — Epistemic Question Substitution Detection (Deeper).

Detects epistemic question substitution — substituting an easier question
for the one actually asked, answering a different question than posed.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_QUESTION_SUBSTITUTION_DEEPER_SYSTEM = """You are an epistemic question substitution specialist. Given substitution of easier questions, assess question substitution:

Key concepts:
- Epistemic question substitution: answering a different question than asked
- Difficulty avoidance: substituting easier question to avoid difficulty
- Attribute substitution: substituting accessible attribute for target attribute
- Proxy confusion: confusing proxy question with actual question
- Answerable bias: bias toward questions that are answerable
- Precision theater: answering precise but wrong question precisely
- Relevance drift: drifting from relevant question to answerable one

When epistemic question substitution IS present:
- Different question answered
- Easier question substituted
- Attribute substituted
- Proxy confused with actual
- Answerable preferred over relevant
- Wrong question answered precisely
- Relevance drifting

When no question substitution:
- Actual question addressed
- Difficulty engaged
- Target attribute assessed
- Actual question distinguished from proxy
- Relevant preferred over answerable
- Right question addressed
- Relevance maintained

Output JSON with: question_substitution_detected (bool), severity (none/mild/moderate/severe), difficulty_avoidance (what difficulty avoided), attribute_substitution (what attribute substituted), proxy_confusion (what proxy confused), precision_theater (what wrong question answered precisely), recommendation (no_question_substitution/mild_question_refocus/significant_actual_question_recovery/major_intensive_difficulty_engagement/emergency_complete_question_substitution)."""

EPISTEMIC_QUESTION_SUBSTITUTION_DEEPER_PROMPT = """Detect epistemic question substitution:

Difficulty avoidance: {difficulty_avoidance}
Attribute substitution: {attribute_substitution}
Proxy confusion: {proxy_confusion}
Precision theater: {precision_theater}
Domain: {domain}
Context: {context}

Is an easier question being substituted for the one actually asked? Return ONLY valid JSON."""


class EpistemicQuestionSubstitutionDeeperService:
    """Detects epistemic question substitution — answering wrong question."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        difficulty_avoidance: str,
        *,
        attribute_substitution: str = "",
        proxy_confusion: str = "",
        precision_theater: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic question substitution."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_QUESTION_SUBSTITUTION_DEEPER_PROMPT.format(
                difficulty_avoidance=difficulty_avoidance,
                attribute_substitution=attribute_substitution or "Not specified",
                proxy_confusion=proxy_confusion or "Not specified",
                precision_theater=precision_theater or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_QUESTION_SUBSTITUTION_DEEPER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "difficulty_avoidance": difficulty_avoidance[:200],
            "question_substitution_detected": data.get("question_substitution_detected", False),
            "severity": data.get("severity", ""),
            "attribute_substitution": data.get("attribute_substitution", ""),
            "proxy_confusion": data.get("proxy_confusion", ""),
            "precision_theater": data.get("precision_theater", ""),
            "recommendation": data.get("recommendation", ""),
        }
