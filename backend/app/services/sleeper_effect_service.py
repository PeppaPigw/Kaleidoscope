"""SleeperEffectService — Sleeper Effect Detection.

Detects sleeper effect — a message from a discredited source gaining
persuasive power over time as the source is forgotten but the message
is remembered. Hovland & Weiss (1951). The discounting cue dissociates
from the message over time.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SLEEPER_EFFECT_SYSTEM = """You are a sleeper effect specialist. Given a belief or attitude change, assess whether the sleeper effect is operating — a discredited message gaining influence over time:

Key concepts (Hovland & Weiss, 1951):
- Sleeper effect: persuasion increases over time after discredited source
- Discounting cue: information that initially reduces message impact
- Dissociation: source and message become separated in memory
- Delayed persuasion: message becomes more persuasive as source is forgotten
- Source amnesia: forgetting where information came from
- Persistence of content: message content outlasts source memory
- Differential decay: source memory fades faster than message memory

When sleeper effect IS present:
- A belief is held whose original source would be rejected if remembered
- The person can't recall where they learned something they believe
- A previously discredited claim has gained credibility over time
- Source information has been forgotten while content persists
- The person would reject the belief if reminded of its source
- Attitudes have shifted toward a position from a discredited source
- Time has separated the message from its discounting cue

When belief IS independently supported:
- The belief is supported by credible, remembered sources
- The person can trace their belief to reliable evidence
- The belief would survive knowing its original source
- Multiple independent sources support the same conclusion
- The belief was formed through deliberate evaluation
- Source credibility was assessed and found adequate
- The belief is maintained by ongoing evidence, not just memory

Output JSON with: sleeper_effect_present (bool), severity (none/mild/moderate/severe), belief (what belief is held), original_source (what was the original source), source_credibility (how credible is the source), dissociation (has source been forgotten), time_factor (how has time affected the belief), recommendation (belief_well_sourced/mild_source_amnesia/significant_sleeper_effect/major_discredited_source_influence/trace_belief_to_source)."""

SLEEPER_EFFECT_PROMPT = """Detect sleeper effect:

Belief: {belief}
Source: {source}
Time elapsed: {time_elapsed}
Source memory: {source_memory}
Domain: {domain}
Context: {context}

Is this belief gaining influence because its discredited source has been forgotten? Return ONLY valid JSON."""


class SleeperEffectService:
    """Detects sleeper effect — discredited messages gaining influence over time."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        belief: str,
        *,
        source: str = "",
        time_elapsed: str = "",
        source_memory: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect sleeper effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SLEEPER_EFFECT_PROMPT.format(
                belief=belief,
                source=source or "Not specified",
                time_elapsed=time_elapsed or "Not specified",
                source_memory=source_memory or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SLEEPER_EFFECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "belief": belief[:200],
            "sleeper_effect_present": data.get("sleeper_effect_present", False),
            "severity": data.get("severity", ""),
            "original_source": data.get("original_source", ""),
            "source_credibility": data.get("source_credibility", ""),
            "dissociation": data.get("dissociation", ""),
            "recommendation": data.get("recommendation", ""),
        }
