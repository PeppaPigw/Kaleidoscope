"""EpistemicCategoryEssentialismService — Epistemic Category Essentialism Detection.

Detects epistemic category essentialism — assuming categories have essential
natures rather than being socially constructed or pragmatically defined.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CATEGORY_ESSENTIALISM_SYSTEM = """You are an epistemic category essentialism specialist. Given essentialist thinking about categories, assess category essentialism:

Key concepts:
- Epistemic category essentialism: assuming categories have essential natures
- Natural kind assumption: assuming categories are natural kinds
- Hidden essence belief: believing in hidden essences defining categories
- Immutability assumption: assuming category membership is immutable
- Homogeneity assumption: assuming category members are homogeneous
- Sharp boundary from essence: deriving sharp boundaries from assumed essences
- Definitional rigidity: rigid definitions from essentialist thinking

When epistemic category essentialism IS present:
- Essential natures assumed
- Natural kinds assumed
- Hidden essences believed
- Membership assumed immutable
- Members assumed homogeneous
- Sharp boundaries from essences
- Definitions rigid

When no category essentialism:
- Categories recognized as constructed
- Natural kind status questioned
- Essences not assumed
- Membership recognized as contextual
- Heterogeneity acknowledged
- Boundaries recognized as pragmatic
- Definitions flexible

Output JSON with: category_essentialism_detected (bool), severity (none/mild/moderate/severe), natural_kind_assumption (what natural kinds assumed), hidden_essence (what hidden essences), immutability_assumption (what immutability assumed), homogeneity_assumption (what homogeneity assumed), recommendation (no_category_essentialism/mild_constructionism_awareness/significant_essence_questioning/major_intensive_category_deconstruction/emergency_complete_category_essentialism)."""

EPISTEMIC_CATEGORY_ESSENTIALISM_PROMPT = """Detect epistemic category essentialism:

Natural kind assumption: {natural_kind_assumption}
Hidden essence: {hidden_essence}
Immutability assumption: {immutability_assumption}
Homogeneity assumption: {homogeneity_assumption}
Domain: {domain}
Context: {context}

Are categories being treated as having essential natures rather than being constructed? Return ONLY valid JSON."""


class EpistemicCategoryEssentialismService:
    """Detects epistemic category essentialism — false essences."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        natural_kind_assumption: str,
        *,
        hidden_essence: str = "",
        immutability_assumption: str = "",
        homogeneity_assumption: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic category essentialism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CATEGORY_ESSENTIALISM_PROMPT.format(
                natural_kind_assumption=natural_kind_assumption,
                hidden_essence=hidden_essence or "Not specified",
                immutability_assumption=immutability_assumption or "Not specified",
                homogeneity_assumption=homogeneity_assumption or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CATEGORY_ESSENTIALISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "natural_kind_assumption": natural_kind_assumption[:200],
            "category_essentialism_detected": data.get("category_essentialism_detected", False),
            "severity": data.get("severity", ""),
            "hidden_essence": data.get("hidden_essence", ""),
            "immutability_assumption": data.get("immutability_assumption", ""),
            "homogeneity_assumption": data.get("homogeneity_assumption", ""),
            "recommendation": data.get("recommendation", ""),
        }
