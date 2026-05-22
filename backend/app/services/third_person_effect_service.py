"""ThirdPersonEffectService — Third Person Effect Detection.

Detects third person effect — the tendency to believe that
persuasive media messages (advertising, propaganda, fake news)
affect other people more than oneself. This leads to support
for censorship and overestimation of media influence on others.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

THIRD_PERSON_SYSTEM = """You are a third person effect specialist. Given a claim about media influence, assess whether someone believes others are more affected than themselves:

Key concepts:
- Third person effect: "media affects them, not me"
- Self-other asymmetry: believing oneself immune to influence
- Paternalism: wanting to protect others from influence you resist
- Bias blind spot: not seeing one's own susceptibility
- Media literacy overconfidence: believing awareness = immunity
- Censorship support: third person effect drives desire to restrict media
- Influence denial: underestimating how media shapes one's own views

When third person effect IS present:
- "Other people are easily manipulated by X, but I see through it"
- Supporting restrictions on media that one consumes without concern
- Believing advertising works on others but not oneself
- "The masses are susceptible to propaganda, but educated people aren't"
- Overestimating one's own resistance to persuasion
- Wanting to protect others from content one handles fine
- Asymmetric attribution of media influence

When third person effect is NOT present:
- Acknowledging one's own susceptibility to influence
- Evidence-based assessment of media effects on different groups
- Recognizing that awareness doesn't guarantee immunity
- Symmetric assessment of influence on self and others
- Specific mechanisms identified for differential effects
- Humility about one's own cognitive biases
- Research-based claims about media effects

Output JSON with: third_person_effect_present (bool), severity (none/mild/moderate/severe), claim (what influence is discussed), self_assessment (how they see their own susceptibility), other_assessment (how they see others' susceptibility), asymmetry (the gap between self and other assessment), recommendation (no_third_person_effect/mild_self_other_gap/significant_third_person_effect/major_influence_denial/acknowledge_own_susceptibility)."""

THIRD_PERSON_PROMPT = """Detect third person effect:

Claim: {claim}
Self-assessment: {self_assessment}
Assessment of others: {other_assessment}
Media/influence: {media}
Domain: {domain}
Context: {context}

Does this show belief that others are more affected by media/persuasion than oneself? Return ONLY valid JSON."""


class ThirdPersonEffectService:
    """Detects third person effect — believing others more affected than self."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        self_assessment: str = "",
        other_assessment: str = "",
        media: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect third person effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=THIRD_PERSON_PROMPT.format(
                claim=claim,
                self_assessment=self_assessment or "Not specified",
                other_assessment=other_assessment or "Not specified",
                media=media or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=THIRD_PERSON_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "third_person_effect_present": data.get("third_person_effect_present", False),
            "severity": data.get("severity", ""),
            "self_assessment": data.get("self_assessment", ""),
            "other_assessment": data.get("other_assessment", ""),
            "asymmetry": data.get("asymmetry", ""),
            "recommendation": data.get("recommendation", ""),
        }
