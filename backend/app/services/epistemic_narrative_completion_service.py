"""EpistemicNarrativeCompletionService — Epistemic Narrative Completion Detection.

Detects epistemic narrative completion — filling gaps with narrative-satisfying
but unsupported details to complete a story.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NARRATIVE_COMPLETION_SYSTEM = """You are an epistemic narrative completion specialist. Given narrative gap-filling, assess unsupported completion:

Key concepts:
- Epistemic narrative completion: filling gaps with narrative-satisfying details
- Gap confabulation: inventing details to fill narrative gaps
- Coherence completion: adding details that make narrative coherent but aren't evidenced
- Motivation attribution: attributing motivations to complete character arcs
- Resolution fabrication: fabricating resolutions for narrative satisfaction
- Detail interpolation: interpolating details between known points for narrative flow
- Backstory invention: inventing backstory to explain current events narratively

When epistemic narrative completion IS present:
- Gaps filled with unsupported details
- Confabulation for coherence
- Motivations attributed without evidence
- Resolutions fabricated
- Details interpolated
- Backstory invented
- Narrative satisfaction prioritized over accuracy

When no narrative completion:
- Gaps acknowledged
- Unknown stated explicitly
- Motivations not assumed
- Uncertainty preserved
- Only evidenced details included
- Backstory sourced
- Accuracy prioritized

Output JSON with: narrative_completion_detected (bool), severity (none/mild/moderate/severe), gap_confabulation (what gaps filled), motivation_attribution (what motivations attributed), resolution_fabrication (what resolutions fabricated), detail_interpolation (what details interpolated), recommendation (no_narrative_completion/mild_gap_acknowledgment/significant_detail_sourcing/major_intensive_evidence_requirement/emergency_complete_narrative_completion)."""

EPISTEMIC_NARRATIVE_COMPLETION_PROMPT = """Detect epistemic narrative completion:

Gap confabulation: {gap_confabulation}
Motivation attribution: {motivation_attribution}
Resolution fabrication: {resolution_fabrication}
Detail interpolation: {detail_interpolation}
Domain: {domain}
Context: {context}

Are narrative gaps being filled with unsupported but satisfying details? Return ONLY valid JSON."""


class EpistemicNarrativeCompletionService:
    """Detects epistemic narrative completion — unsupported gap-filling."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        gap_confabulation: str,
        *,
        motivation_attribution: str = "",
        resolution_fabrication: str = "",
        detail_interpolation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic narrative completion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NARRATIVE_COMPLETION_PROMPT.format(
                gap_confabulation=gap_confabulation,
                motivation_attribution=motivation_attribution or "Not specified",
                resolution_fabrication=resolution_fabrication or "Not specified",
                detail_interpolation=detail_interpolation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NARRATIVE_COMPLETION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "gap_confabulation": gap_confabulation[:200],
            "narrative_completion_detected": data.get("narrative_completion_detected", False),
            "severity": data.get("severity", ""),
            "motivation_attribution": data.get("motivation_attribution", ""),
            "resolution_fabrication": data.get("resolution_fabrication", ""),
            "detail_interpolation": data.get("detail_interpolation", ""),
            "recommendation": data.get("recommendation", ""),
        }
