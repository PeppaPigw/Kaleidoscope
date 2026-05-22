"""EpistemicExplanationAdHocService — Epistemic Ad Hoc Explanation Detection.

Detects epistemic ad hoc explanations — explanations added only to save
a theory from refutation, without independent motivation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EXPLANATION_AD_HOC_SYSTEM = """You are an epistemic ad hoc explanation specialist. Given ad hoc explanations saving theories, assess ad hoc explanation:

Key concepts:
- Epistemic ad hoc explanation: explanation added only to save theory
- Rescue hypothesis: hypothesis added solely to rescue from refutation
- Epicycle addition: adding epicycles to save failing model
- Exception manufacturing: manufacturing exceptions when theory fails
- Post hoc rationalization: rationalizing after prediction fails
- Degenerating research program: program surviving only through ad hoc additions
- Protective belt inflation: inflating protective belt around core theory

When epistemic ad hoc explanation IS present:
- Explanations added to save theory
- Rescue hypotheses deployed
- Epicycles added
- Exceptions manufactured
- Post hoc rationalization used
- Research program degenerating
- Protective belt inflating

When no ad hoc explanation:
- Explanations independently motivated
- Hypotheses predict new facts
- Models simplified
- Exceptions genuine
- Predictions made in advance
- Research program progressive
- Core theory tested directly

Output JSON with: ad_hoc_explanation_detected (bool), severity (none/mild/moderate/severe), rescue_hypothesis (what rescue hypotheses), epicycle_addition (what epicycles added), exception_manufacturing (what exceptions manufactured), degenerating_program (what program degenerating), recommendation (no_ad_hoc_explanation/mild_motivation_checking/significant_independent_testing/major_intensive_theory_revision/emergency_complete_ad_hoc_explanation)."""

EPISTEMIC_EXPLANATION_AD_HOC_PROMPT = """Detect epistemic ad hoc explanation:

Rescue hypothesis: {rescue_hypothesis}
Epicycle addition: {epicycle_addition}
Exception manufacturing: {exception_manufacturing}
Degenerating program: {degenerating_program}
Domain: {domain}
Context: {context}

Are ad hoc explanations being added only to save a theory from refutation? Return ONLY valid JSON."""


class EpistemicExplanationAdHocService:
    """Detects epistemic ad hoc explanation — theory rescue only."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        rescue_hypothesis: str,
        *,
        epicycle_addition: str = "",
        exception_manufacturing: str = "",
        degenerating_program: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic ad hoc explanation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EXPLANATION_AD_HOC_PROMPT.format(
                rescue_hypothesis=rescue_hypothesis,
                epicycle_addition=epicycle_addition or "Not specified",
                exception_manufacturing=exception_manufacturing or "Not specified",
                degenerating_program=degenerating_program or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EXPLANATION_AD_HOC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "rescue_hypothesis": rescue_hypothesis[:200],
            "ad_hoc_explanation_detected": data.get("ad_hoc_explanation_detected", False),
            "severity": data.get("severity", ""),
            "epicycle_addition": data.get("epicycle_addition", ""),
            "exception_manufacturing": data.get("exception_manufacturing", ""),
            "degenerating_program": data.get("degenerating_program", ""),
            "recommendation": data.get("recommendation", ""),
        }
