"""EpistemicCauseOfDeathService — Epistemic Cause of Death Detection.

Detects epistemic cause of death — determining the proximate cause of
intellectual failure, the final mechanism that ended function.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CAUSE_OF_DEATH_SYSTEM = """You are an epistemic cause of death specialist. Given intellectual failure, determine the proximate cause:

Key concepts:
- Epistemic cause of death: proximate cause of intellectual failure
- Immediate cause: final mechanism that ended function
- Underlying cause: disease that initiated chain
- Contributing cause: condition that hastened death
- Mechanism: physiological derangement producing death
- Proximate vs distal: near vs far in causal chain
- Certifiable cause: officially recognized reason

When epistemic cause of death IS identifiable:
- Clear proximate cause of intellectual failure
- Identifiable final mechanism
- Traceable underlying disease
- Contributing conditions present
- Specific physiological derangement
- Clear proximate-distal distinction
- Certifiable official cause

When cause unclear:
- No clear proximate cause
- Multiple possible mechanisms
- No traceable underlying disease
- No clear contributors
- No specific derangement
- Ambiguous causal chain
- Undetermined cause

Output JSON with: cause_of_death_identified (bool), severity (none/mild/moderate/severe), immediate_cause (what final mechanism), underlying_cause (what initiated chain), contributing_cause (what hastened), mechanism (what derangement), recommendation (cause_unclear/mild_identification/significant_cause_identified/major_definitive_cause/document_intellectual_cause_of_death)."""

EPISTEMIC_CAUSE_OF_DEATH_PROMPT = """Detect epistemic cause of death:

Immediate cause: {immediate_cause}
Underlying cause: {underlying_cause}
Contributing cause: {contributing_cause}
Mechanism: {mechanism}
Domain: {domain}
Context: {context}

What was the proximate cause of this intellectual failure? Return ONLY valid JSON."""


class EpistemicCauseOfDeathService:
    """Detects epistemic cause of death — proximate cause of intellectual failure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        immediate_cause: str,
        *,
        underlying_cause: str = "",
        contributing_cause: str = "",
        mechanism: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic cause of death."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CAUSE_OF_DEATH_PROMPT.format(
                immediate_cause=immediate_cause,
                underlying_cause=underlying_cause or "Not specified",
                contributing_cause=contributing_cause or "Not specified",
                mechanism=mechanism or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CAUSE_OF_DEATH_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "immediate_cause": immediate_cause[:200],
            "cause_of_death_identified": data.get("cause_of_death_identified", False),
            "severity": data.get("severity", ""),
            "underlying_cause": data.get("underlying_cause", ""),
            "contributing_cause": data.get("contributing_cause", ""),
            "mechanism": data.get("mechanism", ""),
            "recommendation": data.get("recommendation", ""),
        }
