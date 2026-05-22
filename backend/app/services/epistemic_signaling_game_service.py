"""EpistemicSignalingGameService — Epistemic Signaling Game Detection.

Detects epistemic signaling game — intellectual positions adopted not for
their truth value but to signal group membership or competence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SIGNALING_GAME_SYSTEM = """You are an epistemic signaling game specialist. Given an intellectual position, assess whether it is adopted for signaling rather than truth:

Key concepts:
- Epistemic signaling game: positions adopted for signaling
- Costly signal: expensive to fake, proving authenticity
- Cheap talk: costless claims that may be unreliable
- Separating equilibrium: different types send different signals
- Pooling equilibrium: all types send same signal
- Screening: receiver designing tests to reveal type
- Credible commitment: binding oneself to prove sincerity

When epistemic signaling game IS present:
- Positions adopted for signaling rather than truth
- Costly intellectual investments proving authenticity
- Costless claims that may be unreliable
- Different groups sending different intellectual signals
- All groups sending same signal obscuring differences
- Tests designed to reveal true intellectual type
- Binding commitments proving sincerity

When truth-seeking is present:
- Positions adopted for truth value
- No signaling motivation
- All claims equally costly
- No group differentiation through signals
- No pooling obscuring differences
- No screening tests needed
- No commitment devices needed

Output JSON with: signaling_game_present (bool), severity (none/mild/moderate/severe), costly_signal (what expensive proof), cheap_talk (what unreliable claims), separating (what differentiation), screening (what tests), recommendation (truth_seeking/mild_signaling/significant_signaling_game/major_signal_over_truth/separate_signal_from_substance)."""

EPISTEMIC_SIGNALING_GAME_PROMPT = """Detect epistemic signaling game:

Costly signal: {costly_signal}
Cheap talk: {cheap_talk}
Separating: {separating}
Screening: {screening}
Domain: {domain}
Context: {context}

Are intellectual positions adopted not for their truth value but to signal group membership or competence? Return ONLY valid JSON."""


class EpistemicSignalingGameService:
    """Detects epistemic signaling game — positions for signaling not truth."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        costly_signal: str,
        *,
        cheap_talk: str = "",
        separating: str = "",
        screening: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic signaling game."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SIGNALING_GAME_PROMPT.format(
                costly_signal=costly_signal,
                cheap_talk=cheap_talk or "Not specified",
                separating=separating or "Not specified",
                screening=screening or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SIGNALING_GAME_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "costly_signal": costly_signal[:200],
            "signaling_game_present": data.get("signaling_game_present", False),
            "severity": data.get("severity", ""),
            "cheap_talk": data.get("cheap_talk", ""),
            "separating": data.get("separating", ""),
            "screening": data.get("screening", ""),
            "recommendation": data.get("recommendation", ""),
        }
