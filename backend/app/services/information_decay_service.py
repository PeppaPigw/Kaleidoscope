"""InformationDecayService — Research Finding Freshness & Decay Detection.

Monitors how research findings age over time. Detects when evidence is
becoming stale, being superseded by newer work, or losing relevance due
to paradigm shifts. Essential for maintaining current knowledge bases.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DECAY_SYSTEM = """You are an information decay analyst. Given a research finding or claim, assess how it's aging. Consider:
- Citation velocity: is it still being cited, or has citation dropped off?
- Supersession: has newer work replaced or refined this finding?
- Replication status: have replication attempts succeeded or failed?
- Paradigm alignment: does it fit current theoretical frameworks?
- Methodology currency: were the methods state-of-art when published? Are they now outdated?
- Data freshness: is the underlying data still representative?

Output JSON with: decay_assessment.finding_age_category (fresh/current/aging/stale/obsolete), decay_assessment.decay_rate (slow/moderate/fast/accelerating), decay_assessment.superseded_by (list of newer findings that update/replace this), decay_assessment.still_valid_aspects (what parts remain true), decay_assessment.invalidated_aspects (what parts are no longer accepted), decay_assessment.replication_status (replicated/partially_replicated/failed/untested), decay_assessment.methodology_currency (current/dated/obsolete), decay_assessment.recommended_action (keep/update/replace/archive), decay_assessment.shelf_life_estimate (how much longer this finding will remain useful), decay_assessment.confidence (0-1)."""

DECAY_PROMPT = """Assess information decay for this finding:

Finding: {finding}
Publication year (approx): {year}
Domain: {domain}
Context: {context}

How well has this finding aged? Is it still current? Return ONLY valid JSON."""


class InformationDecayService:
    """Tracks how research findings age and decay over time."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assess_decay(
        self,
        finding: str,
        *,
        year: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Assess how a finding has aged."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DECAY_PROMPT.format(
                finding=finding,
                year=year or "unknown",
                domain=domain or "research",
                context=context or "No additional context",
            ),
            system=DECAY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        assessment = data.get("decay_assessment", data)

        return {
            "finding": finding[:200],
            "age_category": assessment.get("finding_age_category", ""),
            "decay_rate": assessment.get("decay_rate", ""),
            "superseded_by": assessment.get("superseded_by", []),
            "still_valid": assessment.get("still_valid_aspects", []),
            "invalidated": assessment.get("invalidated_aspects", []),
            "replication_status": assessment.get("replication_status", ""),
            "methodology_currency": assessment.get("methodology_currency", ""),
            "recommended_action": assessment.get("recommended_action", ""),
            "shelf_life": assessment.get("shelf_life_estimate", ""),
            "confidence": assessment.get("confidence", 0),
        }
