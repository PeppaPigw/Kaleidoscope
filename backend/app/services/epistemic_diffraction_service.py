"""EpistemicDiffractionService — Epistemic Diffraction Detection.

Detects epistemic diffraction — knowledge spreading and losing
coherence as it passes through narrow openings or around obstacles.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DIFFRACTION_SYSTEM = """You are an epistemic diffraction specialist. Given a knowledge transmission pattern, assess whether knowledge loses coherence at boundaries:

Key concepts:
- Epistemic diffraction: knowledge spreading and losing coherence at boundaries
- Coherence loss: focused knowledge becoming diffuse
- Boundary spreading: knowledge spreading as it passes through constraints
- Pattern interference: different knowledge waves interfering
- Resolution loss: losing fine detail after diffraction
- Aperture effect: narrow channels causing more spreading
- Fringe effects: unexpected patterns at edges

When epistemic diffraction IS present:
- Knowledge spreading and losing coherence at boundaries
- Focused knowledge becoming diffuse after passing through constraints
- Knowledge spreading as it passes through narrow channels
- Different knowledge streams interfering with each other
- Fine detail lost after passing through boundaries
- Narrow communication channels causing more spreading
- Unexpected patterns appearing at edges

When coherent transmission is present:
- Knowledge maintaining coherence through boundaries
- Focused knowledge remaining focused
- Knowledge not spreading through constraints
- No interference between knowledge streams
- Fine detail preserved after transmission
- Communication channels not causing spreading
- No unexpected edge patterns

Output JSON with: diffraction_present (bool), severity (none/mild/moderate/severe), knowledge (what knowledge diffracts), boundary (what boundary causes it), spreading (how knowledge spreads), coherence_loss (what coherence is lost), recommendation (coherent_transmission/mild_spreading/significant_diffraction/major_coherence_loss/widen_channels)."""

EPISTEMIC_DIFFRACTION_PROMPT = """Detect epistemic diffraction:

Knowledge: {knowledge}
Boundary: {boundary}
Spreading: {spreading}
Coherence loss: {coherence_loss}
Domain: {domain}
Context: {context}

Is knowledge spreading and losing coherence as it passes through boundaries? Return ONLY valid JSON."""


class EpistemicDiffractionService:
    """Detects epistemic diffraction — knowledge losing coherence at boundaries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge: str,
        *,
        boundary: str = "",
        spreading: str = "",
        coherence_loss: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic diffraction."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DIFFRACTION_PROMPT.format(
                knowledge=knowledge,
                boundary=boundary or "Not specified",
                spreading=spreading or "Not specified",
                coherence_loss=coherence_loss or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DIFFRACTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge": knowledge[:200],
            "diffraction_present": data.get("diffraction_present", False),
            "severity": data.get("severity", ""),
            "boundary": data.get("boundary", ""),
            "spreading": data.get("spreading", ""),
            "coherence_loss": data.get("coherence_loss", ""),
            "recommendation": data.get("recommendation", ""),
        }
