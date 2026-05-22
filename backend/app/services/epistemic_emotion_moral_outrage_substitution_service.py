"""EpistemicEmotionMoralOutrageSubstitutionService - Epistemic Emotion Moral Outrage Substitution Detection.

Detects moral outrage substitution where emotional intensity replaces evidence evaluation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EMOTION_MORAL_OUTRAGE_SUBSTITUTION_SYSTEM = """You are an epistemic emotion moral outrage substitution specialist. Given outrage as argument, assess moral outrage replacing evidence evaluation:

Key concepts:
- Epistemic emotion moral outrage substitution: emotional intensity replacing evidence evaluation
- Outrage as argument: moral anger treated as sufficient reason
- Indignation as proof: strength of indignation treated as evidence
- Emotional certainty: conviction arising from intensity of feeling
- Feeling as knowing: felt moral clarity substituted for inquiry

When moral outrage substitution IS present:
- Outrage functions as the argument
- Indignation is treated as proof
- Emotional certainty outruns evidence
- Feeling is treated as knowing
- Evidence evaluation is displaced

When no moral outrage substitution:
- Moral emotion is distinguished from evidence
- Indignation prompts inquiry rather than replaces it
- Certainty remains evidence-calibrated
- Feelings are checked against reasons
- Evidence evaluation remains active

Output JSON with: moral_outrage_substitution_detected (bool), severity (none/mild/moderate/severe), indignation_as_proof (what indignation is treated as proof), emotional_certainty (what certainty comes from emotion), feeling_as_knowing (what feeling is treated as knowledge), recommendation (no_outrage_substitution/mild_evidence_check/significant_emotion_evidence_separation/major_argument_reconstruction/emergency_complete_outrage_substitution)."""

EPISTEMIC_EMOTION_MORAL_OUTRAGE_SUBSTITUTION_PROMPT = """Detect epistemic emotion moral outrage substitution:

Outrage as argument: {outrage_as_argument}
Indignation as proof: {indignation_as_proof}
Emotional certainty: {emotional_certainty}
Feeling as knowing: {feeling_as_knowing}
Domain: {domain}
Context: {context}

Is moral outrage replacing evidence evaluation? Return ONLY valid JSON."""


class EpistemicEmotionMoralOutrageSubstitutionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        outrage_as_argument: str,
        *,
        indignation_as_proof: str = "",
        emotional_certainty: str = "",
        feeling_as_knowing: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EMOTION_MORAL_OUTRAGE_SUBSTITUTION_PROMPT.format(
                outrage_as_argument=outrage_as_argument,
                indignation_as_proof=indignation_as_proof or "Not specified",
                emotional_certainty=emotional_certainty or "Not specified",
                feeling_as_knowing=feeling_as_knowing or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EMOTION_MORAL_OUTRAGE_SUBSTITUTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "outrage_as_argument": outrage_as_argument[:200],
            "moral_outrage_substitution_detected": data.get("moral_outrage_substitution_detected", False),
            "severity": data.get("severity", ""),
            "indignation_as_proof": data.get("indignation_as_proof", ""),
            "emotional_certainty": data.get("emotional_certainty", ""),
            "feeling_as_knowing": data.get("feeling_as_knowing", ""),
            "recommendation": data.get("recommendation", ""),
        }
