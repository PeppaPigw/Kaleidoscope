"""BandwagonEffectService — Bandwagon Effect Detection.

Detects the bandwagon effect — where adoption/belief increases
because others have adopted/believed, independent of underlying
merit. "Everyone is doing it" becomes the reason to do it.
Drives bubbles, fads, viral misinformation, and herd behavior.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

BANDWAGON_SYSTEM = """You are a bandwagon effect specialist. Given a trend or adoption pattern, assess whether the bandwagon effect is driving behavior:

Key concepts:
- Social proof: using others' behavior as evidence of correctness
- Information cascade: rational to follow the crowd when you have little private info
- Network effects (real): value genuinely increases with adoption (phones, platforms)
- Bandwagon (false): perceived value increases with adoption but actual value doesn't
- Herd behavior: following the crowd even against private information
- FOMO: fear of missing out drives adoption independent of merit

Distinguish between:
- Legitimate network effects (more users = genuinely more value)
- Informational cascades (rational inference from others' choices)
- Pure bandwagon (popularity itself is the only reason)

Output JSON with: bandwagon_present (bool), severity (none/mild/moderate/severe/extreme), adoption_driver (merit/network_effect/social_proof/fomo/herd/information_cascade), independent_merit (0-1 — how much value exists independent of popularity), popularity_contribution (0-1 — how much of adoption is driven by popularity itself), information_cascade (bool — are people following without private info?), network_effect_genuine (bool — does value genuinely increase with users?), early_vs_late (early_adoption/growth_phase/peak/late_majority/laggards), bubble_risk (0-1 — risk this is a popularity bubble), contrarian_signal (what a contrarian would notice), what_happens_if_trend_reverses (consequences if popularity drops), who_benefits_from_bandwagon (who gains from herd behavior), independent_evaluation (what merit-based assessment would conclude), social_pressure_mechanisms (how conformity is enforced), recommendation (genuine_trend/mostly_merit/bandwagon_component/primarily_bandwagon/bubble_warning)."""

BANDWAGON_PROMPT = """Detect bandwagon effect:

Trend/Adoption: {trend}
Adoption rate: {adoption_rate}
Independent evidence of merit: {merit_evidence}
Social dynamics: {social_dynamics}
Domain: {domain}
Context: {context}

Is the bandwagon effect driving this? Return ONLY valid JSON."""


class BandwagonEffectService:
    """Detects bandwagon effect and herd behavior."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        trend: str,
        *,
        adoption_rate: str = "",
        merit_evidence: str = "",
        social_dynamics: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect bandwagon effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BANDWAGON_PROMPT.format(
                trend=trend,
                adoption_rate=adoption_rate or "Not specified",
                merit_evidence=merit_evidence or "Not specified",
                social_dynamics=social_dynamics or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=BANDWAGON_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "trend": trend[:200],
            "bandwagon_present": data.get("bandwagon_present", False),
            "severity": data.get("severity", ""),
            "adoption_driver": data.get("adoption_driver", ""),
            "independent_merit": data.get("independent_merit", 0),
            "popularity_contribution": data.get("popularity_contribution", 0),
            "information_cascade": data.get("information_cascade", False),
            "network_effect_genuine": data.get("network_effect_genuine", False),
            "early_vs_late": data.get("early_vs_late", ""),
            "bubble_risk": data.get("bubble_risk", 0),
            "contrarian_signal": data.get("contrarian_signal", ""),
            "what_happens_if_trend_reverses": data.get("what_happens_if_trend_reverses", ""),
            "who_benefits_from_bandwagon": data.get("who_benefits_from_bandwagon", ""),
            "independent_evaluation": data.get("independent_evaluation", ""),
            "social_pressure_mechanisms": data.get("social_pressure_mechanisms", ""),
            "recommendation": data.get("recommendation", ""),
        }
