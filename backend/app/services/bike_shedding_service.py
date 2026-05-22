"""BikeShedService — Bike-Shedding (Law of Triviality) Detection.

Detects Parkinson's Law of Triviality — disproportionate time and
attention on trivial issues while important complex issues get
rubber-stamped. People discuss what they understand (bike shed
color) and defer on what they don't (nuclear reactor design).
C. Northcote Parkinson (1957).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

BIKESHED_SYSTEM = """You are a bike-shedding (Law of Triviality) specialist. Given a discussion or decision process, assess whether trivial issues are consuming disproportionate attention:

Key concepts (C. Northcote Parkinson, 1957):
- Law of Triviality: time spent on an item is inversely proportional to its importance
- Bike shed effect: everyone has an opinion on paint color, few understand reactor design
- Competence display: people discuss what they understand to feel useful
- Complexity avoidance: deferring on hard issues because they're intimidating
- Democratic illusion: trivial discussions feel participatory while important decisions are made by few
- Attention budget: time spent on trivia is time NOT spent on what matters

When bike-shedding IS present:
- Trivial items get extended discussion while major items pass quickly
- Discussion correlates with accessibility, not importance
- People contribute opinions on easy topics and stay silent on hard ones
- The ratio of discussion time to stakes is inverted
- Important decisions are made by default (no one engages)

When detailed discussion IS appropriate:
- The "trivial" item actually has hidden complexity
- The group genuinely has expertise on the topic
- The major items were pre-decided with good reason
- Time allocation matches actual impact

Output JSON with: bike_shedding_present (bool), severity (none/mild/moderate/severe), trivial_topics (what's getting disproportionate attention), important_topics (what's being neglected or rubber-stamped), attention_ratio (description of time allocation vs importance), complexity_avoidance (bool — are people avoiding hard topics?), competence_display (bool — discussing what they understand to feel useful?), democratic_theater (bool — trivial discussion creating illusion of participation?), decision_quality_impact (how this affects outcomes), opportunity_cost (what could be accomplished with redirected attention), who_benefits (who gains from attention on trivia), important_decisions_defaulted (what major choices were made without scrutiny), facilitation_failure (bool — could a facilitator fix this?), time_boxing_needed (bool), stakes_mismatch (ratio of discussion time to actual impact), recommendation (discussion_appropriate/mild_triviality_bias/significant_bike_shedding/severe_attention_misallocation/redirect_immediately)."""

BIKESHED_PROMPT = """Detect bike-shedding:

Discussion/Process: {discussion}
Topics covered: {topics}
Time allocation: {time_allocation}
Stakes involved: {stakes}
Domain: {domain}
Context: {context}

Is bike-shedding distorting attention allocation? Return ONLY valid JSON."""


class BikeShedService:
    """Detects bike-shedding — disproportionate attention on trivial issues."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        discussion: str,
        *,
        topics: str = "",
        time_allocation: str = "",
        stakes: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect bike-shedding."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BIKESHED_PROMPT.format(
                discussion=discussion,
                topics=topics or "Not specified",
                time_allocation=time_allocation or "Not specified",
                stakes=stakes or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=BIKESHED_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "discussion": discussion[:200],
            "bike_shedding_present": data.get("bike_shedding_present", False),
            "severity": data.get("severity", ""),
            "trivial_topics": data.get("trivial_topics", ""),
            "important_topics": data.get("important_topics", ""),
            "attention_ratio": data.get("attention_ratio", ""),
            "complexity_avoidance": data.get("complexity_avoidance", False),
            "competence_display": data.get("competence_display", False),
            "democratic_theater": data.get("democratic_theater", False),
            "decision_quality_impact": data.get("decision_quality_impact", ""),
            "opportunity_cost": data.get("opportunity_cost", ""),
            "who_benefits": data.get("who_benefits", ""),
            "important_decisions_defaulted": data.get("important_decisions_defaulted", ""),
            "facilitation_failure": data.get("facilitation_failure", False),
            "time_boxing_needed": data.get("time_boxing_needed", False),
            "stakes_mismatch": data.get("stakes_mismatch", ""),
            "recommendation": data.get("recommendation", ""),
        }
