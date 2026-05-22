"""EpistemicTectonicShiftService — Epistemic Tectonic Shift Detection.

Detects epistemic tectonic shifts — deep structural movements in
knowledge creating surface-level disruptions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TECTONIC_SHIFT_SYSTEM = """You are an epistemic tectonic shift specialist. Given a knowledge landscape, assess whether deep structural movements are creating surface disruptions:

Key concepts:
- Epistemic tectonic shift: deep structural movements in knowledge
- Surface disruption: surface-level effects of deep changes
- Paradigm plate movement: fundamental paradigms shifting
- Fault line activation: existing tensions becoming active
- Conceptual earthquake: sudden disruption from accumulated pressure
- Deep structure change: changes at foundational level
- Aftershock cascade: cascading effects of deep shift

When epistemic tectonic shift IS present:
- Deep structural movements creating surface disruptions
- Surface-level effects of deep foundational changes
- Fundamental paradigms shifting beneath surface
- Existing tensions becoming active and disruptive
- Sudden disruption from accumulated deep pressure
- Changes at foundational level affecting everything above
- Cascading effects from deep structural shift

When surface change is present:
- Changes occurring at surface level only
- No deep structural movement underlying changes
- Paradigms stable beneath surface activity
- Tensions not reflecting deep structural issues
- Changes proportionate and non-disruptive
- Foundation stable despite surface activity
- Effects contained and non-cascading

Output JSON with: tectonic_shift_present (bool), severity (none/mild/moderate/severe), landscape (what landscape is affected), deep_movement (what deep movement exists), surface_disruption (what surface disruption results), fault_lines (what fault lines are active), recommendation (surface_change/mild_movement/significant_tectonic_shift/major_paradigm_earthquake/prepare_for_deep_restructuring)."""

EPISTEMIC_TECTONIC_SHIFT_PROMPT = """Detect epistemic tectonic shift:

Landscape: {landscape}
Deep movement: {deep_movement}
Surface disruption: {surface_disruption}
Fault lines: {fault_lines}
Domain: {domain}
Context: {context}

Are deep structural movements creating surface-level disruptions? Return ONLY valid JSON."""


class EpistemicTectonicShiftService:
    """Detects epistemic tectonic shifts — deep structural movements."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        landscape: str,
        *,
        deep_movement: str = "",
        surface_disruption: str = "",
        fault_lines: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic tectonic shift."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TECTONIC_SHIFT_PROMPT.format(
                landscape=landscape,
                deep_movement=deep_movement or "Not specified",
                surface_disruption=surface_disruption or "Not specified",
                fault_lines=fault_lines or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TECTONIC_SHIFT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "landscape": landscape[:200],
            "tectonic_shift_present": data.get("tectonic_shift_present", False),
            "severity": data.get("severity", ""),
            "deep_movement": data.get("deep_movement", ""),
            "surface_disruption": data.get("surface_disruption", ""),
            "fault_lines": data.get("fault_lines", ""),
            "recommendation": data.get("recommendation", ""),
        }
