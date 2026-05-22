"""EpistemicNarrativeSelectionService — Epistemic Narrative Selection Detection.

Detects epistemic narrative selection — selecting facts that fit the narrative
while ignoring those that don't.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NARRATIVE_SELECTION_SYSTEM = """You are an epistemic narrative selection specialist. Given narrative-driven fact selection, assess selective inclusion:

Key concepts:
- Epistemic narrative selection: choosing facts that fit narrative, ignoring others
- Narrative-fit filtering: including only facts that support the story
- Contradicting evidence omission: omitting evidence that contradicts narrative
- Emphasis distortion: emphasizing narrative-supporting facts disproportionately
- Context stripping for narrative: removing context that complicates narrative
- Timeline manipulation: reordering events for narrative effect
- Character consistency enforcement: ignoring facts that complicate character portrayal

When epistemic narrative selection IS present:
- Facts selected for narrative fit
- Contradicting evidence omitted
- Emphasis distorted
- Context stripped for narrative
- Timeline manipulated
- Character consistency enforced over truth
- Story prioritized over completeness

When no narrative selection:
- Facts included regardless of narrative fit
- Contradicting evidence presented
- Emphasis proportional
- Context preserved
- Timeline accurate
- Character complexity maintained
- Completeness prioritized

Output JSON with: narrative_selection_detected (bool), severity (none/mild/moderate/severe), narrative_fit_filtering (what filtered for fit), evidence_omission (what evidence omitted), emphasis_distortion (what emphasis distorted), timeline_manipulation (what timeline manipulated), recommendation (no_narrative_selection/mild_completeness_check/significant_counter_evidence_inclusion/major_intensive_narrative_separation/emergency_complete_narrative_selection)."""

EPISTEMIC_NARRATIVE_SELECTION_PROMPT = """Detect epistemic narrative selection:

Narrative fit filtering: {narrative_fit_filtering}
Evidence omission: {evidence_omission}
Emphasis distortion: {emphasis_distortion}
Timeline manipulation: {timeline_manipulation}
Domain: {domain}
Context: {context}

Are facts being selected to fit a narrative while contradicting evidence is ignored? Return ONLY valid JSON."""


class EpistemicNarrativeSelectionService:
    """Detects epistemic narrative selection — narrative-driven fact filtering."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        narrative_fit_filtering: str,
        *,
        evidence_omission: str = "",
        emphasis_distortion: str = "",
        timeline_manipulation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic narrative selection."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NARRATIVE_SELECTION_PROMPT.format(
                narrative_fit_filtering=narrative_fit_filtering,
                evidence_omission=evidence_omission or "Not specified",
                emphasis_distortion=emphasis_distortion or "Not specified",
                timeline_manipulation=timeline_manipulation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NARRATIVE_SELECTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "narrative_fit_filtering": narrative_fit_filtering[:200],
            "narrative_selection_detected": data.get("narrative_selection_detected", False),
            "severity": data.get("severity", ""),
            "evidence_omission": data.get("evidence_omission", ""),
            "emphasis_distortion": data.get("emphasis_distortion", ""),
            "timeline_manipulation": data.get("timeline_manipulation", ""),
            "recommendation": data.get("recommendation", ""),
        }
