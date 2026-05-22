"""EpistemicTrichotillomaniaService — Epistemic Trichotillomania Detection.

Detects epistemic trichotillomania — compulsive pulling apart of own ideas,
repetitive deconstruction of own intellectual work.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TRICHOTILLOMANIA_SYSTEM = """You are an epistemic trichotillomania specialist. Given compulsive idea-pulling, assess trichotillomania:

Key concepts:
- Epistemic trichotillomania: compulsive pulling apart own ideas
- Repetitive: same deconstruction behavior over and over
- Tension-relief: urge builds until pulling occurs
- Automatic: often unaware of pulling behavior
- Focused: deliberate pulling to relieve specific tension
- Damage: intellectual work progressively destroyed
- Shame: embarrassment about self-destructive pattern

When epistemic trichotillomania IS present:
- Compulsive pulling apart ideas
- Same behavior repeated
- Urge builds until pulling
- Often unaware of behavior
- Deliberate tension relief
- Work progressively destroyed
- Embarrassment about pattern

When no trichotillomania:
- Ideas left intact
- No repetitive deconstruction
- No urge to pull apart
- Full awareness of actions
- No tension-relief cycle
- Work preserved
- No shame about process

Output JSON with: trichotillomania_detected (bool), severity (none/mild/moderate/severe), pulling_pattern (what deconstruction), tension_cycle (what urge-relief), awareness_level (what automatic vs focused), damage_extent (what destruction), recommendation (no_trichotillomania/mild_habit_reversal/significant_cbt/major_intensive_therapy/emergency_complete_destruction)."""

EPISTEMIC_TRICHOTILLOMANIA_PROMPT = """Detect epistemic trichotillomania:

Pulling pattern: {pulling_pattern}
Tension cycle: {tension_cycle}
Awareness level: {awareness_level}
Damage extent: {damage_extent}
Domain: {domain}
Context: {context}

Is there compulsive pulling apart of own ideas and repetitive deconstruction? Return ONLY valid JSON."""


class EpistemicTrichotillomaniaService:
    """Detects epistemic trichotillomania — compulsive idea-pulling."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        pulling_pattern: str,
        *,
        tension_cycle: str = "",
        awareness_level: str = "",
        damage_extent: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic trichotillomania."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TRICHOTILLOMANIA_PROMPT.format(
                pulling_pattern=pulling_pattern,
                tension_cycle=tension_cycle or "Not specified",
                awareness_level=awareness_level or "Not specified",
                damage_extent=damage_extent or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TRICHOTILLOMANIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "pulling_pattern": pulling_pattern[:200],
            "trichotillomania_detected": data.get("trichotillomania_detected", False),
            "severity": data.get("severity", ""),
            "tension_cycle": data.get("tension_cycle", ""),
            "awareness_level": data.get("awareness_level", ""),
            "damage_extent": data.get("damage_extent", ""),
            "recommendation": data.get("recommendation", ""),
        }
