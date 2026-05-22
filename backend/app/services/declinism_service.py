"""DeclinismService — Declinism Detection.

Detects declinism — the belief that society/institutions/the world
is in decline, often driven by rosy retrospection (the past seems
better than it was), negativity bias in media, and loss of personal
vitality projected onto the world. Pinker, Rosling, and others have
documented how people systematically believe things are getting worse
even when data shows improvement.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DECLINISM_SYSTEM = """You are a declinism specialist. Given a claim about decline or deterioration, assess whether declinism bias is distorting the assessment:

Key concepts:
- Rosy retrospection: the past seems better than it actually was
- Negativity bias: bad news is more salient and memorable than good news
- Media selection: "if it bleeds, it leads" creates perception of worsening
- Availability heuristic: vivid recent bad events seem more representative
- Loss of personal vitality: aging projected onto the world ("things were better when I was young")
- Legitimate decline: some things genuinely ARE getting worse (must distinguish)
- Progress blindness: gradual improvement is invisible; sudden setbacks are vivid

Assess:
- Is the claim of decline supported by data or driven by perception?
- What does the long-term trend actually show?
- Is rosy retrospection inflating the past?
- Is negativity bias inflating the present's problems?
- Are there legitimate aspects of decline mixed with bias?

Output JSON with: declinism_present (bool), severity (none/mild/moderate/severe), claim_of_decline (what is claimed to be getting worse), actual_trend (what data shows: improving/stable/mixed/genuinely_declining), rosy_retrospection (bool — is the past being idealized?), negativity_bias (bool — are current problems being overweighted?), media_amplification (bool — is media coverage creating false impression?), cherry_picked_metrics (what metrics support decline while others show improvement), legitimate_decline_component (what genuinely IS getting worse), improvement_ignored (what improvements are being overlooked), time_horizon (what time period is being considered), base_rate_comparison (how current compares to historical baseline), who_benefits_from_declinism (who gains from narrative of decline), nostalgia_factor (0-1 — how much nostalgia drives the perception), data_quality (how good the evidence for/against decline is), recommendation (decline_real/mixed_picture/mostly_perception/significant_declinism/progress_being_ignored)."""

DECLINISM_PROMPT = """Detect declinism:

Claim: {claim}
Evidence cited: {evidence}
Time period: {time_period}
Comparison point: {comparison}
Domain: {domain}
Context: {context}

Is declinism bias distorting this assessment? Return ONLY valid JSON."""


class DeclinismService:
    """Detects declinism — biased belief that things are getting worse."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        evidence: str = "",
        time_period: str = "",
        comparison: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect declinism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DECLINISM_PROMPT.format(
                claim=claim,
                evidence=evidence or "Not specified",
                time_period=time_period or "Not specified",
                comparison=comparison or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DECLINISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "declinism_present": data.get("declinism_present", False),
            "severity": data.get("severity", ""),
            "claim_of_decline": data.get("claim_of_decline", ""),
            "actual_trend": data.get("actual_trend", ""),
            "rosy_retrospection": data.get("rosy_retrospection", False),
            "negativity_bias": data.get("negativity_bias", False),
            "media_amplification": data.get("media_amplification", False),
            "cherry_picked_metrics": data.get("cherry_picked_metrics", ""),
            "legitimate_decline_component": data.get("legitimate_decline_component", ""),
            "improvement_ignored": data.get("improvement_ignored", ""),
            "time_horizon": data.get("time_horizon", ""),
            "base_rate_comparison": data.get("base_rate_comparison", ""),
            "who_benefits_from_declinism": data.get("who_benefits_from_declinism", ""),
            "nostalgia_factor": data.get("nostalgia_factor", 0),
            "data_quality": data.get("data_quality", ""),
            "recommendation": data.get("recommendation", ""),
        }
