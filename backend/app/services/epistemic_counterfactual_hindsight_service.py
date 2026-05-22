"""EpistemicCounterfactualHindsightService — Epistemic Counterfactual Hindsight Detection.

Detects epistemic counterfactual hindsight — using hindsight knowledge
to generate unfair counterfactuals about past decisions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COUNTERFACTUAL_HINDSIGHT_SYSTEM = """You are an epistemic counterfactual hindsight specialist. Given hindsight-based unfair counterfactuals, assess counterfactual hindsight:

Key concepts:
- Epistemic counterfactual hindsight: using hindsight to generate unfair counterfactuals
- Outcome knowledge contamination: knowing outcome makes alternatives seem obvious
- Should-have-known fallacy: assuming past self should have known what present self knows
- Foresight-hindsight confusion: confusing what was foreseeable with what is now known
- Unfair blame: blaming past decisions using information unavailable at the time
- Wisdom-of-hindsight illusion: illusion that the right choice was obvious
- Retrospective inevitability: making the actual outcome seem inevitable

When epistemic counterfactual hindsight IS present:
- Hindsight generating unfair counterfactuals
- Outcome knowledge contaminating
- Should-have-known applied unfairly
- Foresight confused with hindsight
- Blame unfair given information available
- Right choice seems falsely obvious
- Outcome seems falsely inevitable

When no counterfactual hindsight:
- Counterfactuals fair given information available
- Outcome knowledge bracketed
- Past decisions judged by past information
- Foresight and hindsight distinguished
- Blame proportionate to information
- Difficulty of choice acknowledged
- Contingency preserved

Output JSON with: counterfactual_hindsight_detected (bool), severity (none/mild/moderate/severe), outcome_knowledge_contamination (what contaminated), should_have_known (what unfairly expected), foresight_hindsight_confusion (what confused), unfair_blame (what blamed unfairly), recommendation (no_counterfactual_hindsight/mild_temporal_fairness/significant_information_bracketing/major_intensive_hindsight_correction/emergency_complete_counterfactual_hindsight)."""

EPISTEMIC_COUNTERFACTUAL_HINDSIGHT_PROMPT = """Detect epistemic counterfactual hindsight:

Outcome knowledge contamination: {outcome_knowledge_contamination}
Should-have-known: {should_have_known}
Foresight-hindsight confusion: {foresight_hindsight_confusion}
Unfair blame: {unfair_blame}
Domain: {domain}
Context: {context}

Is hindsight being used to generate unfair counterfactuals? Return ONLY valid JSON."""


class EpistemicCounterfactualHindsightService:
    """Detects epistemic counterfactual hindsight — unfair retrospective what-ifs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        outcome_knowledge_contamination: str,
        *,
        should_have_known: str = "",
        foresight_hindsight_confusion: str = "",
        unfair_blame: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic counterfactual hindsight."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COUNTERFACTUAL_HINDSIGHT_PROMPT.format(
                outcome_knowledge_contamination=outcome_knowledge_contamination,
                should_have_known=should_have_known or "Not specified",
                foresight_hindsight_confusion=foresight_hindsight_confusion or "Not specified",
                unfair_blame=unfair_blame or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COUNTERFACTUAL_HINDSIGHT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "outcome_knowledge_contamination": outcome_knowledge_contamination[:200],
            "counterfactual_hindsight_detected": data.get("counterfactual_hindsight_detected", False),
            "severity": data.get("severity", ""),
            "should_have_known": data.get("should_have_known", ""),
            "foresight_hindsight_confusion": data.get("foresight_hindsight_confusion", ""),
            "unfair_blame": data.get("unfair_blame", ""),
            "recommendation": data.get("recommendation", ""),
        }
