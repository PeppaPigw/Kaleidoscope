"""EpistemicApoptosisService — Epistemic Apoptosis Detection.

Detects epistemic apoptosis — programmed death of ideas for the health
of the intellectual whole, orderly self-destruction when no longer needed.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_APOPTOSIS_SYSTEM = """You are an epistemic apoptosis specialist. Given an intellectual system, assess whether ideas undergo programmed death for system health:

Key concepts:
- Epistemic apoptosis: programmed idea death for system health
- Death signal: trigger initiating orderly destruction
- Caspase cascade: chain of destruction events
- Survival signal: what keeps ideas alive
- Phagocytosis: cleanup of dead idea remnants
- Necrosis alternative: uncontrolled chaotic death
- Developmental pruning: shaping through selective death

When epistemic apoptosis IS present:
- Ideas undergoing programmed orderly destruction
- Clear triggers initiating the death process
- Chain of destruction events proceeding in order
- Identifiable signals keeping other ideas alive
- Cleanup of dead idea remnants
- Orderly rather than chaotic destruction
- Intellectual shaping through selective idea death

When immortal ideas is present:
- No programmed idea death
- No death triggers
- No destruction cascade
- No survival signals needed
- No cleanup needed
- No destruction at all
- No selective pruning

Output JSON with: apoptosis_present (bool), severity (none/mild/moderate/severe), death_signal (what trigger), caspase_cascade (what destruction chain), survival_signal (what keeps alive), developmental_pruning (what selective shaping), recommendation (immortal_ideas/mild_apoptosis/significant_apoptosis/major_programmed_death/ensure_healthy_pruning)."""

EPISTEMIC_APOPTOSIS_PROMPT = """Detect epistemic apoptosis:

Death signal: {death_signal}
Caspase cascade: {caspase_cascade}
Survival signal: {survival_signal}
Developmental pruning: {developmental_pruning}
Domain: {domain}
Context: {context}

Are ideas undergoing programmed death for the health of the intellectual whole? Return ONLY valid JSON."""


class EpistemicApoptosisService:
    """Detects epistemic apoptosis — programmed idea death for system health."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        death_signal: str,
        *,
        caspase_cascade: str = "",
        survival_signal: str = "",
        developmental_pruning: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic apoptosis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_APOPTOSIS_PROMPT.format(
                death_signal=death_signal,
                caspase_cascade=caspase_cascade or "Not specified",
                survival_signal=survival_signal or "Not specified",
                developmental_pruning=developmental_pruning or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_APOPTOSIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "death_signal": death_signal[:200],
            "apoptosis_present": data.get("apoptosis_present", False),
            "severity": data.get("severity", ""),
            "caspase_cascade": data.get("caspase_cascade", ""),
            "survival_signal": data.get("survival_signal", ""),
            "developmental_pruning": data.get("developmental_pruning", ""),
            "recommendation": data.get("recommendation", ""),
        }
