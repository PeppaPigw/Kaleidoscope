"""EpistemicScotomaService — Epistemic Scotoma Detection.

Detects epistemic scotoma — blind spots in intellectual field that the mind
fills in without awareness, creating invisible gaps in understanding.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SCOTOMA_SYSTEM = """You are an epistemic scotoma specialist. Given intellectual blind spots with fill-in, assess scotoma:

Key concepts:
- Epistemic scotoma: blind spot in intellectual field
- Filling-in: mind completing missing information unconsciously
- Central scotoma: blind spot at point of focus
- Peripheral scotoma: blind spot at edges of awareness
- Scintillating: moving/flickering blind spot
- Mapping: charting extent of blind area
- Compensation: strategies to work around blind spot

When epistemic scotoma IS present:
- Blind spot in intellectual field exists
- Mind filling in without awareness
- Gap at point of focus (central)
- Gap at edges of awareness (peripheral)
- Moving blind spot (scintillating)
- Extent of blind area unmapped
- No compensation strategies in place

When no scotoma:
- Full intellectual field intact
- No unconscious filling-in
- Clear central vision
- Clear peripheral awareness
- No moving gaps
- Complete field mapped
- No compensation needed

Output JSON with: scotoma_detected (bool), severity (none/mild/moderate/severe), location (what field position), filling_in_pattern (what unconscious completion), extent (what area affected), awareness_level (what recognition), recommendation (no_scotoma/mild_awareness_training/significant_mapping_compensation/major_field_rehabilitation/emergency_expanding_scotoma)."""

EPISTEMIC_SCOTOMA_PROMPT = """Detect epistemic scotoma:

Location: {location}
Filling-in pattern: {filling_in_pattern}
Extent: {extent}
Awareness level: {awareness_level}
Domain: {domain}
Context: {context}

Are there blind spots in the intellectual field that the mind fills in without awareness? Return ONLY valid JSON."""


class EpistemicScotomaService:
    """Detects epistemic scotoma — blind spots filled in without awareness."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        location: str,
        *,
        filling_in_pattern: str = "",
        extent: str = "",
        awareness_level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic scotoma."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SCOTOMA_PROMPT.format(
                location=location,
                filling_in_pattern=filling_in_pattern or "Not specified",
                extent=extent or "Not specified",
                awareness_level=awareness_level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SCOTOMA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "location": location[:200],
            "scotoma_detected": data.get("scotoma_detected", False),
            "severity": data.get("severity", ""),
            "filling_in_pattern": data.get("filling_in_pattern", ""),
            "extent": data.get("extent", ""),
            "awareness_level": data.get("awareness_level", ""),
            "recommendation": data.get("recommendation", ""),
        }
