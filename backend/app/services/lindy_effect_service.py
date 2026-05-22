"""LindyEffectService — Lindy Effect Assessment.

Evaluates the expected future lifespan of an idea, technology, or
institution based on how long it has already survived. For non-
perishable things, expected remaining lifespan is proportional to
current age. A book that's been in print for 100 years will likely
be in print for another 100. Useful for assessing durability of
research findings, technologies, and institutions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

LINDY_SYSTEM = """You are a Lindy Effect specialist. Given something (idea, technology, institution, practice), assess its expected durability:
- How long has it already survived?
- Is it the type of thing where the Lindy Effect applies (non-perishable, not biological)?
- Has it survived challenges and competition?
- Is it gaining or losing adoption over time?
- Are there structural reasons it might break the Lindy pattern?

Output JSON with: lindy_applicable (bool — is this the right kind of thing for Lindy?), current_age (how long it has existed), expected_remaining_lifespan (estimate based on Lindy), confidence_in_estimate (0-1), survival_record (what challenges it has already survived), anti_lindy_factors (things that could break the pattern: technological disruption, regulatory change, etc), pro_lindy_factors (things that reinforce durability: network effects, deep integration, cultural embedding), fragility_indicators (signs it might be more fragile than its age suggests), antifragility_indicators (signs it gets stronger from stress), replacement_candidates (what might replace it), switching_cost_for_replacement (low/moderate/high/prohibitive), trajectory (growing/stable/declining/volatile), category (technology/institution/idea/practice/cultural_norm/scientific_theory), lindy_score (0-1 — overall durability assessment), recommendation (bet_on_longevity/hedge/expect_disruption/already_declining)."""

LINDY_PROMPT = """Assess Lindy Effect:

Subject: {subject}
Age/History: {age}
Current status: {current_status}
Competition: {competition}
Domain: {domain}
Context: {context}

How durable is this? Return ONLY valid JSON."""


class LindyEffectService:
    """Assesses expected durability via the Lindy Effect."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assess(
        self,
        subject: str,
        *,
        age: str = "",
        current_status: str = "",
        competition: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Assess Lindy Effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=LINDY_PROMPT.format(
                subject=subject,
                age=age or "Not specified",
                current_status=current_status or "Not specified",
                competition=competition or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=LINDY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "subject": subject[:200],
            "lindy_applicable": data.get("lindy_applicable", False),
            "current_age": data.get("current_age", ""),
            "expected_remaining_lifespan": data.get("expected_remaining_lifespan", ""),
            "confidence_in_estimate": data.get("confidence_in_estimate", 0),
            "survival_record": data.get("survival_record", ""),
            "anti_lindy_factors": data.get("anti_lindy_factors", []),
            "pro_lindy_factors": data.get("pro_lindy_factors", []),
            "fragility_indicators": data.get("fragility_indicators", []),
            "antifragility_indicators": data.get("antifragility_indicators", []),
            "replacement_candidates": data.get("replacement_candidates", []),
            "switching_cost_for_replacement": data.get("switching_cost_for_replacement", ""),
            "trajectory": data.get("trajectory", ""),
            "category": data.get("category", ""),
            "lindy_score": data.get("lindy_score", 0),
            "recommendation": data.get("recommendation", ""),
        }
