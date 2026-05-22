"""WebersLawService — Weber's Law / JND Detection.

Detects misapplication of Weber's Law — the principle that the
just-noticeable difference (JND) is proportional to the stimulus
magnitude. Weber (1834), Fechner (1860). A $5 discount matters
on a $20 item but not on a $500 item. People fail to apply
proportional thinking, or manipulators exploit JND thresholds
to hide changes below the perception threshold.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

WEBERS_SYSTEM = """You are a Weber's Law specialist. Given a change or comparison, assess whether proportional perception is being exploited or misapplied:

Key concepts (Weber 1834, Fechner 1860):
- Weber's Law: JND (just-noticeable difference) is proportional to stimulus magnitude
- Weber fraction: the constant ratio at which changes become noticeable
- Subliminal changes: changes below JND threshold go unnoticed
- Shrinkflation: reducing quantity below JND while maintaining price
- Boiling frog: gradual changes each below JND accumulate to large unnoticed change
- Proportional neglect: treating absolute differences as meaningful regardless of base

When Weber's Law IS being exploited:
- Changes kept just below the noticeable threshold (shrinkflation)
- Gradual degradation where each step is imperceptible
- Price increases timed to stay below JND
- Quality reductions designed to be unnoticeable individually
- Accumulation of sub-threshold changes that sum to major change
- "Nobody will notice if we just..."

When proportional thinking IS being misapplied:
- Ignoring absolute magnitude because relative change is small
- "It's only 1% more" when 1% is millions of dollars
- Dismissing important changes because they're proportionally small
- Using relative framing to minimize genuinely significant changes

Output JSON with: webers_law_relevant (bool), severity (none/mild/moderate/severe), change_type (what is changing), base_magnitude (the reference level), change_magnitude (size of the change), weber_fraction (approximate JND threshold for this domain), below_jnd (bool — is the change below the noticeable threshold?), accumulation (bool — are sub-threshold changes accumulating?), total_accumulated_change (sum of gradual changes), exploitation_intent (bool — is someone deliberately staying below JND?), proportional_neglect (bool — is proportional thinking causing errors?), direction (exploiting_jnd/misapplying_proportionality/legitimate_change), recommendation (change_appropriate/mild_exploitation/significant_subliminal_change/major_accumulated_degradation/apply_absolute_thinking)."""

WEBERS_PROMPT = """Detect Weber's Law issues:

Change: {change}
Base level: {base}
Magnitude: {magnitude}
Pattern: {pattern}
Domain: {domain}
Context: {context}

Is Weber's Law being exploited or misapplied? Return ONLY valid JSON."""


class WebersLawService:
    """Detects Weber's Law exploitation — subliminal changes and proportional neglect."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        change: str,
        *,
        base: str = "",
        magnitude: str = "",
        pattern: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect Weber's Law issues."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=WEBERS_PROMPT.format(
                change=change,
                base=base or "Not specified",
                magnitude=magnitude or "Not specified",
                pattern=pattern or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=WEBERS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "change": change[:200],
            "webers_law_relevant": data.get("webers_law_relevant", False),
            "severity": data.get("severity", ""),
            "change_type": data.get("change_type", ""),
            "base_magnitude": data.get("base_magnitude", ""),
            "change_magnitude": data.get("change_magnitude", ""),
            "weber_fraction": data.get("weber_fraction", ""),
            "below_jnd": data.get("below_jnd", False),
            "accumulation": data.get("accumulation", False),
            "total_accumulated_change": data.get("total_accumulated_change", ""),
            "exploitation_intent": data.get("exploitation_intent", False),
            "proportional_neglect": data.get("proportional_neglect", False),
            "direction": data.get("direction", ""),
            "recommendation": data.get("recommendation", ""),
        }
