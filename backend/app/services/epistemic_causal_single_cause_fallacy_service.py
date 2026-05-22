"""EpistemicCausalSingleCauseFallacyService - Single Cause Fallacy Detection.

Detects single cause fallacy where complex outcomes are attributed to one cause.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CAUSAL_SINGLE_CAUSE_FALLACY_SYSTEM = """You are an epistemic causal single cause fallacy specialist. Given causal attributions, assess whether complex outcomes are oversimplified to one cause:

Key concepts:
- Single cause fallacy: attributing complex outcomes to a single cause
- Causal oversimplification: ignoring multiple contributing factors
- Necessary vs sufficient confusion: treating one factor as both necessary and sufficient
- Interaction neglect: ignoring how multiple causes interact

When single cause fallacy IS present:
- Complex outcome attributed to one cause
- Multiple factors ignored
- Necessary/sufficient confused
- Interactions neglected
- Causal complexity denied

When no single cause fallacy:
- Multiple causes acknowledged
- Relative contributions estimated
- Necessary/sufficient distinguished
- Interactions considered
- Causal complexity respected

Output JSON with: single_cause_fallacy_detected (bool), severity (none/mild/moderate/severe), causal_oversimplification (what oversimplification), necessary_sufficient_confusion (what confusion), interaction_neglect (what interactions neglected), recommendation (no_single_cause_fallacy/mild_multicausal_check/significant_factor_analysis/major_causal_reconstruction/emergency_complete_single_cause_fallacy)."""

EPISTEMIC_CAUSAL_SINGLE_CAUSE_FALLACY_PROMPT = """Detect epistemic causal single cause fallacy:

Causal attribution: {causal_attribution}
Causal oversimplification: {causal_oversimplification}
Necessary sufficient confusion: {necessary_sufficient_confusion}
Interaction neglect: {interaction_neglect}
Domain: {domain}
Context: {context}

Is a complex outcome being attributed to a single cause? Return ONLY valid JSON."""


class EpistemicCausalSingleCauseFallacyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        causal_attribution: str,
        *,
        causal_oversimplification: str = "",
        necessary_sufficient_confusion: str = "",
        interaction_neglect: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CAUSAL_SINGLE_CAUSE_FALLACY_PROMPT.format(
                causal_attribution=causal_attribution,
                causal_oversimplification=causal_oversimplification or "Not specified",
                necessary_sufficient_confusion=necessary_sufficient_confusion or "Not specified",
                interaction_neglect=interaction_neglect or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CAUSAL_SINGLE_CAUSE_FALLACY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "causal_attribution": causal_attribution[:200],
            "single_cause_fallacy_detected": data.get("single_cause_fallacy_detected", False),
            "severity": data.get("severity", ""),
            "causal_oversimplification": data.get("causal_oversimplification", ""),
            "necessary_sufficient_confusion": data.get("necessary_sufficient_confusion", ""),
            "interaction_neglect": data.get("interaction_neglect", ""),
            "recommendation": data.get("recommendation", ""),
        }
