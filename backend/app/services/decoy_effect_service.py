"""DecoyEffectService — Decoy Effect Detection.

Detects the decoy effect (asymmetric dominance) — when adding
an inferior third option changes preference between two original
options. Huber, Payne & Puto (1982). The "decoy" is dominated
by one option but not the other, making the dominating option
look better by comparison. Common in pricing, marketing, and
choice architecture.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DECOY_SYSTEM = """You are a decoy effect specialist. Given a choice set, assess whether an asymmetrically dominated option is manipulating preference:

Key concepts (Huber, Payne & Puto, 1982):
- Decoy effect: adding an inferior option shifts preference toward the option that dominates it
- Asymmetric dominance: the decoy is worse than one option on all dimensions but not the other
- Attraction effect: the target option "attracts" choice share from the competitor
- Compromise effect: the decoy makes the target look like a reasonable middle ground
- Phantom decoy: an unavailable option that still shifts preference
- Choice architecture: deliberate structuring of options to influence decisions

When the decoy effect IS present:
- A third option exists that is clearly inferior to one option but not the other
- The "decoy" makes one option look like a better deal by comparison
- Pricing tiers where the middle option is designed to push toward the expensive one
- "Nobody would choose X, but it makes Y look good"
- The decoy was added specifically to influence choice
- Removing the decoy would change the preference between remaining options

When the third option IS genuine:
- All options serve different genuine needs
- No option is clearly dominated on all relevant dimensions
- The options were not designed to manipulate preference
- Each option has a natural audience
- The choice set reflects genuine market segmentation

Output JSON with: decoy_present (bool), severity (none/mild/moderate/severe), choice_set (what options are available), likely_decoy (which option is the decoy), target_option (which option benefits from the decoy), competitor_option (which option loses share to the decoy), dominance_dimensions (on what dimensions does the target dominate the decoy?), non_dominance_dimensions (on what dimensions is the decoy not dominated by the competitor?), manipulation_intent (bool — was the decoy deliberately added?), removal_test (would removing the decoy change preference?), price_anchoring (bool — is the decoy anchoring price perception?), compromise_framing (bool — does the decoy create a false middle ground?), recommendation (options_genuine/mild_decoy_effect/significant_manipulation/major_choice_architecture/evaluate_without_decoy)."""

DECOY_PROMPT = """Detect decoy effect:

Choice set: {choices}
Suspected decoy: {decoy}
Decision context: {decision_context}
Pricing/features: {pricing}
Domain: {domain}
Context: {context}

Is an asymmetrically dominated option manipulating preference? Return ONLY valid JSON."""


class DecoyEffectService:
    """Detects decoy effect — asymmetric dominance manipulating choice."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        choices: str,
        *,
        decoy: str = "",
        decision_context: str = "",
        pricing: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect decoy effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DECOY_PROMPT.format(
                choices=choices,
                decoy=decoy or "Not specified",
                decision_context=decision_context or "Not specified",
                pricing=pricing or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DECOY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "choices": choices[:200],
            "decoy_present": data.get("decoy_present", False),
            "severity": data.get("severity", ""),
            "likely_decoy": data.get("likely_decoy", ""),
            "target_option": data.get("target_option", ""),
            "competitor_option": data.get("competitor_option", ""),
            "dominance_dimensions": data.get("dominance_dimensions", ""),
            "non_dominance_dimensions": data.get("non_dominance_dimensions", ""),
            "manipulation_intent": data.get("manipulation_intent", False),
            "removal_test": data.get("removal_test", ""),
            "price_anchoring": data.get("price_anchoring", False),
            "compromise_framing": data.get("compromise_framing", False),
            "recommendation": data.get("recommendation", ""),
        }
