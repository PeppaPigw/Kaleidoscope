"""EpistemicFrictionService — Epistemic Friction Detection.

Detects epistemic friction — unnecessary resistance slowing
knowledge transfer and integration.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FRICTION_SYSTEM = """You are an epistemic friction specialist. Given a knowledge transfer situation, assess whether unnecessary resistance is slowing integration:

Key concepts:
- Epistemic friction: unnecessary resistance to knowledge transfer
- Transfer resistance: resistance slowing knowledge movement
- Integration barriers: barriers preventing knowledge integration
- Jargon walls: specialized language blocking understanding
- Institutional resistance: institutional structures blocking flow
- Format incompatibility: knowledge in incompatible formats
- Translation loss: meaning lost in translation between contexts

When epistemic friction IS present:
- Unnecessary resistance slowing knowledge transfer
- Resistance not serving any protective function
- Barriers preventing integration without good reason
- Specialized language blocking rather than enabling
- Institutional structures blocking knowledge flow
- Knowledge in incompatible formats without translation
- Meaning lost unnecessarily in transfer

When healthy gatekeeping is present:
- Resistance serving quality control function
- Barriers protecting against misinformation
- Specialization enabling precision
- Institutional review ensuring quality
- Format requirements ensuring rigor
- Translation maintaining fidelity
- Friction proportionate to risk

Output JSON with: friction_present (bool), severity (none/mild/moderate/severe), situation (what transfer situation), resistance (what resistance exists), barrier (what barriers exist), purpose (whether friction serves purpose), recommendation (healthy_gatekeeping/mild_friction/significant_epistemic_friction/major_transfer_blockage/reduce_unnecessary_barriers)."""

EPISTEMIC_FRICTION_PROMPT = """Detect epistemic friction:

Situation: {situation}
Resistance: {resistance}
Barrier: {barrier}
Purpose: {purpose}
Domain: {domain}
Context: {context}

Is unnecessary resistance slowing knowledge transfer and integration? Return ONLY valid JSON."""


class EpistemicFrictionService:
    """Detects epistemic friction — unnecessary resistance to knowledge transfer."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        resistance: str = "",
        barrier: str = "",
        purpose: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic friction."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FRICTION_PROMPT.format(
                situation=situation,
                resistance=resistance or "Not specified",
                barrier=barrier or "Not specified",
                purpose=purpose or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FRICTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "friction_present": data.get("friction_present", False),
            "severity": data.get("severity", ""),
            "resistance": data.get("resistance", ""),
            "barrier": data.get("barrier", ""),
            "purpose": data.get("purpose", ""),
            "recommendation": data.get("recommendation", ""),
        }
