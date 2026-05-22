"""HumorEffectService — Humor Effect Detection.

Detects the humor effect — humorous information being remembered
better and thus given disproportionate weight in evaluations.
Schmidt (1994). Funny examples, witty arguments, and humorous
framings stick in memory while serious but important information
fades. Entertainment value gets confused with evidential value.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

HUMOR_EFFECT_SYSTEM = """You are a humor effect specialist. Given a judgment or evaluation situation, assess whether humor/entertainment value is distorting the weighting of information:

Key concepts (Schmidt, 1994):
- Humor effect: funny items remembered better
- Entertainment-credibility confusion: amusing = memorable = important
- Wit as persuasion: clever framing substituting for evidence
- Comedic framing: serious issues trivialized through humor
- Likability halo: funny people seem more credible
- Engagement bias: entertaining content gets more attention
- Viral spread: humorous framings spread regardless of accuracy

When the humor effect IS distorting:
- Witty arguments being more persuasive than well-reasoned ones
- Funny examples dominating memory over important but dry ones
- Humorous framing making weak arguments seem stronger
- Entertainment value being confused with informational value
- "That was a great line" substituting for "that was a great argument"
- Serious counterarguments dismissed because they're not entertaining
- Comedic dismissal of valid concerns

When humor IS appropriate:
- Humor genuinely aids comprehension of complex material
- The entertaining framing accurately represents the underlying point
- Humor is being used to engage, not to substitute for evidence
- The funny example is also the most representative example
- Levity appropriately reduces unnecessary anxiety about a topic

Output JSON with: humor_effect_present (bool), severity (none/mild/moderate/severe), situation (what is being evaluated), humorous_content (what funny content is being overweighted), serious_content (what serious content is being underweighted), entertainment_credibility (is entertainment being confused with credibility), actual_merit (relative merit regardless of humor), persuasion_mechanism (how is humor persuading), recommendation (humor_appropriate/mild_entertainment_bias/significant_humor_effect/major_wit_over_substance/evaluate_argument_not_delivery)."""

HUMOR_EFFECT_PROMPT = """Detect humor effect:

Situation: {situation}
Humorous content: {humorous}
Serious content: {serious}
Persuasion: {persuasion}
Domain: {domain}
Context: {context}

Is humor/entertainment value causing information to be weighted disproportionately? Return ONLY valid JSON."""


class HumorEffectService:
    """Detects humor effect — entertainment value distorting information weighting."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        humorous: str = "",
        serious: str = "",
        persuasion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect humor effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=HUMOR_EFFECT_PROMPT.format(
                situation=situation,
                humorous=humorous or "Not specified",
                serious=serious or "Not specified",
                persuasion=persuasion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=HUMOR_EFFECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "humor_effect_present": data.get("humor_effect_present", False),
            "severity": data.get("severity", ""),
            "humorous_content": data.get("humorous_content", ""),
            "serious_content": data.get("serious_content", ""),
            "entertainment_credibility": data.get("entertainment_credibility", ""),
            "actual_merit": data.get("actual_merit", ""),
            "persuasion_mechanism": data.get("persuasion_mechanism", ""),
            "recommendation": data.get("recommendation", ""),
        }
