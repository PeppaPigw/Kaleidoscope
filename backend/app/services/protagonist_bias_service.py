"""ProtagonistBiasService — Protagonist Bias Detection.

Detects protagonist bias — viewing situations through a single
protagonist's perspective, missing other viewpoints, stakeholders,
and the systemic context beyond any one actor.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PROTAGONIST_BIAS_SYSTEM = """You are a protagonist bias specialist. Given a narrative or analysis, assess whether it is locked into a single protagonist's perspective:

Key concepts:
- Protagonist bias: seeing everything through one actor's eyes
- Perspective narrowing: missing other stakeholders' viewpoints
- Agency attribution: over-attributing outcomes to protagonist's actions
- Systemic blindness: missing structural factors by focusing on individual
- Antagonist flattening: reducing others to obstacles for protagonist
- Stakeholder invisibility: people affected but not centered in narrative
- Multi-perspectival analysis: considering multiple viewpoints

When protagonist bias IS present:
- Analysis centered on single actor's perspective
- Other stakeholders' interests invisible or dismissed
- Outcomes attributed primarily to protagonist's agency
- Systemic factors reduced to protagonist's challenges
- Other actors flattened into helpers or obstacles
- Success/failure defined only from protagonist's viewpoint
- Structural context missing from individual-focused narrative

When multiple perspectives are considered:
- Multiple stakeholders' viewpoints represented
- Systemic factors analyzed alongside individual agency
- Other actors given full dimensionality
- Success defined from multiple perspectives
- Structural context provided
- Power dynamics acknowledged
- Analysis not locked to single viewpoint

Output JSON with: bias_present (bool), severity (none/mild/moderate/severe), narrative (what story is told), protagonist (whose perspective dominates), missing_perspectives (whose viewpoints are absent), agency_attribution (how much is attributed to protagonist), recommendation (multi_perspectival/mild_centering/significant_protagonist_lock/major_perspective_blindness/include_other_viewpoints)."""

PROTAGONIST_BIAS_PROMPT = """Detect protagonist bias:

Narrative: {narrative}
Central actor: {protagonist}
Other stakeholders: {stakeholders}
Systemic factors: {systemic}
Domain: {domain}
Context: {context}

Is this analysis locked into a single protagonist's perspective? Return ONLY valid JSON."""


class ProtagonistBiasService:
    """Detects protagonist bias — locked into single actor's perspective."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        narrative: str,
        *,
        protagonist: str = "",
        stakeholders: str = "",
        systemic: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect protagonist bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PROTAGONIST_BIAS_PROMPT.format(
                narrative=narrative,
                protagonist=protagonist or "Not specified",
                stakeholders=stakeholders or "Not specified",
                systemic=systemic or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PROTAGONIST_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "narrative": narrative[:200],
            "bias_present": data.get("bias_present", False),
            "severity": data.get("severity", ""),
            "protagonist": data.get("protagonist", ""),
            "missing_perspectives": data.get("missing_perspectives", ""),
            "agency_attribution": data.get("agency_attribution", ""),
            "recommendation": data.get("recommendation", ""),
        }
