"""EleganceBiasService — Elegance Bias Detection.

Detects elegance bias — preferring elegant theories over messy
but more accurate ones.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ELEGANCE_BIAS_SYSTEM = """You are an elegance bias specialist. Given a theory preference, assess whether elegance is being preferred over accuracy:

Key concepts:
- Elegance bias: preferring elegant theories over accurate ones
- Beauty over truth: choosing beautiful explanations over true ones
- Aesthetic theory selection: selecting theories on aesthetic grounds
- Simplicity worship: worshipping simplicity at cost of accuracy
- Mathematical beauty bias: preferring mathematically beautiful theories
- Parsimony excess: excessive parsimony sacrificing accuracy
- Elegance as evidence: treating elegance as evidence of truth

When elegance bias IS present:
- Elegant theory preferred despite less accuracy
- Beauty chosen over truth in theory selection
- Aesthetic grounds driving theory choice
- Simplicity preferred at cost of accuracy
- Mathematical beauty treated as evidence
- Parsimony excessive given the evidence
- Elegance mistaken for truth

When appropriate aesthetic appreciation is present:
- Elegance appreciated but not decisive
- Beauty noted but accuracy prioritized
- Aesthetic qualities secondary to evidence
- Simplicity preferred only when equally accurate
- Mathematical beauty appreciated in context
- Parsimony balanced with accuracy
- Elegance as heuristic not proof

Output JSON with: elegance_bias_present (bool), severity (none/mild/moderate/severe), theory (what theory is preferred), elegance (what makes it elegant), accuracy_cost (what accuracy is sacrificed), alternative (what messier but more accurate alternative exists), recommendation (appropriate_appreciation/mild_preference/significant_elegance_bias/major_beauty_over_truth/prioritize_accuracy)."""

ELEGANCE_BIAS_PROMPT = """Detect elegance bias:

Theory preferred: {theory}
Elegance: {elegance}
Accuracy cost: {accuracy}
Alternative: {alternative}
Domain: {domain}
Context: {context}

Is elegance being preferred over accuracy? Return ONLY valid JSON."""


class EleganceBiasService:
    """Detects elegance bias — preferring elegant theories over accurate ones."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        theory: str,
        *,
        elegance: str = "",
        accuracy: str = "",
        alternative: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect elegance bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ELEGANCE_BIAS_PROMPT.format(
                theory=theory,
                elegance=elegance or "Not specified",
                accuracy=accuracy or "Not specified",
                alternative=alternative or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ELEGANCE_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "theory": theory[:200],
            "elegance_bias_present": data.get("elegance_bias_present", False),
            "severity": data.get("severity", ""),
            "elegance": data.get("elegance", ""),
            "accuracy_cost": data.get("accuracy_cost", ""),
            "alternative": data.get("alternative", ""),
            "recommendation": data.get("recommendation", ""),
        }
