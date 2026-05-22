"""EpistemicSupercoolingService — Epistemic Supercooling Detection.

Detects epistemic supercooling — ideas remaining in a liquid uncertain
state well below the temperature where they should have solidified into belief.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SUPERCOOLING_SYSTEM = """You are an epistemic supercooling specialist. Given an idea state pattern, assess whether ideas remain liquid below their solidification point:

Key concepts:
- Epistemic supercooling: ideas liquid below solidification point
- Undercooling: degree below normal solidification temperature
- Metastable: unstable state that persists temporarily
- Nucleation barrier: what prevents solidification
- Flash freezing: sudden solidification when disturbed
- Recalescence: heat released during sudden solidification
- Glass transition: becoming rigid without crystallizing

When epistemic supercooling IS present:
- Ideas remaining uncertain below the point where evidence supports belief
- Degree of evidence beyond what should trigger commitment
- Unstable uncertainty persisting temporarily
- Barriers preventing commitment despite sufficient evidence
- Sudden commitment when slightly disturbed
- Energy released during sudden belief formation
- Ideas becoming rigid without proper crystallization

When normal solidification is present:
- Ideas solidifying into belief at appropriate evidence level
- No excess evidence without commitment
- Stable states at each temperature
- No barriers to appropriate commitment
- Gradual commitment as evidence accumulates
- Smooth energy transitions
- Proper crystallization into structured belief

Output JSON with: supercooling_present (bool), severity (none/mild/moderate/severe), undercooling (what excess evidence without commitment), nucleation_barrier (what prevents solidification), flash_freezing (what triggers sudden commitment), glass_transition (what rigid without structure), recommendation (normal_solidification/mild_supercooling/significant_supercooling/major_commitment_avoidance/provide_nucleation_site)."""

EPISTEMIC_SUPERCOOLING_PROMPT = """Detect epistemic supercooling:

Undercooling: {undercooling}
Nucleation barrier: {nucleation_barrier}
Flash freezing: {flash_freezing}
Glass transition: {glass_transition}
Domain: {domain}
Context: {context}

Are ideas remaining in a liquid uncertain state well below the temperature where they should have solidified into belief? Return ONLY valid JSON."""


class EpistemicSupercoolingService:
    """Detects epistemic supercooling — ideas liquid below solidification point."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        undercooling: str,
        *,
        nucleation_barrier: str = "",
        flash_freezing: str = "",
        glass_transition: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic supercooling."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SUPERCOOLING_PROMPT.format(
                undercooling=undercooling,
                nucleation_barrier=nucleation_barrier or "Not specified",
                flash_freezing=flash_freezing or "Not specified",
                glass_transition=glass_transition or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SUPERCOOLING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "undercooling": undercooling[:200],
            "supercooling_present": data.get("supercooling_present", False),
            "severity": data.get("severity", ""),
            "nucleation_barrier": data.get("nucleation_barrier", ""),
            "flash_freezing": data.get("flash_freezing", ""),
            "glass_transition": data.get("glass_transition", ""),
            "recommendation": data.get("recommendation", ""),
        }
