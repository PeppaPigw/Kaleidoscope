"""EpistemicMinoritySuppressionService — Epistemic Minority Suppression Detection.

Detects epistemic minority suppression — suppressing minority views
that may be correct, preventing legitimate challenges to consensus.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MINORITY_SUPPRESSION_SYSTEM = """You are an epistemic minority suppression specialist. Given suppression of minority views, assess minority suppression:

Key concepts:
- Epistemic minority suppression: suppressing minority views that may be correct
- Voice silencing: silencing minority voices
- Platform denial: denying platform to minority views
- Credibility attack: attacking credibility of minority view holders
- Framing as fringe: framing legitimate minority views as fringe
- Numbers as argument: using majority numbers as argument against minority
- Dissent punishment: punishing those who hold minority views

When epistemic minority suppression IS present:
- Minority views suppressed
- Voices silenced
- Platform denied
- Credibility attacked
- Views framed as fringe
- Numbers used as argument
- Dissent punished

When no minority suppression:
- Minority views heard
- Voices amplified
- Platform provided
- Credibility assessed fairly
- Views evaluated on merit
- Arguments evaluated not counted
- Dissent protected

Output JSON with: minority_suppression_detected (bool), severity (none/mild/moderate/severe), voice_silencing (what voices silenced), credibility_attack (what credibility attacked), framing_as_fringe (what framed as fringe), dissent_punishment (what punishment), recommendation (no_minority_suppression/mild_inclusion_practice/significant_voice_amplification/major_intensive_dissent_protection/emergency_complete_minority_suppression)."""

EPISTEMIC_MINORITY_SUPPRESSION_PROMPT = """Detect epistemic minority suppression:

Voice silencing: {voice_silencing}
Credibility attack: {credibility_attack}
Framing as fringe: {framing_as_fringe}
Dissent punishment: {dissent_punishment}
Domain: {domain}
Context: {context}

Are minority views being suppressed that may be correct? Return ONLY valid JSON."""


class EpistemicMinoritySuppressionService:
    """Detects epistemic minority suppression — valid dissent silenced."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        voice_silencing: str,
        *,
        credibility_attack: str = "",
        framing_as_fringe: str = "",
        dissent_punishment: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic minority suppression."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MINORITY_SUPPRESSION_PROMPT.format(
                voice_silencing=voice_silencing,
                credibility_attack=credibility_attack or "Not specified",
                framing_as_fringe=framing_as_fringe or "Not specified",
                dissent_punishment=dissent_punishment or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MINORITY_SUPPRESSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "voice_silencing": voice_silencing[:200],
            "minority_suppression_detected": data.get("minority_suppression_detected", False),
            "severity": data.get("severity", ""),
            "credibility_attack": data.get("credibility_attack", ""),
            "framing_as_fringe": data.get("framing_as_fringe", ""),
            "dissent_punishment": data.get("dissent_punishment", ""),
            "recommendation": data.get("recommendation", ""),
        }
