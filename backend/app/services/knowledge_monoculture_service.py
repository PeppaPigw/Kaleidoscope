"""KnowledgeMonocultureService — Knowledge Monoculture Detection.

Detects knowledge monoculture — monoculture in knowledge production
reducing epistemic resilience, where homogeneity in methods,
perspectives, or sources creates fragility.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

KNOWLEDGE_MONOCULTURE_SYSTEM = """You are a knowledge monoculture specialist. Given a knowledge production context, assess whether monoculture is reducing epistemic resilience:

Key concepts:
- Knowledge monoculture: homogeneity reducing resilience
- Methodological monoculture: single method dominating
- Perspective monoculture: single perspective dominating
- Source monoculture: single source type dominating
- Fragility through homogeneity: same approach everywhere
- Diversity loss: epistemic diversity declining
- Resilience reduction: ability to detect errors declining

When knowledge monoculture IS present:
- Single method dominating knowledge production
- Single perspective crowding out alternatives
- Source diversity declining
- Homogeneity creating blind spots
- Epistemic diversity declining
- Resilience to error reduced by sameness
- Alternative approaches marginalized

When appropriate standardization is present:
- Standardization serving quality not homogeneity
- Methods chosen for fitness not conformity
- Perspectives diverse within productive bounds
- Source diversity maintained alongside standards
- Homogeneity in quality not in approach
- Diversity valued alongside rigor
- Alternatives available even if not dominant

Output JSON with: monoculture_present (bool), severity (none/mild/moderate/severe), production (what knowledge production context), homogeneity (what is homogeneous), diversity_lost (what diversity is lost), fragility (what fragility results), recommendation (appropriate_standardization/mild_homogeneity/significant_knowledge_monoculture/major_epistemic_fragility/cultivate_epistemic_diversity)."""

KNOWLEDGE_MONOCULTURE_PROMPT = """Detect knowledge monoculture:

Knowledge production: {production}
Methods used: {methods}
Perspectives included: {perspectives}
Alternatives available: {alternatives}
Domain: {domain}
Context: {context}

Is monoculture in knowledge production reducing epistemic resilience? Return ONLY valid JSON."""


class KnowledgeMonocultureService:
    """Detects knowledge monoculture — homogeneity reducing epistemic resilience."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        production: str,
        *,
        methods: str = "",
        perspectives: str = "",
        alternatives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect knowledge monoculture."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=KNOWLEDGE_MONOCULTURE_PROMPT.format(
                production=production,
                methods=methods or "Not specified",
                perspectives=perspectives or "Not specified",
                alternatives=alternatives or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=KNOWLEDGE_MONOCULTURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "production": production[:200],
            "monoculture_present": data.get("monoculture_present", False),
            "severity": data.get("severity", ""),
            "homogeneity": data.get("homogeneity", ""),
            "diversity_lost": data.get("diversity_lost", ""),
            "fragility": data.get("fragility", ""),
            "recommendation": data.get("recommendation", ""),
        }
