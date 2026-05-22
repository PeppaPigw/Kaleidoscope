"""EpistemicNicheCollapseService — Epistemic Niche Collapse Detection.

Detects epistemic niche collapse — intellectual niches disappearing,
forcing ideas into inappropriate competition.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NICHE_COLLAPSE_SYSTEM = """You are an epistemic niche collapse specialist. Given an intellectual landscape, assess whether niches are disappearing and forcing inappropriate competition:

Key concepts:
- Epistemic niche collapse: intellectual niches disappearing
- Forced competition: ideas forced to compete inappropriately
- Habitat loss: loss of intellectual space for certain ideas
- Specialization death: specialized knowledge losing its home
- Generalization pressure: pressure to be general rather than specialized
- Context erasure: contexts that supported ideas disappearing
- Diversity loss: loss of intellectual diversity through niche collapse

When epistemic niche collapse IS present:
- Intellectual niches disappearing
- Ideas forced into inappropriate competition
- Intellectual space for certain ideas lost
- Specialized knowledge losing its appropriate context
- Pressure to generalize destroying specialization
- Contexts that supported ideas disappearing
- Intellectual diversity lost through niche collapse

When healthy specialization is present:
- Intellectual niches maintained and valued
- Ideas competing within appropriate contexts
- Space preserved for specialized knowledge
- Specialization valued alongside generalization
- Contexts maintained for diverse approaches
- Diversity of intellectual approaches preserved
- Niches evolving but not collapsing

Output JSON with: niche_collapse_present (bool), severity (none/mild/moderate/severe), landscape (what landscape is affected), niches_lost (what niches are disappearing), forced_competition (what inappropriate competition results), diversity_impact (how diversity is affected), recommendation (healthy_specialization/mild_pressure/significant_niche_collapse/major_diversity_loss/preserve_intellectual_niches)."""

EPISTEMIC_NICHE_COLLAPSE_PROMPT = """Detect epistemic niche collapse:

Landscape: {landscape}
Niches lost: {niches_lost}
Forced competition: {forced_competition}
Diversity impact: {diversity_impact}
Domain: {domain}
Context: {context}

Are intellectual niches disappearing, forcing inappropriate competition? Return ONLY valid JSON."""


class EpistemicNicheCollapseService:
    """Detects epistemic niche collapse — intellectual niches disappearing."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        landscape: str,
        *,
        niches_lost: str = "",
        forced_competition: str = "",
        diversity_impact: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic niche collapse."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NICHE_COLLAPSE_PROMPT.format(
                landscape=landscape,
                niches_lost=niches_lost or "Not specified",
                forced_competition=forced_competition or "Not specified",
                diversity_impact=diversity_impact or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NICHE_COLLAPSE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "landscape": landscape[:200],
            "niche_collapse_present": data.get("niche_collapse_present", False),
            "severity": data.get("severity", ""),
            "niches_lost": data.get("niches_lost", ""),
            "forced_competition": data.get("forced_competition", ""),
            "diversity_impact": data.get("diversity_impact", ""),
            "recommendation": data.get("recommendation", ""),
        }
