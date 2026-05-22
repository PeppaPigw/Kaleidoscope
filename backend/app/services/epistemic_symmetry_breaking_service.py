"""EpistemicSymmetryBreakingService — Epistemic Symmetry Breaking Detection.

Detects epistemic symmetry breaking — hidden symmetries in intellectual
space breaking spontaneously to create structure and differentiation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SYMMETRY_BREAKING_SYSTEM = """You are an epistemic symmetry breaking specialist. Given an intellectual landscape, assess whether hidden symmetries are breaking to create structure:

Key concepts:
- Epistemic symmetry breaking: hidden symmetries breaking to create structure
- Spontaneous breaking: system choosing one state from equivalent options
- Goldstone boson: massless mode from broken continuous symmetry
- Higgs mechanism: broken symmetry giving mass to ideas
- Order parameter: quantity distinguishing broken from unbroken phase
- Phase transition: sudden change when symmetry breaks
- Explicit breaking: external force breaking the symmetry

When epistemic symmetry breaking IS present:
- Hidden equivalences breaking to create differentiation
- System choosing one intellectual direction from equivalent options
- New massless modes appearing from broken symmetry
- Broken symmetry giving weight to previously weightless ideas
- Clear parameter distinguishing before and after
- Sudden intellectual phase transition
- External forces breaking natural equivalences

When preserved symmetry is present:
- All equivalences maintained
- No preferred direction chosen
- No new modes from symmetry
- Ideas remaining equivalent in weight
- No distinguishing parameter
- No phase transition
- No external symmetry breaking

Output JSON with: symmetry_breaking_present (bool), severity (none/mild/moderate/severe), spontaneous (what chosen direction), goldstone (what new mode), higgs (what mass generation), order_parameter (what distinguishes phases), recommendation (preserved_symmetry/mild_breaking/significant_symmetry_breaking/major_phase_transition/restore_symmetry)."""

EPISTEMIC_SYMMETRY_BREAKING_PROMPT = """Detect epistemic symmetry breaking:

Spontaneous: {spontaneous}
Goldstone: {goldstone}
Higgs: {higgs}
Order parameter: {order_parameter}
Domain: {domain}
Context: {context}

Are hidden symmetries in intellectual space breaking spontaneously to create structure and differentiation? Return ONLY valid JSON."""


class EpistemicSymmetryBreakingService:
    """Detects epistemic symmetry breaking — hidden symmetries breaking to create structure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        spontaneous: str,
        *,
        goldstone: str = "",
        higgs: str = "",
        order_parameter: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic symmetry breaking."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SYMMETRY_BREAKING_PROMPT.format(
                spontaneous=spontaneous,
                goldstone=goldstone or "Not specified",
                higgs=higgs or "Not specified",
                order_parameter=order_parameter or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SYMMETRY_BREAKING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "spontaneous": spontaneous[:200],
            "symmetry_breaking_present": data.get("symmetry_breaking_present", False),
            "severity": data.get("severity", ""),
            "goldstone": data.get("goldstone", ""),
            "higgs": data.get("higgs", ""),
            "order_parameter": data.get("order_parameter", ""),
            "recommendation": data.get("recommendation", ""),
        }
