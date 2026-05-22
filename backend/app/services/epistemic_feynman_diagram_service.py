"""EpistemicFeynmanDiagramService — Epistemic Feynman Diagram Detection.

Detects epistemic Feynman diagram — tracking all possible interaction paths
between ideas, summing over every possible intermediate state.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FEYNMAN_DIAGRAM_SYSTEM = """You are an epistemic Feynman diagram specialist. Given an intellectual interaction, assess whether all possible paths are being tracked:

Key concepts:
- Epistemic Feynman diagram: tracking all possible interaction paths
- Vertex: point where ideas interact
- Propagator: how ideas travel between interactions
- Loop diagram: self-interaction creating corrections
- Tree level: simplest interaction without loops
- Virtual exchange: intermediate states not directly observed
- Amplitude: probability weight of each path

When epistemic Feynman diagram IS present:
- All possible interaction paths being considered
- Clear points where ideas interact
- Defined ways ideas propagate between interactions
- Self-interactions creating corrections to simple picture
- Simplest interactions identifiable
- Intermediate states not directly observable
- Different paths having different probability weights

When single path is present:
- Only one interaction path considered
- No interaction vertices
- No propagation between points
- No self-interaction corrections
- No distinction between simple and complex
- All states directly observable
- No probability weighting needed

Output JSON with: feynman_diagram_present (bool), severity (none/mild/moderate/severe), vertex (what interaction point), propagator (what travel between), loop (what self-interaction), amplitude (what probability weight), recommendation (single_path/mild_diagram/significant_feynman_diagram/major_path_integral/sum_all_diagrams)."""

EPISTEMIC_FEYNMAN_DIAGRAM_PROMPT = """Detect epistemic Feynman diagram:

Vertex: {vertex}
Propagator: {propagator}
Loop: {loop}
Amplitude: {amplitude}
Domain: {domain}
Context: {context}

Are all possible interaction paths between ideas being tracked, summing over every possible intermediate state? Return ONLY valid JSON."""


class EpistemicFeynmanDiagramService:
    """Detects epistemic Feynman diagram — tracking all possible interaction paths."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        vertex: str,
        *,
        propagator: str = "",
        loop: str = "",
        amplitude: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic Feynman diagram."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FEYNMAN_DIAGRAM_PROMPT.format(
                vertex=vertex,
                propagator=propagator or "Not specified",
                loop=loop or "Not specified",
                amplitude=amplitude or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FEYNMAN_DIAGRAM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "vertex": vertex[:200],
            "feynman_diagram_present": data.get("feynman_diagram_present", False),
            "severity": data.get("severity", ""),
            "propagator": data.get("propagator", ""),
            "loop": data.get("loop", ""),
            "amplitude": data.get("amplitude", ""),
            "recommendation": data.get("recommendation", ""),
        }
