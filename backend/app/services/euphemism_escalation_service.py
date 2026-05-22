"""EuphemismEscalationService — Euphemism Escalation Detection.

Detects euphemism escalation — progressive use of euphemism that
obscures reality, where language becomes increasingly disconnected
from what it describes to avoid confronting uncomfortable truths.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EUPHEMISM_ESCALATION_SYSTEM = """You are a euphemism escalation specialist. Given language use, assess whether euphemism is progressively obscuring reality:

Key concepts:
- Euphemism escalation: progressive obscuring through language
- Reality disconnection: language drifting from what it describes
- Comfort over clarity: choosing comfort over accurate description
- Semantic inflation: words losing connection to referents
- Accountability avoidance: euphemism preventing accountability
- Normalization through language: making harmful things sound normal
- Doublespeak: language that reverses or obscures meaning

When euphemism escalation IS present:
- Language progressively disconnected from reality
- Euphemisms layered to avoid confronting truth
- Comfort prioritized over accurate description
- Words losing connection to what they describe
- Euphemism preventing accountability
- Harmful realities normalized through language
- Meaning obscured rather than communicated

When careful language is appropriate:
- Sensitivity to audience without obscuring truth
- Technical terminology that adds precision
- Diplomatic language that preserves relationships
- Context-appropriate register
- Language that respects dignity without hiding reality
- Euphemism acknowledged as such
- Clarity maintained alongside sensitivity

Output JSON with: escalation_present (bool), severity (none/mild/moderate/severe), language (what language is used), reality (what reality is obscured), progression (how euphemism has escalated), accountability_lost (what accountability is avoided), recommendation (appropriate_careful_language/mild_euphemism/significant_euphemism_escalation/major_reality_obscuring/name_reality_clearly)."""

EUPHEMISM_ESCALATION_PROMPT = """Detect euphemism escalation:

Language used: {language}
Reality described: {reality}
Previous terms: {previous}
Effect on understanding: {effect}
Domain: {domain}
Context: {context}

Is euphemism progressively obscuring reality? Return ONLY valid JSON."""


class EuphemismEscalationService:
    """Detects euphemism escalation — progressive obscuring through language."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        language: str,
        *,
        reality: str = "",
        previous: str = "",
        effect: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect euphemism escalation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EUPHEMISM_ESCALATION_PROMPT.format(
                language=language,
                reality=reality or "Not specified",
                previous=previous or "Not specified",
                effect=effect or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EUPHEMISM_ESCALATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "language": language[:200],
            "escalation_present": data.get("escalation_present", False),
            "severity": data.get("severity", ""),
            "reality": data.get("reality", ""),
            "progression": data.get("progression", ""),
            "accountability_lost": data.get("accountability_lost", ""),
            "recommendation": data.get("recommendation", ""),
        }
