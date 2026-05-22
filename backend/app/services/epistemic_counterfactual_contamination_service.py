"""EpistemicCounterfactualContaminationService — Epistemic Counterfactual Contamination Detection.

Detects epistemic counterfactual contamination — counterfactual thinking
contaminating factual assessment of what actually happened.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COUNTERFACTUAL_CONTAMINATION_SYSTEM = """You are an epistemic counterfactual contamination specialist. Given counterfactuals contaminating factual assessment, assess contamination:

Key concepts:
- Epistemic counterfactual contamination: counterfactuals contaminating factual assessment
- Fact-fiction blurring: blurring what happened with what might have happened
- Outcome revision: revising what actually happened based on what should have
- Memory contamination: counterfactual scenarios contaminating actual memories
- Probability distortion: counterfactual ease distorting probability estimates
- Blame contamination: counterfactual availability affecting blame attribution
- Reality testing failure: losing track of what actually occurred

When epistemic counterfactual contamination IS present:
- Counterfactuals contaminating facts
- Fact and fiction blurred
- Outcomes revised
- Memories contaminated
- Probabilities distorted
- Blame contaminated
- Reality testing failing

When no counterfactual contamination:
- Facts and counterfactuals separated
- What happened clear
- Outcomes accurately recalled
- Memories intact
- Probabilities accurate
- Blame based on facts
- Reality testing intact

Output JSON with: counterfactual_contamination_detected (bool), severity (none/mild/moderate/severe), fact_fiction_blurring (what blurred), outcome_revision (what revised), memory_contamination (what contaminated), probability_distortion (what distorted), recommendation (no_counterfactual_contamination/mild_separation_practice/significant_reality_anchoring/major_intensive_fact_recovery/emergency_complete_counterfactual_contamination)."""

EPISTEMIC_COUNTERFACTUAL_CONTAMINATION_PROMPT = """Detect epistemic counterfactual contamination:

Fact-fiction blurring: {fact_fiction_blurring}
Outcome revision: {outcome_revision}
Memory contamination: {memory_contamination}
Probability distortion: {probability_distortion}
Domain: {domain}
Context: {context}

Are counterfactuals contaminating factual assessment? Return ONLY valid JSON."""


class EpistemicCounterfactualContaminationService:
    """Detects epistemic counterfactual contamination — what-ifs polluting facts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        fact_fiction_blurring: str,
        *,
        outcome_revision: str = "",
        memory_contamination: str = "",
        probability_distortion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic counterfactual contamination."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COUNTERFACTUAL_CONTAMINATION_PROMPT.format(
                fact_fiction_blurring=fact_fiction_blurring,
                outcome_revision=outcome_revision or "Not specified",
                memory_contamination=memory_contamination or "Not specified",
                probability_distortion=probability_distortion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COUNTERFACTUAL_CONTAMINATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "fact_fiction_blurring": fact_fiction_blurring[:200],
            "counterfactual_contamination_detected": data.get("counterfactual_contamination_detected", False),
            "severity": data.get("severity", ""),
            "outcome_revision": data.get("outcome_revision", ""),
            "memory_contamination": data.get("memory_contamination", ""),
            "probability_distortion": data.get("probability_distortion", ""),
            "recommendation": data.get("recommendation", ""),
        }
