"""MeanWorldSyndromeService — Mean World Syndrome Detection.

Detects mean world syndrome — overestimating the prevalence of
danger, violence, or negative events due to heavy media exposure.
People who consume more news/media tend to believe the world is
more dangerous than it actually is.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MEAN_WORLD_SYSTEM = """You are a mean world syndrome specialist. Given a risk assessment or worldview claim, evaluate whether danger is being overestimated due to media exposure:

Key concepts:
- Mean world syndrome: believing the world is more dangerous than it is
- Cultivation theory: media shapes perception of reality over time
- Availability heuristic: vivid media examples distort probability estimates
- Base rate neglect: ignoring actual statistics in favor of anecdotes
- Negativity bias in media: "if it bleeds, it leads"
- Risk perception: subjective vs objective risk assessment
- Statistical literacy: understanding actual prevalence rates

When mean world syndrome IS present:
- Overestimating crime rates based on news coverage
- "The world is getting worse" when statistics show improvement
- Fear disproportionate to actual risk
- Citing dramatic examples while ignoring base rates
- Believing rare events are common because they're newsworthy
- Generalizing from media narratives to real-world prevalence
- Risk assessment driven by emotional salience, not data

When mean world syndrome is NOT present:
- Risk assessment based on actual statistics
- Media examples used illustratively, not as prevalence data
- Base rates are cited and contextualized
- Trends are assessed using longitudinal data
- The assessment acknowledges both risks and safety improvements
- Specific, local risk factors are identified (not generalized fear)
- The concern is proportionate to actual evidence

Output JSON with: mean_world_present (bool), severity (none/mild/moderate/severe), claim (what danger is perceived), actual_risk (what statistics show), media_influence (how media shapes the perception), base_rate (what the actual prevalence is), recommendation (no_mean_world/mild_risk_inflation/significant_mean_world/major_danger_overestimation/consult_statistics)."""

MEAN_WORLD_PROMPT = """Detect mean world syndrome:

Assessment: {assessment}
Perceived risk: {perceived_risk}
Actual statistics: {actual_stats}
Media exposure: {media_exposure}
Domain: {domain}
Context: {context}

Is danger being overestimated due to media exposure rather than actual data? Return ONLY valid JSON."""


class MeanWorldSyndromeService:
    """Detects mean world syndrome — overestimating danger due to media."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        assessment: str,
        *,
        perceived_risk: str = "",
        actual_stats: str = "",
        media_exposure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect mean world syndrome."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MEAN_WORLD_PROMPT.format(
                assessment=assessment,
                perceived_risk=perceived_risk or "Not specified",
                actual_stats=actual_stats or "Not specified",
                media_exposure=media_exposure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MEAN_WORLD_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "assessment": assessment[:200],
            "mean_world_present": data.get("mean_world_present", False),
            "severity": data.get("severity", ""),
            "claim": data.get("claim", ""),
            "actual_risk": data.get("actual_risk", ""),
            "media_influence": data.get("media_influence", ""),
            "recommendation": data.get("recommendation", ""),
        }
