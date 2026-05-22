"""NoveltyOverImportanceService — Novelty Over Importance Detection.

Detects novelty-over-importance bias — novel information being
prioritized over important information, where newness captures
attention at the expense of significance.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

NOVELTY_OVER_IMPORTANCE_SYSTEM = """You are a novelty-over-importance specialist. Given an information prioritization, assess whether novelty is displacing importance:

Key concepts:
- Novelty over importance: new prioritized over significant
- Newness bias: recent/new given excess attention
- Importance neglect: important but familiar ignored
- Novelty seeking: pursuing new over pursuing important
- Familiarity discount: familiar information undervalued
- News cycle effect: latest displacing most significant
- Shiny object syndrome: new things capturing attention

When novelty-over-importance IS present:
- Novel information prioritized over more important
- Newness capturing attention at expense of significance
- Important but familiar information neglected
- Pursuit of new displacing pursuit of important
- Familiar information discounted despite importance
- Latest information displacing most significant
- Attention captured by novelty not importance

When novelty focus is appropriate:
- Novel information genuinely more important
- Newness reflects genuine change in situation
- Familiar information already well-integrated
- Novel information fills genuine knowledge gap
- Attention to new proportionate to significance
- Novelty and importance aligned
- New information genuinely updates understanding

Output JSON with: novelty_bias_present (bool), severity (none/mild/moderate/severe), prioritization (what is prioritized), novel_info (what novel info dominates), important_info (what important info is neglected), displacement (how importance is displaced), recommendation (appropriate_novelty_attention/mild_newness_preference/significant_novelty_over_importance/major_importance_neglect/prioritize_by_importance_not_novelty)."""

NOVELTY_OVER_IMPORTANCE_PROMPT = """Detect novelty over importance:

Prioritization: {prioritization}
Novel information: {novel}
Important information: {important}
Attention allocation: {allocation}
Domain: {domain}
Context: {context}

Is novel information being prioritized over more important information? Return ONLY valid JSON."""


class NoveltyOverImportanceService:
    """Detects novelty-over-importance — newness displacing significance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        prioritization: str,
        *,
        novel: str = "",
        important: str = "",
        allocation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect novelty over importance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=NOVELTY_OVER_IMPORTANCE_PROMPT.format(
                prioritization=prioritization,
                novel=novel or "Not specified",
                important=important or "Not specified",
                allocation=allocation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=NOVELTY_OVER_IMPORTANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "prioritization": prioritization[:200],
            "novelty_bias_present": data.get("novelty_bias_present", False),
            "severity": data.get("severity", ""),
            "novel_info": data.get("novel_info", ""),
            "important_info": data.get("important_info", ""),
            "displacement": data.get("displacement", ""),
            "recommendation": data.get("recommendation", ""),
        }
