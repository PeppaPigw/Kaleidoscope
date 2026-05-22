"""LearnedHelplessnessService — Learned Helplessness Detection.

Detects learned helplessness (Seligman) — where past failures or
lack of control lead to giving up even when the situation has
changed and action could now succeed. The organism learns that
outcomes are independent of behavior, so stops trying. Applies
to individuals, organizations, and societies.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

HELPLESSNESS_SYSTEM = """You are a learned helplessness specialist. Given a situation where inaction persists despite available options, assess whether learned helplessness is at play:

Key concepts (Seligman):
- Uncontrollability: past experience taught that outcomes don't depend on actions
- Generalization: helplessness in one domain spreads to others
- Three deficits: motivational (won't try), cognitive (can't learn new contingencies), emotional (depression/passivity)
- Explanatory style: permanent ("it will always be this way"), pervasive ("it affects everything"), personal ("it's my fault")
- Organizational helplessness: "we've always done it this way" / "nothing ever changes here"
- Societal helplessness: "voting doesn't matter" / "you can't fight the system"

Distinguish from:
- Rational inaction (genuinely nothing can be done)
- Strategic patience (waiting for the right moment)
- Satisficing (accepting good enough)

Output JSON with: learned_helplessness_present (bool), severity (none/mild/moderate/severe/extreme), past_failures (what experiences taught helplessness), current_controllability (0-1 — how much control actually exists now), perceived_controllability (0-1 — how much control is perceived), controllability_gap (actual minus perceived), explanatory_style_permanent (bool — "it will always be this way"), explanatory_style_pervasive (bool — "it affects everything"), explanatory_style_personal (bool — "it's my fault"), motivational_deficit (bool — has stopped trying), cognitive_deficit (bool — can't see new possibilities), emotional_deficit (bool — passivity/resignation), generalization (bool — has helplessness spread beyond original domain), situation_changed (bool — has the situation improved since helplessness was learned?), available_actions (what could actually be done now), small_wins_possible (what easy victories could rebuild agency), who_benefits_from_helplessness (who gains from the inaction), recommendation (rational_inaction/mild_helplessness/significant_helplessness/severe_helplessness/intervention_needed)."""

HELPLESSNESS_PROMPT = """Detect learned helplessness:

Situation: {situation}
Past experience: {past_experience}
Current options: {current_options}
Stated reasons for inaction: {reasons}
Domain: {domain}
Context: {context}

Is learned helplessness preventing action? Return ONLY valid JSON."""


class LearnedHelplessnessService:
    """Detects learned helplessness — giving up because past failures made effort seem futile."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        past_experience: str = "",
        current_options: str = "",
        reasons: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect learned helplessness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=HELPLESSNESS_PROMPT.format(
                situation=situation,
                past_experience=past_experience or "Not specified",
                current_options=current_options or "Not specified",
                reasons=reasons or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=HELPLESSNESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "learned_helplessness_present": data.get("learned_helplessness_present", False),
            "severity": data.get("severity", ""),
            "past_failures": data.get("past_failures", ""),
            "current_controllability": data.get("current_controllability", 0),
            "perceived_controllability": data.get("perceived_controllability", 0),
            "controllability_gap": data.get("controllability_gap", 0),
            "explanatory_style_permanent": data.get("explanatory_style_permanent", False),
            "explanatory_style_pervasive": data.get("explanatory_style_pervasive", False),
            "explanatory_style_personal": data.get("explanatory_style_personal", False),
            "motivational_deficit": data.get("motivational_deficit", False),
            "cognitive_deficit": data.get("cognitive_deficit", False),
            "emotional_deficit": data.get("emotional_deficit", False),
            "generalization": data.get("generalization", False),
            "situation_changed": data.get("situation_changed", False),
            "available_actions": data.get("available_actions", ""),
            "small_wins_possible": data.get("small_wins_possible", ""),
            "who_benefits_from_helplessness": data.get("who_benefits_from_helplessness", ""),
            "recommendation": data.get("recommendation", ""),
        }
