"""EpistemicDistillationService — Epistemic Distillation Failure Detection.

Detects epistemic distillation failure — failure to separate essential
knowledge from impurities through proper intellectual processes.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DISTILLATION_SYSTEM = """You are an epistemic distillation specialist. Given a knowledge purification attempt, assess whether essential knowledge fails to separate from impurities:

Key concepts:
- Epistemic distillation failure: failure to separate essential from impure
- Separation failure: essential knowledge not separated from noise
- Impurity retention: impurities remaining in distilled product
- Boiling point confusion: not knowing what temperature separates components
- Condensation failure: purified knowledge not captured
- Fractional failure: failing to separate different knowledge fractions
- Residue: valuable knowledge left behind in residue

When distillation failure IS present:
- Essential knowledge not separated from impurities
- Noise remaining in supposedly purified knowledge
- Impurities retained in final product
- Not knowing how to separate knowledge components
- Purified knowledge not properly captured
- Different knowledge fractions not separated
- Valuable knowledge left behind as residue

When successful distillation is present:
- Essential knowledge cleanly separated
- Noise removed from purified knowledge
- No impurities in final product
- Clear separation process for components
- Purified knowledge properly captured
- Different fractions cleanly separated
- No valuable knowledge lost as residue

Output JSON with: distillation_failure (bool), severity (none/mild/moderate/severe), knowledge (what knowledge fails to distill), impurities (what impurities remain), separation (what separation fails), residue (what valuable knowledge is lost), recommendation (successful_distillation/mild_impurity/significant_distillation_failure/major_separation_failure/refine_separation_process)."""

EPISTEMIC_DISTILLATION_PROMPT = """Detect epistemic distillation failure:

Knowledge: {knowledge}
Impurities: {impurities}
Separation: {separation}
Residue: {residue}
Domain: {domain}
Context: {context}

Is essential knowledge failing to separate from impurities? Return ONLY valid JSON."""


class EpistemicDistillationService:
    """Detects epistemic distillation failure — separation of essential from impure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge: str,
        *,
        impurities: str = "",
        separation: str = "",
        residue: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic distillation failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DISTILLATION_PROMPT.format(
                knowledge=knowledge,
                impurities=impurities or "Not specified",
                separation=separation or "Not specified",
                residue=residue or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DISTILLATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge": knowledge[:200],
            "distillation_failure": data.get("distillation_failure", False),
            "severity": data.get("severity", ""),
            "impurities": data.get("impurities", ""),
            "separation": data.get("separation", ""),
            "residue": data.get("residue", ""),
            "recommendation": data.get("recommendation", ""),
        }
