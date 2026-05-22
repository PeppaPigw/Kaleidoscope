"""EpistemicPaternalismService — Epistemic Paternalism Detection.

Detects epistemic paternalism — deciding for others what they should
believe 'for their own good' without respecting their epistemic autonomy.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PATERNALISM_SYSTEM = """You are an epistemic paternalism specialist. Given a knowledge-sharing situation, assess whether someone is deciding for others what they should believe:

Key concepts:
- Epistemic paternalism: deciding beliefs for others for their own good
- Autonomy override: overriding others' epistemic autonomy
- Protective withholding: withholding information to protect
- Belief management: managing others' beliefs without consent
- Infantilizing protection: protecting others from knowledge they can handle
- Benevolent control: controlling beliefs with benevolent intent
- Truth gatekeeping: gatekeeping truth for others' supposed benefit

When epistemic paternalism IS present:
- Beliefs decided for others without their consent
- Epistemic autonomy overridden for supposed benefit
- Information withheld to protect from truth
- Others' beliefs managed without their knowledge
- Capable agents treated as needing protection
- Control exercised with benevolent justification
- Truth gatekept for others' supposed good

When appropriate guidance is present:
- Information shared respecting autonomy
- Guidance offered not imposed
- Protection proportionate to genuine vulnerability
- Beliefs respected as others' own
- Capability acknowledged and supported
- Help offered without control
- Truth shared with appropriate context

Output JSON with: paternalism_present (bool), severity (none/mild/moderate/severe), situation (what situation exists), autonomy_override (how autonomy is overridden), justification (what justification is given), target_capability (what capability target actually has), recommendation (appropriate_guidance/mild_overprotection/significant_epistemic_paternalism/major_autonomy_override/respect_epistemic_autonomy)."""

EPISTEMIC_PATERNALISM_PROMPT = """Detect epistemic paternalism:

Situation: {situation}
Autonomy override: {override}
Justification: {justification}
Target capability: {capability}
Domain: {domain}
Context: {context}

Is someone deciding for others what they should believe? Return ONLY valid JSON."""


class EpistemicPaternalismService:
    """Detects epistemic paternalism — deciding beliefs for others."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        override: str = "",
        justification: str = "",
        capability: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic paternalism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PATERNALISM_PROMPT.format(
                situation=situation,
                override=override or "Not specified",
                justification=justification or "Not specified",
                capability=capability or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PATERNALISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "paternalism_present": data.get("paternalism_present", False),
            "severity": data.get("severity", ""),
            "autonomy_override": data.get("autonomy_override", ""),
            "justification": data.get("justification", ""),
            "target_capability": data.get("target_capability", ""),
            "recommendation": data.get("recommendation", ""),
        }
