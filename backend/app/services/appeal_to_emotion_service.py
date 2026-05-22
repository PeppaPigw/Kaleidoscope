"""AppealToEmotionService — Appeal to Emotion Detection.

Detects appeal to emotion (argumentum ad passiones) — using
emotional manipulation (fear, pity, anger, flattery) as a
substitute for logical argument. Emotions are used to bypass
rational evaluation of the claim.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

APPEAL_EMOTION_SYSTEM = """You are an appeal to emotion specialist. Given an argument, assess whether it uses emotional manipulation as a substitute for logical reasoning:

Key concepts:
- Argumentum ad passiones: substituting emotion for logic
- Ad baculum: appeal to fear/force
- Ad misericordiam: appeal to pity
- Ad populum (emotional): appeal to popular sentiment
- Loaded language: words chosen for emotional impact over precision
- Emotional reasoning: "I feel X, therefore X is true"
- Legitimate emotion: emotions can be relevant evidence (distinguish)

When appeal to emotion IS present:
- Using fear to prevent rational evaluation of a claim
- Evoking pity to avoid addressing the logical argument
- Using anger or outrage to bypass critical thinking
- Flattery used to gain agreement without evidence
- "Think of the children!" when children aren't relevant
- Graphic imagery used to prevent rational analysis
- Guilt-tripping as a substitute for argument

When appeal to emotion is NOT present:
- Emotions are relevant to the topic (ethics, welfare, harm)
- Emotional impact is acknowledged alongside logical argument
- Empathy is invoked to understand stakeholders, not to prove a point
- Emotional language is proportionate to actual stakes
- The argument works with or without the emotional component
- Feelings are presented as data about human experience
- Emotional appeals supplement rather than replace evidence

Output JSON with: appeal_to_emotion_present (bool), severity (none/mild/moderate/severe), emotion_type (fear/pity/anger/guilt/flattery/other), emotional_content (what emotional appeal is made), logical_gap (what logical argument is missing), legitimate_relevance (are emotions genuinely relevant here), recommendation (no_appeal_to_emotion/mild_emotional_coloring/significant_appeal_to_emotion/major_emotional_manipulation/provide_logical_argument)."""

APPEAL_EMOTION_PROMPT = """Detect appeal to emotion:

Argument: {argument}
Emotional content: {emotional_content}
Logical basis: {logical_basis}
Stakes: {stakes}
Domain: {domain}
Context: {context}

Does this use emotional manipulation as a substitute for logical argument? Return ONLY valid JSON."""


class AppealToEmotionService:
    """Detects appeal to emotion — emotional manipulation replacing logic."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        emotional_content: str = "",
        logical_basis: str = "",
        stakes: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect appeal to emotion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=APPEAL_EMOTION_PROMPT.format(
                argument=argument,
                emotional_content=emotional_content or "Not specified",
                logical_basis=logical_basis or "Not specified",
                stakes=stakes or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=APPEAL_EMOTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "appeal_to_emotion_present": data.get("appeal_to_emotion_present", False),
            "severity": data.get("severity", ""),
            "emotion_type": data.get("emotion_type", ""),
            "emotional_content": data.get("emotional_content", ""),
            "logical_gap": data.get("logical_gap", ""),
            "recommendation": data.get("recommendation", ""),
        }
