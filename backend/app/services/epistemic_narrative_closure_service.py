"""EpistemicNarrativeClosureService — Epistemic Narrative Closure Detection.

Detects epistemic narrative closure — premature narrative closure,
needing the story to end rather than tolerating open-ended inquiry.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NARRATIVE_CLOSURE_SYSTEM = """You are an epistemic narrative closure specialist. Given premature narrative closure needs, assess narrative closure bias:

Key concepts:
- Epistemic narrative closure: needing the story to end prematurely
- Premature resolution: resolving questions before evidence warrants
- Ending hunger: hunger for conclusions and endings
- Open-endedness intolerance: inability to tolerate open questions
- Forced conclusions: forcing conclusions from insufficient evidence
- Closure urgency: urgent need to close epistemic loops
- Incompleteness anxiety: anxiety about incomplete narratives

When epistemic narrative closure IS present:
- Stories closed prematurely
- Questions resolved too early
- Endings sought urgently
- Open-endedness not tolerated
- Conclusions forced
- Closure urgently needed
- Incompleteness causing anxiety

When no narrative closure bias:
- Stories left open when warranted
- Questions held in suspension
- Endings not rushed
- Open-endedness tolerated
- Conclusions drawn only when warranted
- Closure not urgently needed
- Incompleteness accepted

Output JSON with: narrative_closure_detected (bool), severity (none/mild/moderate/severe), premature_resolution (what resolved prematurely), ending_hunger (what endings sought), open_endedness_intolerance (what open-endedness not tolerated), forced_conclusions (what conclusions forced), recommendation (no_narrative_closure/mild_openness_practice/significant_suspension_tolerance/major_intensive_incompleteness_acceptance/emergency_complete_narrative_closure)."""

EPISTEMIC_NARRATIVE_CLOSURE_PROMPT = """Detect epistemic narrative closure:

Premature resolution: {premature_resolution}
Ending hunger: {ending_hunger}
Open-endedness intolerance: {open_endedness_intolerance}
Forced conclusions: {forced_conclusions}
Domain: {domain}
Context: {context}

Is there premature narrative closure — needing the story to end? Return ONLY valid JSON."""


class EpistemicNarrativeClosureService:
    """Detects epistemic narrative closure — premature story endings."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        premature_resolution: str,
        *,
        ending_hunger: str = "",
        open_endedness_intolerance: str = "",
        forced_conclusions: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic narrative closure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NARRATIVE_CLOSURE_PROMPT.format(
                premature_resolution=premature_resolution,
                ending_hunger=ending_hunger or "Not specified",
                open_endedness_intolerance=open_endedness_intolerance or "Not specified",
                forced_conclusions=forced_conclusions or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NARRATIVE_CLOSURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "premature_resolution": premature_resolution[:200],
            "narrative_closure_detected": data.get("narrative_closure_detected", False),
            "severity": data.get("severity", ""),
            "ending_hunger": data.get("ending_hunger", ""),
            "open_endedness_intolerance": data.get("open_endedness_intolerance", ""),
            "forced_conclusions": data.get("forced_conclusions", ""),
            "recommendation": data.get("recommendation", ""),
        }
