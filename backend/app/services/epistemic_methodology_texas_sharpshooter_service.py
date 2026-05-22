"""EpistemicMethodologyTexasSharpshooterService - Epistemic Methodology Texas Sharpshooter Detection.

Detects Texas sharpshooter fallacy drawing targets around clusters after the fact.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_METHODOLOGY_TEXAS_SHARPSHOOTER_SYSTEM = """You are an epistemic methodology Texas sharpshooter specialist. Given post hoc pattern, assess target-drawing after the fact:

Key concepts:
- Epistemic methodology Texas sharpshooter: drawing targets around clusters after the fact
- Post hoc pattern: pattern identified after seeing the data
- Cluster illusion: random clusters treated as meaningful
- Data snooping: searching data until a pattern appears
- Narrative fitting: constructing explanation after selecting the pattern

When Texas sharpshooter fallacy IS present:
- Patterns are selected post hoc
- Clusters are treated as meaningful without prior hypothesis
- Data snooping drives the finding
- Narrative is fitted after the fact
- Randomness is underconsidered

When no Texas sharpshooter fallacy:
- Patterns follow prior hypotheses
- Clusters are tested against chance
- Exploratory analysis is labeled
- Narrative is separated from validation
- Randomness is considered

Output JSON with: texas_sharpshooter_detected (bool), severity (none/mild/moderate/severe), cluster_illusion (what cluster may be illusory), data_snooping (what data snooping appears), narrative_fitting (what narrative is fitted), recommendation (no_texas_sharpshooter/mild_chance_check/significant_validation_needed/major_holdout_testing/emergency_complete_texas_sharpshooter)."""

EPISTEMIC_METHODOLOGY_TEXAS_SHARPSHOOTER_PROMPT = """Detect epistemic methodology Texas sharpshooter fallacy:

Post hoc pattern: {post_hoc_pattern}
Cluster illusion: {cluster_illusion}
Data snooping: {data_snooping}
Narrative fitting: {narrative_fitting}
Domain: {domain}
Context: {context}

Are targets being drawn around clusters after the fact? Return ONLY valid JSON."""


class EpistemicMethodologyTexasSharpshooterService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        post_hoc_pattern: str,
        *,
        cluster_illusion: str = "",
        data_snooping: str = "",
        narrative_fitting: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_METHODOLOGY_TEXAS_SHARPSHOOTER_PROMPT.format(
                post_hoc_pattern=post_hoc_pattern,
                cluster_illusion=cluster_illusion or "Not specified",
                data_snooping=data_snooping or "Not specified",
                narrative_fitting=narrative_fitting or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_METHODOLOGY_TEXAS_SHARPSHOOTER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "post_hoc_pattern": post_hoc_pattern[:200],
            "texas_sharpshooter_detected": data.get("texas_sharpshooter_detected", False),
            "severity": data.get("severity", ""),
            "cluster_illusion": data.get("cluster_illusion", ""),
            "data_snooping": data.get("data_snooping", ""),
            "narrative_fitting": data.get("narrative_fitting", ""),
            "recommendation": data.get("recommendation", ""),
        }
