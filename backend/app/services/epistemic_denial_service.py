"""EpistemicDenialService — Epistemic Denial Detection.

Detects epistemic denial — refusing to acknowledge reality of intellectual
evidence or implications despite clear and available information.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DENIAL_SYSTEM = """You are an epistemic denial specialist. Given refusal to acknowledge reality, assess denial:

Key concepts:
- Epistemic denial: refusing to acknowledge clear evidence
- Reality avoidance: not facing what is clearly true
- Minimization: acknowledging partially but reducing significance
- Selective attention: only seeing what supports denial
- Rationalization: creating false reasons for ignoring evidence
- Temporal displacement: acknowledging for future but not now
- Emotional protection: denial serving to avoid pain

When epistemic denial IS present:
- Refusing to acknowledge evidence
- Not facing clear truth
- Reducing significance
- Only seeing supporting info
- Creating false reasons
- Future but not now
- Avoiding pain through denial

When no denial:
- Acknowledging evidence
- Facing truth
- Appropriate significance
- Seeing all information
- Honest reasoning
- Present acknowledgment
- Facing pain constructively

Output JSON with: denial_detected (bool), severity (none/mild/moderate/severe), reality_avoidance (what not facing), minimization_pattern (what reducing), selective_attention (what only seeing), emotional_protection (what avoiding pain), recommendation (no_denial/mild_gentle_confrontation/significant_reality_therapy/major_intensive_acceptance/emergency_dangerous_denial)."""

EPISTEMIC_DENIAL_PROMPT = """Detect epistemic denial:

Reality avoidance: {reality_avoidance}
Minimization pattern: {minimization_pattern}
Selective attention: {selective_attention}
Emotional protection: {emotional_protection}
Domain: {domain}
Context: {context}

Is there refusal to acknowledge reality of intellectual evidence despite clear information? Return ONLY valid JSON."""


class EpistemicDenialService:
    """Detects epistemic denial — refusing to acknowledge clear evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reality_avoidance: str,
        *,
        minimization_pattern: str = "",
        selective_attention: str = "",
        emotional_protection: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic denial."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DENIAL_PROMPT.format(
                reality_avoidance=reality_avoidance,
                minimization_pattern=minimization_pattern or "Not specified",
                selective_attention=selective_attention or "Not specified",
                emotional_protection=emotional_protection or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DENIAL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "reality_avoidance": reality_avoidance[:200],
            "denial_detected": data.get("denial_detected", False),
            "severity": data.get("severity", ""),
            "minimization_pattern": data.get("minimization_pattern", ""),
            "selective_attention": data.get("selective_attention", ""),
            "emotional_protection": data.get("emotional_protection", ""),
            "recommendation": data.get("recommendation", ""),
        }
