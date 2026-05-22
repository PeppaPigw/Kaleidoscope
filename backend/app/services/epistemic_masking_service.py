"""EpistemicMaskingService — Epistemic Masking Detection.

Detects epistemic masking — louder ideas making quieter but important
ideas inaudible through frequency overlap.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MASKING_SYSTEM = """You are an epistemic masking specialist. Given an idea audibility pattern, assess whether louder ideas make quieter ones inaudible:

Key concepts:
- Epistemic masking: louder ideas making quieter ones inaudible
- Masker: the louder idea that obscures others
- Maskee: the quieter idea being obscured
- Frequency overlap: ideas in same intellectual band
- Temporal masking: ideas obscured by timing proximity
- Upward spread: loud low ideas masking higher ones
- Critical band: frequency range within which masking occurs

When epistemic masking IS present:
- Louder ideas making quieter but important ideas inaudible
- Dominant ideas obscuring others
- Important ideas being obscured by dominant ones
- Ideas in same intellectual frequency band competing
- Ideas obscured by timing proximity to louder ones
- Loud basic ideas masking more nuanced ones
- Masking occurring within specific intellectual ranges

When full audibility is present:
- All ideas audible regardless of volume
- No dominant ideas obscuring others
- No important ideas being hidden
- Ideas in different frequency bands not competing
- No temporal interference between ideas
- Basic and nuanced ideas both clear
- No frequency-based masking

Output JSON with: masking_present (bool), severity (none/mild/moderate/severe), masker (what louder idea), maskee (what is obscured), overlap (what frequency band), temporal (what timing interference), recommendation (full_audibility/mild_masking/significant_masking/major_obscuring/separate_frequency_bands)."""

EPISTEMIC_MASKING_PROMPT = """Detect epistemic masking:

Masker: {masker}
Maskee: {maskee}
Overlap: {overlap}
Temporal: {temporal}
Domain: {domain}
Context: {context}

Are louder ideas making quieter but important ideas inaudible through frequency overlap? Return ONLY valid JSON."""


class EpistemicMaskingService:
    """Detects epistemic masking — louder ideas obscuring quieter ones."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        masker: str,
        *,
        maskee: str = "",
        overlap: str = "",
        temporal: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic masking."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MASKING_PROMPT.format(
                masker=masker,
                maskee=maskee or "Not specified",
                overlap=overlap or "Not specified",
                temporal=temporal or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MASKING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "masker": masker[:200],
            "masking_present": data.get("masking_present", False),
            "severity": data.get("severity", ""),
            "maskee": data.get("maskee", ""),
            "overlap": data.get("overlap", ""),
            "temporal": data.get("temporal", ""),
            "recommendation": data.get("recommendation", ""),
        }
