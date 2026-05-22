"""EpistemicAlloyService — Epistemic Alloy Detection.

Detects epistemic alloy contamination — impure knowledge mixtures
where incompatible elements weaken the overall conclusion.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ALLOY_SYSTEM = """You are an epistemic alloy specialist. Given a knowledge mixture, assess whether incompatible elements weaken conclusions:

Key concepts:
- Epistemic alloy: mixture of knowledge elements forming conclusions
- Contamination: incompatible elements weakening the mixture
- Impurity: foreign elements degrading knowledge quality
- Incompatibility: elements that don't combine well
- Weakness points: where impurities create vulnerability
- Composition failure: wrong proportions of elements
- Grain boundary: where different knowledge types meet poorly

When alloy contamination IS present:
- Incompatible knowledge elements mixed together
- Foreign elements degrading conclusion quality
- Impurities creating weakness in reasoning
- Elements that don't combine well forced together
- Vulnerabilities at points of impurity
- Wrong proportions of different knowledge types
- Poor boundaries between incompatible elements

When proper alloy is present:
- Compatible knowledge elements combined well
- All elements contributing to strength
- No impurities degrading quality
- Elements that combine synergistically
- No vulnerability from composition
- Proper proportions of elements
- Clean boundaries between knowledge types

Output JSON with: contamination_present (bool), severity (none/mild/moderate/severe), mixture (what elements are mixed), impurities (what impurities exist), weakness (where weakness results), composition (what composition problems), recommendation (proper_alloy/mild_impurity/significant_contamination/major_incompatibility/purify_mixture)."""

EPISTEMIC_ALLOY_PROMPT = """Detect epistemic alloy contamination:

Mixture: {mixture}
Impurities: {impurities}
Weakness: {weakness}
Composition: {composition}
Domain: {domain}
Context: {context}

Are incompatible knowledge elements mixed together, weakening conclusions? Return ONLY valid JSON."""


class EpistemicAlloyService:
    """Detects epistemic alloy contamination — impure knowledge mixtures."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        mixture: str,
        *,
        impurities: str = "",
        weakness: str = "",
        composition: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic alloy contamination."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ALLOY_PROMPT.format(
                mixture=mixture,
                impurities=impurities or "Not specified",
                weakness=weakness or "Not specified",
                composition=composition or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ALLOY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "mixture": mixture[:200],
            "contamination_present": data.get("contamination_present", False),
            "severity": data.get("severity", ""),
            "impurities": data.get("impurities", ""),
            "weakness": data.get("weakness", ""),
            "composition": data.get("composition", ""),
            "recommendation": data.get("recommendation", ""),
        }
