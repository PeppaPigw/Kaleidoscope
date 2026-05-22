"""EpistemicWorldviewCollapseService — Epistemic Worldview Collapse Detection.

Detects epistemic worldview collapse — grief from the disintegration
of one's entire intellectual worldview.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_WORLDVIEW_COLLAPSE_SYSTEM = """You are an epistemic worldview collapse specialist. Given worldview disintegration grief, assess worldview collapse:

Key concepts:
- Epistemic worldview collapse: grief from worldview disintegration
- Total framework failure: entire way of understanding failing
- Coherence loss: nothing making sense anymore
- Reconstruction overwhelm: too much to rebuild
- Existential vertigo: groundlessness from total collapse
- Trust destruction: unable to trust any framework now
- Meaning annihilation: all meaning structures destroyed

When epistemic worldview collapse IS present:
- Grief from worldview disintegration
- Entire framework failing
- Nothing making sense
- Too much to rebuild
- Groundlessness from collapse
- Unable to trust frameworks
- All meaning destroyed

When no worldview collapse:
- Worldview evolving gradually
- Framework adapting
- Coherence maintained
- Manageable updates
- Grounded through change
- Trust in process
- Meaning preserved

Output JSON with: worldview_collapse_detected (bool), severity (none/mild/moderate/severe), framework_failure (what failing), coherence_loss (what not making sense), reconstruction_overwhelm (what too much to rebuild), trust_destruction (what unable to trust), recommendation (no_worldview_collapse/mild_framework_support/significant_reconstruction_help/major_intensive_collapse_processing/emergency_total_disintegration)."""

EPISTEMIC_WORLDVIEW_COLLAPSE_PROMPT = """Detect epistemic worldview collapse:

Framework failure: {framework_failure}
Coherence loss: {coherence_loss}
Reconstruction overwhelm: {reconstruction_overwhelm}
Trust destruction: {trust_destruction}
Domain: {domain}
Context: {context}

Is there grief from worldview disintegration? Return ONLY valid JSON."""


class EpistemicWorldviewCollapseService:
    """Detects epistemic worldview collapse — grief from worldview disintegration."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        framework_failure: str,
        *,
        coherence_loss: str = "",
        reconstruction_overwhelm: str = "",
        trust_destruction: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic worldview collapse."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_WORLDVIEW_COLLAPSE_PROMPT.format(
                framework_failure=framework_failure,
                coherence_loss=coherence_loss or "Not specified",
                reconstruction_overwhelm=reconstruction_overwhelm or "Not specified",
                trust_destruction=trust_destruction or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_WORLDVIEW_COLLAPSE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "framework_failure": framework_failure[:200],
            "worldview_collapse_detected": data.get("worldview_collapse_detected", False),
            "severity": data.get("severity", ""),
            "coherence_loss": data.get("coherence_loss", ""),
            "reconstruction_overwhelm": data.get("reconstruction_overwhelm", ""),
            "trust_destruction": data.get("trust_destruction", ""),
            "recommendation": data.get("recommendation", ""),
        }
