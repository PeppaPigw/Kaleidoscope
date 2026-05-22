"""EmotionalEpistemicBypassService — Emotional Epistemic Bypass Detection.

Detects emotional epistemic bypass — using emotional intensity to
bypass rational evaluation, where strong feelings are treated as
evidence or used to short-circuit critical thinking.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EMOTIONAL_EPISTEMIC_BYPASS_SYSTEM = """You are an emotional epistemic bypass specialist. Given an argument or claim, assess whether emotion is bypassing rational evaluation:

Key concepts:
- Emotional epistemic bypass: feelings replacing evidence
- Emotional reasoning: feeling it therefore true
- Intensity as evidence: strong feeling as proof
- Affective override: emotion overriding analysis
- Sentiment as argument: how I feel as why it's true
- Emotional certainty: feeling certain without evidence
- Passion as proof: conviction as substitute for evidence

When emotional epistemic bypass IS present:
- Emotional intensity treated as evidence
- Feelings used to bypass critical evaluation
- Strong emotions short-circuit analysis
- Sentiment presented as argument
- Emotional certainty substitutes for evidence
- Passion treated as proof of correctness
- Affective state overrides rational assessment

When emotional engagement is appropriate:
- Emotions inform but don't replace evidence
- Feelings acknowledged alongside analysis
- Emotional engagement motivates inquiry
- Sentiment and evidence distinguished
- Emotional responses examined critically
- Passion drives investigation not conclusion
- Affect and reason work together

Output JSON with: bypass_present (bool), severity (none/mild/moderate/severe), argument (what argument is made), emotion (what emotion is involved), bypass_mechanism (how emotion bypasses reason), evidence_gap (what evidence is missing), recommendation (appropriate_emotional_engagement/mild_affective_influence/significant_emotional_bypass/major_reason_override/integrate_emotion_and_evidence)."""

EMOTIONAL_EPISTEMIC_BYPASS_PROMPT = """Detect emotional epistemic bypass:

Argument: {argument}
Emotion involved: {emotion}
Evidence provided: {evidence}
Reasoning quality: {reasoning}
Domain: {domain}
Context: {context}

Is emotional intensity being used to bypass rational evaluation? Return ONLY valid JSON."""


class EmotionalEpistemicBypassService:
    """Detects emotional epistemic bypass — feelings replacing evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        emotion: str = "",
        evidence: str = "",
        reasoning: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect emotional epistemic bypass."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EMOTIONAL_EPISTEMIC_BYPASS_PROMPT.format(
                argument=argument,
                emotion=emotion or "Not specified",
                evidence=evidence or "Not specified",
                reasoning=reasoning or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EMOTIONAL_EPISTEMIC_BYPASS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "bypass_present": data.get("bypass_present", False),
            "severity": data.get("severity", ""),
            "emotion": data.get("emotion", ""),
            "bypass_mechanism": data.get("bypass_mechanism", ""),
            "evidence_gap": data.get("evidence_gap", ""),
            "recommendation": data.get("recommendation", ""),
        }
