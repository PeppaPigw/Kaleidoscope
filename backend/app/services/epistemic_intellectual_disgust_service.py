"""EpistemicIntellectualDisgustService — Epistemic Intellectual Disgust Detection.

Detects epistemic intellectual disgust — visceral disgust at perceived
intellectual inadequacy in others.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INTELLECTUAL_DISGUST_SYSTEM = """You are an epistemic intellectual disgust specialist. Given visceral disgust at intellectual inadequacy, assess intellectual disgust:

Key concepts:
- Epistemic intellectual disgust: visceral disgust at perceived inadequacy
- Cognitive revulsion: physical-like revulsion at poor thinking
- Contamination response: feeling polluted by bad ideas
- Purity violation: seeing poor thinking as impure
- Visceral rejection: gut-level rejection of intellectual weakness
- Disgust generalization: extending disgust from ideas to people
- Moral-intellectual fusion: treating intellectual failure as moral failure

When epistemic intellectual disgust IS present:
- Visceral disgust at inadequacy
- Physical-like revulsion
- Feeling polluted by bad ideas
- Seeing poor thinking as impure
- Gut-level rejection
- Extending disgust to people
- Treating intellectual failure as moral

When no intellectual disgust:
- Patience with inadequacy
- Calm response to poor thinking
- Comfortable with diverse quality
- Accepting imperfection
- Measured rejection
- Separating ideas from people
- Separating intellect from morality

Output JSON with: intellectual_disgust_detected (bool), severity (none/mild/moderate/severe), cognitive_revulsion (what revolted by), contamination_response (what feeling polluted by), purity_violation (what seeing as impure), disgust_generalization (what extending to people), recommendation (no_intellectual_disgust/mild_patience_practice/significant_compassion_building/major_intensive_disgust_processing/emergency_active_dehumanization)."""

EPISTEMIC_INTELLECTUAL_DISGUST_PROMPT = """Detect epistemic intellectual disgust:

Cognitive revulsion: {cognitive_revulsion}
Contamination response: {contamination_response}
Purity violation: {purity_violation}
Disgust generalization: {disgust_generalization}
Domain: {domain}
Context: {context}

Is there visceral disgust at perceived intellectual inadequacy? Return ONLY valid JSON."""


class EpistemicIntellectualDisgustService:
    """Detects epistemic intellectual disgust — visceral disgust at perceived inadequacy."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        cognitive_revulsion: str,
        *,
        contamination_response: str = "",
        purity_violation: str = "",
        disgust_generalization: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic intellectual disgust."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INTELLECTUAL_DISGUST_PROMPT.format(
                cognitive_revulsion=cognitive_revulsion,
                contamination_response=contamination_response or "Not specified",
                purity_violation=purity_violation or "Not specified",
                disgust_generalization=disgust_generalization or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INTELLECTUAL_DISGUST_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "cognitive_revulsion": cognitive_revulsion[:200],
            "intellectual_disgust_detected": data.get("intellectual_disgust_detected", False),
            "severity": data.get("severity", ""),
            "contamination_response": data.get("contamination_response", ""),
            "purity_violation": data.get("purity_violation", ""),
            "disgust_generalization": data.get("disgust_generalization", ""),
            "recommendation": data.get("recommendation", ""),
        }
