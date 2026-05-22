"""EpistemicPhaseTransitionService — Epistemic Phase Transition Detection.

Detects epistemic phase transitions — sudden qualitative shifts in
understanding without gradual change.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PHASE_TRANSITION_SYSTEM = """You are an epistemic phase transition specialist. Given a knowledge shift, assess whether a sudden qualitative change occurred without gradual transition:

Key concepts:
- Epistemic phase transition: sudden qualitative shift in understanding
- Paradigm discontinuity: abrupt break from previous understanding
- Conceptual revolution: revolutionary rather than evolutionary change
- Understanding rupture: rupture in continuity of understanding
- Framework collapse: old framework suddenly replaced
- Gestalt shift: sudden reorganization of perception
- Threshold effect: gradual pressure producing sudden change

When epistemic phase transition IS present:
- Sudden qualitative shift without gradual transition
- Abrupt break from previous understanding
- Revolutionary rather than evolutionary change
- Rupture in continuity of understanding
- Old framework suddenly replaced without transition
- Sudden reorganization of perception
- Gradual pressure producing sudden discontinuous change

When gradual development is present:
- Understanding evolving continuously
- Changes building incrementally
- Evolution rather than revolution
- Continuity maintained through change
- Frameworks adapting gradually
- Perception shifting smoothly
- Change proportionate to evidence accumulation

Output JSON with: phase_transition_present (bool), severity (none/mild/moderate/severe), shift (what shift occurred), discontinuity (what discontinuity exists), trigger (what triggered the transition), before_after (what changed), recommendation (gradual_development/mild_shift/significant_phase_transition/major_paradigm_rupture/ensure_continuity)."""

EPISTEMIC_PHASE_TRANSITION_PROMPT = """Detect epistemic phase transition:

Shift: {shift}
Discontinuity: {discontinuity}
Trigger: {trigger}
Before/After: {before_after}
Domain: {domain}
Context: {context}

Did a sudden qualitative shift occur without gradual transition? Return ONLY valid JSON."""


class EpistemicPhaseTransitionService:
    """Detects epistemic phase transitions — sudden qualitative shifts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        shift: str,
        *,
        discontinuity: str = "",
        trigger: str = "",
        before_after: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic phase transition."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PHASE_TRANSITION_PROMPT.format(
                shift=shift,
                discontinuity=discontinuity or "Not specified",
                trigger=trigger or "Not specified",
                before_after=before_after or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PHASE_TRANSITION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "shift": shift[:200],
            "phase_transition_present": data.get("phase_transition_present", False),
            "severity": data.get("severity", ""),
            "discontinuity": data.get("discontinuity", ""),
            "trigger": data.get("trigger", ""),
            "before_after": data.get("before_after", ""),
            "recommendation": data.get("recommendation", ""),
        }
