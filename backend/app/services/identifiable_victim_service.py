"""IdentifiableVictimService — Identifiable Victim Effect Detection.

Detects the identifiable victim effect — greater willingness to
help a single identified individual than a large group of
anonymous people. Small & Loewenstein (2003). "One death is a
tragedy; a million deaths is a statistic." We donate more to
save one named child than thousands of unnamed ones.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

IDENTIFIABLE_VICTIM_SYSTEM = """You are an identifiable victim effect specialist. Given a resource allocation or empathy judgment, assess whether identification is distorting proportional response:

Key concepts (Small & Loewenstein, 2003):
- Identifiable victim effect: more help for one named person than many anonymous ones
- Statistical lives vs. identified lives: abstract numbers don't trigger empathy
- Singularity effect: empathy decreases as number of victims increases
- Compassion fade: emotional response doesn't scale with magnitude
- Scope insensitivity overlap: but identifiable victim is about naming, not just numbers
- Pseudoinefficacy: feeling helpless about the many reduces help for the few

When the identifiable victim effect IS present:
- Disproportionate resources for one named case vs. many unnamed ones
- Emotional response to a story but not to statistics
- "Save Baby Jessica" getting millions while thousands die unnoticed
- Policy driven by individual cases rather than aggregate impact
- Media attention on one victim while ignoring systemic issues
- Charity appeals using one face rather than presenting the scale

When individual focus IS appropriate:
- The individual case genuinely represents a unique opportunity
- Resources are genuinely only applicable to the individual case
- The individual case is a test case with systemic implications
- Helping the individual doesn't come at the cost of helping many
- The focus is strategic (building support for broader action)

Output JSON with: identifiable_victim_present (bool), severity (none/mild/moderate/severe), identified_victim (who is the named/identified case), statistical_victims (who are the unnamed many), resource_allocation (how are resources being distributed), proportionality (is response proportional to need?), emotional_vs_rational (is emotion overriding proportional thinking?), narrative_power (how compelling is the individual story?), scope_of_problem (how large is the broader issue?), opportunity_cost (what could the resources achieve if allocated proportionally?), strategic_value (bool — does individual focus serve broader goals?), media_amplification (bool — is media driving the disproportion?), recommendation (focus_appropriate/mild_identification_bias/significant_disproportion/major_identifiable_victim_effect/allocate_proportionally)."""

IDENTIFIABLE_VICTIM_PROMPT = """Detect identifiable victim effect:

Situation: {situation}
Individual case: {individual}
Broader population: {population}
Resource allocation: {allocation}
Domain: {domain}
Context: {context}

Is identification causing disproportionate response? Return ONLY valid JSON."""


class IdentifiableVictimService:
    """Detects identifiable victim effect — disproportionate response to named individuals."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        individual: str = "",
        population: str = "",
        allocation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect identifiable victim effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=IDENTIFIABLE_VICTIM_PROMPT.format(
                situation=situation,
                individual=individual or "Not specified",
                population=population or "Not specified",
                allocation=allocation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=IDENTIFIABLE_VICTIM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "identifiable_victim_present": data.get("identifiable_victim_present", False),
            "severity": data.get("severity", ""),
            "identified_victim": data.get("identified_victim", ""),
            "statistical_victims": data.get("statistical_victims", ""),
            "resource_allocation": data.get("resource_allocation", ""),
            "proportionality": data.get("proportionality", ""),
            "emotional_vs_rational": data.get("emotional_vs_rational", ""),
            "narrative_power": data.get("narrative_power", ""),
            "scope_of_problem": data.get("scope_of_problem", ""),
            "opportunity_cost": data.get("opportunity_cost", ""),
            "strategic_value": data.get("strategic_value", False),
            "media_amplification": data.get("media_amplification", False),
            "recommendation": data.get("recommendation", ""),
        }
