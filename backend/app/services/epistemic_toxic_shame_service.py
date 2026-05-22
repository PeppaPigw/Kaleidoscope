"""EpistemicToxicShameService — Epistemic Toxic Shame Detection.

Detects epistemic toxic shame — pervasive sense of intellectual defectiveness,
feeling fundamentally flawed as a thinker.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TOXIC_SHAME_SYSTEM = """You are an epistemic toxic shame specialist. Given pervasive intellectual defectiveness, assess toxic shame:

Key concepts:
- Epistemic toxic shame: feeling fundamentally flawed as thinker
- Core defectiveness: belief that intellectual self is broken
- Global attribution: I am stupid vs I made a mistake
- Identity fusion: shame IS the self, not a feeling
- Hiding compulsion: must conceal intellectual self
- Worthlessness: intellectual contributions have no value
- Contamination: shame spreads to all intellectual activity

When epistemic toxic shame IS present:
- Feeling fundamentally flawed
- Belief self is broken
- I am stupid (global)
- Shame is the self
- Must conceal self
- Contributions worthless
- Shame spreads everywhere

When no toxic shame:
- Feeling capable
- Self is intact
- Made a mistake (specific)
- Shame is a feeling
- Comfortable being seen
- Contributions valued
- Contained experiences

Output JSON with: toxic_shame_detected (bool), severity (none/mild/moderate/severe), core_defectiveness (what fundamentally flawed), global_attribution (what I am), hiding_compulsion (what concealing), worthlessness_belief (what no value), recommendation (no_toxic_shame/mild_shame_resilience/significant_shame_therapy/major_intensive_core_work/emergency_severe_toxic_shame)."""

EPISTEMIC_TOXIC_SHAME_PROMPT = """Detect epistemic toxic shame:

Core defectiveness: {core_defectiveness}
Global attribution: {global_attribution}
Hiding compulsion: {hiding_compulsion}
Worthlessness belief: {worthlessness_belief}
Domain: {domain}
Context: {context}

Is there pervasive sense of intellectual defectiveness — feeling fundamentally flawed? Return ONLY valid JSON."""


class EpistemicToxicShameService:
    """Detects epistemic toxic shame — pervasive intellectual defectiveness."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        core_defectiveness: str,
        *,
        global_attribution: str = "",
        hiding_compulsion: str = "",
        worthlessness_belief: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic toxic shame."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TOXIC_SHAME_PROMPT.format(
                core_defectiveness=core_defectiveness,
                global_attribution=global_attribution or "Not specified",
                hiding_compulsion=hiding_compulsion or "Not specified",
                worthlessness_belief=worthlessness_belief or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TOXIC_SHAME_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "core_defectiveness": core_defectiveness[:200],
            "toxic_shame_detected": data.get("toxic_shame_detected", False),
            "severity": data.get("severity", ""),
            "global_attribution": data.get("global_attribution", ""),
            "hiding_compulsion": data.get("hiding_compulsion", ""),
            "worthlessness_belief": data.get("worthlessness_belief", ""),
            "recommendation": data.get("recommendation", ""),
        }
