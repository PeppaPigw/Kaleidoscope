"""ResearchGapService — Systematic Research Gap Identification.

Identifies under-researched areas, missing connections, and unexplored
questions within a domain. Maps what's known against what should be known,
revealing high-value research opportunities.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

GAPS_SYSTEM = """You are a research gap analyst. Given a domain or topic, systematically identify under-researched areas by analyzing:
- What questions remain unanswered?
- What connections between known findings haven't been explored?
- What methodologies haven't been applied to this domain?
- What populations/contexts/conditions are understudied?
- What assumptions remain untested?

Output JSON with: gaps (list of: area, description, importance (0-1), tractability (0-1), novelty_potential (0-1), suggested_approach, blocking_factors), domain_maturity (nascent/growing/mature/saturated), coverage_map (well_studied list, partially_studied list, understudied list), highest_value_gap (which gap and why), meta_observation (pattern across the gaps)."""

GAPS_PROMPT = """Identify research gaps in this domain:

Domain/Topic: {topic}
Specific focus: {focus}

Known findings in this area:
{known_text}

What are the most important under-researched areas? Return ONLY valid JSON."""

OPPORTUNITY_SYSTEM = """You are a research opportunity evaluator. Given a specific research gap, assess its value as a research opportunity considering:
- Scientific importance: how much would filling this gap advance understanding?
- Practical impact: what real-world problems would this solve?
- Feasibility: can this be studied with current methods and resources?
- Timing: is this the right moment (new tools, new data, shifting interest)?
- Competition: how many others are likely pursuing this?

Output JSON with: opportunity.scientific_value (0-1), opportunity.practical_impact (0-1), opportunity.feasibility (0-1), opportunity.timing_score (0-1), opportunity.competition_level (low/medium/high), opportunity.overall_score (0-1), opportunity.ideal_approach, opportunity.required_resources, opportunity.timeline_estimate, opportunity.risk_factors (list), opportunity.synergies (what other research this enables)."""

OPPORTUNITY_PROMPT = """Evaluate this research gap as an opportunity:

Gap: {gap}
Domain: {domain}
Context: {context}

How valuable is this as a research opportunity? Return ONLY valid JSON."""


class ResearchGapService:
    """Identifies under-researched areas and evaluates research opportunities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_gaps(
        self,
        topic: str,
        *,
        focus: str = "",
        domain: str = "",
    ) -> dict:
        """Identify research gaps in a domain."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        known = await self._gather_known(topic)
        known_text = "\n".join(f"- {k}" for k in known[:8]) or "Limited prior knowledge available"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=GAPS_PROMPT.format(
                topic=topic,
                focus=focus or "general",
                known_text=known_text,
            ),
            system=GAPS_SYSTEM,
            max_tokens=4096,
            temperature=0.5,
        )
        data = parse_llm_json(raw)

        gaps = data.get("gaps", [])
        return {
            "topic": topic,
            "gaps_found": len(gaps),
            "gaps": gaps,
            "domain_maturity": data.get("domain_maturity", ""),
            "coverage_map": data.get("coverage_map", {}),
            "highest_value_gap": data.get("highest_value_gap", ""),
            "meta_observation": data.get("meta_observation", ""),
        }

    async def evaluate_opportunity(
        self,
        gap: str,
        *,
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Evaluate a specific research gap as an opportunity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=OPPORTUNITY_PROMPT.format(
                gap=gap,
                domain=domain or "research",
                context=context or "No additional context",
            ),
            system=OPPORTUNITY_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)
        opp = data.get("opportunity", data)

        return {
            "gap": gap,
            "scientific_value": opp.get("scientific_value", 0),
            "practical_impact": opp.get("practical_impact", 0),
            "feasibility": opp.get("feasibility", 0),
            "timing_score": opp.get("timing_score", 0),
            "competition": opp.get("competition_level", ""),
            "overall_score": opp.get("overall_score", 0),
            "ideal_approach": opp.get("ideal_approach", ""),
            "required_resources": opp.get("required_resources", ""),
            "timeline": opp.get("timeline_estimate", ""),
            "risk_factors": opp.get("risk_factors", []),
            "synergies": opp.get("synergies", ""),
        }

    async def _gather_known(self, topic: str) -> list[str]:
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=topic[:100], top_k=6)
            return [r.get("payload", {}).get("text", "")[:120] for r in results if r.get("payload", {}).get("text")]
        except Exception:
            return []
