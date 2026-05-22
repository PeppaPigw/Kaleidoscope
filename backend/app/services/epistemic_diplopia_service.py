"""EpistemicDiplopiaService — Epistemic Diplopia Detection.

Detects epistemic diplopia — double vision where a single concept appears
as two distinct incompatible interpretations simultaneously.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DIPLOPIA_SYSTEM = """You are an epistemic diplopia specialist. Given intellectual double vision, assess diplopia:

Key concepts:
- Epistemic diplopia: single concept appearing as two interpretations
- Binocular diplopia: both perspectives producing doubles
- Monocular diplopia: single perspective producing doubles
- Horizontal diplopia: side-by-side doubling
- Vertical diplopia: above-below doubling
- Prism correction: merging doubled images
- Patching: suppressing one image temporarily

When epistemic diplopia IS present:
- Single concept appearing as two interpretations
- Both perspectives producing doubles
- Single perspective producing doubles
- Side-by-side doubling of meaning
- Above-below layering of interpretation
- Unable to merge into single understanding
- Temporary suppression needed

When no diplopia:
- Single clear interpretation per concept
- No doubling from either perspective
- No single-perspective doubling
- No side-by-side splitting
- No layered interpretations
- Clear merged understanding
- No suppression needed

Output JSON with: diplopia_detected (bool), severity (none/mild/moderate/severe), doubling_type (what split pattern), origin (what causes split), fusion_status (what merger ability), compensation (what coping), recommendation (no_diplopia/mild_prism_exercises/significant_vision_therapy/major_surgical_correction/emergency_acute_onset)."""

EPISTEMIC_DIPLOPIA_PROMPT = """Detect epistemic diplopia:

Doubling type: {doubling_type}
Origin: {origin}
Fusion status: {fusion_status}
Compensation: {compensation}
Domain: {domain}
Context: {context}

Is a single concept appearing as two distinct incompatible interpretations simultaneously? Return ONLY valid JSON."""


class EpistemicDiplopiaService:
    """Detects epistemic diplopia — single concept appearing as two interpretations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        doubling_type: str,
        *,
        origin: str = "",
        fusion_status: str = "",
        compensation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic diplopia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DIPLOPIA_PROMPT.format(
                doubling_type=doubling_type,
                origin=origin or "Not specified",
                fusion_status=fusion_status or "Not specified",
                compensation=compensation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DIPLOPIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "doubling_type": doubling_type[:200],
            "diplopia_detected": data.get("diplopia_detected", False),
            "severity": data.get("severity", ""),
            "origin": data.get("origin", ""),
            "fusion_status": data.get("fusion_status", ""),
            "compensation": data.get("compensation", ""),
            "recommendation": data.get("recommendation", ""),
        }
