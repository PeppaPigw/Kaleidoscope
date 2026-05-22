"""EpistemicSlagService — Epistemic Slag Detection.

Detects epistemic slag — impurities and waste products not removed
from knowledge production, contaminating final conclusions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SLAG_SYSTEM = """You are an epistemic slag specialist. Given a knowledge production process, assess whether impurities remain in conclusions:

Key concepts:
- Epistemic slag: waste products from knowledge production left in conclusions
- Impurity retention: failing to remove impurities from reasoning
- Waste contamination: waste products contaminating conclusions
- Refining failure: failure to properly refine knowledge
- Residual bias: biases remaining as slag in conclusions
- Production waste: byproducts of reasoning not cleaned up
- Contaminated output: final conclusions containing impurities

When epistemic slag IS present:
- Impurities from reasoning process left in conclusions
- Waste products contaminating final knowledge
- Failure to refine and purify conclusions
- Residual biases remaining in output
- Byproducts of reasoning not cleaned up
- Final conclusions containing process artifacts
- Knowledge production waste mixed with output

When clean knowledge is present:
- Impurities properly removed from conclusions
- No waste products in final knowledge
- Conclusions properly refined and purified
- No residual biases in output
- Reasoning byproducts properly separated
- Clean conclusions free of process artifacts
- Knowledge production waste properly disposed

Output JSON with: slag_present (bool), severity (none/mild/moderate/severe), knowledge (what knowledge contains slag), impurities (what impurities remain), contamination (how contamination occurs), refining_failure (what refining was skipped), recommendation (clean_knowledge/mild_impurity/significant_slag/major_contamination/refine_and_purify)."""

EPISTEMIC_SLAG_PROMPT = """Detect epistemic slag:

Knowledge: {knowledge}
Impurities: {impurities}
Contamination: {contamination}
Refining failure: {refining_failure}
Domain: {domain}
Context: {context}

Are impurities and waste products from reasoning contaminating conclusions? Return ONLY valid JSON."""


class EpistemicSlagService:
    """Detects epistemic slag — impurities not removed from knowledge production."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge: str,
        *,
        impurities: str = "",
        contamination: str = "",
        refining_failure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic slag."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SLAG_PROMPT.format(
                knowledge=knowledge,
                impurities=impurities or "Not specified",
                contamination=contamination or "Not specified",
                refining_failure=refining_failure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SLAG_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge": knowledge[:200],
            "slag_present": data.get("slag_present", False),
            "severity": data.get("severity", ""),
            "impurities": data.get("impurities", ""),
            "contamination": data.get("contamination", ""),
            "refining_failure": data.get("refining_failure", ""),
            "recommendation": data.get("recommendation", ""),
        }
