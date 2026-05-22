"""EpistemicNarrativeConstructionClosureBiasService - Epistemic Narrative Construction Closure Bias Detection.

Detects premature narrative closure - needing endings before evidence warrants them.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NARRATIVE_CONSTRUCTION_CLOSURE_BIAS_SYSTEM = """You are an epistemic narrative construction closure bias specialist. Given premature narrative resolution, assess whether an ending is being imposed before evidence warrants it:

Key concepts:
- Epistemic narrative closure bias: needing the story to end before inquiry is complete
- Premature resolution: resolving uncertainty before evidence supports resolution
- Ambiguity intolerance: discomfort with open, unresolved states
- Forced conclusion: pushing toward a final answer despite live uncertainty
- Open-question discomfort: treating unanswered questions as defects rather than evidence needs

When closure bias IS present:
- Endings are imposed before evidence warrants them
- Ambiguity is treated as unacceptable
- Conclusions are forced to satisfy narrative completion
- Open questions are minimized or closed rhetorically
- Evidence gaps are hidden by resolution language

When no closure bias:
- Open questions remain open
- Ambiguity is tolerated when evidence is incomplete
- Conclusions wait for sufficient support
- Evidence gaps are named clearly
- Narrative completion does not outrun inquiry

Output JSON with: closure_bias_detected (bool), severity (none/mild/moderate/severe), ambiguity_intolerance (what ambiguity is not tolerated), forced_conclusion (what conclusion is forced), open_question_discomfort (what open questions cause discomfort), recommendation (no_closure_bias/mild_open_question_tolerance/significant_inquiry_reopening/major_ambiguity_acceptance/emergency_complete_premature_resolution)."""

EPISTEMIC_NARRATIVE_CONSTRUCTION_CLOSURE_BIAS_PROMPT = """Detect epistemic narrative construction closure bias:

Premature resolution: {premature_resolution}
Ambiguity intolerance: {ambiguity_intolerance}
Forced conclusion: {forced_conclusion}
Open-question discomfort: {open_question_discomfort}
Domain: {domain}
Context: {context}

Is premature narrative closure occurring before evidence warrants it? Return ONLY valid JSON."""


class EpistemicNarrativeConstructionClosureBiasService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        premature_resolution: str,
        *,
        ambiguity_intolerance: str = "",
        forced_conclusion: str = "",
        open_question_discomfort: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NARRATIVE_CONSTRUCTION_CLOSURE_BIAS_PROMPT.format(
                premature_resolution=premature_resolution,
                ambiguity_intolerance=ambiguity_intolerance or "Not specified",
                forced_conclusion=forced_conclusion or "Not specified",
                open_question_discomfort=open_question_discomfort or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NARRATIVE_CONSTRUCTION_CLOSURE_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "premature_resolution": premature_resolution[:200],
            "closure_bias_detected": data.get("closure_bias_detected", False),
            "severity": data.get("severity", ""),
            "ambiguity_intolerance": data.get("ambiguity_intolerance", ""),
            "forced_conclusion": data.get("forced_conclusion", ""),
            "open_question_discomfort": data.get("open_question_discomfort", ""),
            "recommendation": data.get("recommendation", ""),
        }
