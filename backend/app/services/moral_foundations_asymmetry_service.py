"""MoralFoundationsAsymmetryService — Moral Foundations Asymmetry Detection.

Detects moral foundations asymmetry — the tendency to view one's
own moral foundations (care, fairness, loyalty, authority, sanctity)
as universally valid while dismissing others' foundations as mere
preferences or rationalizations. Haidt (2012). Liberals emphasize
care/fairness; conservatives weight all five — each side sees the
other as morally deficient rather than morally different.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MORAL_FOUNDATIONS_ASYMMETRY_SYSTEM = """You are a moral foundations asymmetry specialist. Given a moral disagreement, assess whether one side's moral foundations are being dismissed as invalid:

Key concepts (Haidt, 2012):
- Moral foundations: care, fairness, loyalty, authority, sanctity, liberty
- Foundation asymmetry: treating own foundations as universal, others as bias
- Moral matrix: each group lives in its own moral reality
- Moral dumbfounding: can't articulate why something is wrong but it IS wrong
- Moral taste buds: different people weight foundations differently
- Moral monism: assuming one foundation trumps all others
- Moral realism assumption: "my morality is objective, yours is cultural"

When moral foundations asymmetry IS present:
- "They don't really care about X, they just want power/control"
- Dismissing loyalty/authority/sanctity as primitive or irrational
- Dismissing care/fairness as naive or sentimental
- Assuming moral disagreement means moral deficiency
- "How can they not see that X is obviously wrong?"
- Treating own moral intuitions as self-evident truths
- Pathologizing the other side's moral reasoning

When moral evaluation IS appropriate:
- Some moral positions genuinely cause measurable harm
- The evaluation considers the other side's framework charitably
- Disagreement is about application, not foundation validity
- Both sides' moral reasoning is engaged with seriously
- The critique addresses specific claims, not entire moral worldviews

Output JSON with: moral_foundations_asymmetry_present (bool), severity (none/mild/moderate/severe), disagreement (what is the moral disagreement), own_foundations (which foundations are being privileged), other_foundations (which foundations are being dismissed), dismissal_mechanism (how are other foundations being invalidated), charitable_interpretation (is the other side's view engaged charitably), structural_harm (is there genuine harm being caused), recommendation (evaluation_fair/mild_foundation_bias/significant_moral_asymmetry/major_foundation_dismissal/engage_all_foundations_charitably)."""

MORAL_FOUNDATIONS_ASYMMETRY_PROMPT = """Detect moral foundations asymmetry:

Disagreement: {disagreement}
Own position: {own_position}
Other position: {other_position}
Characterization: {characterization}
Domain: {domain}
Context: {context}

Is one side's moral foundations being dismissed as invalid rather than engaged with charitably? Return ONLY valid JSON."""


class MoralFoundationsAsymmetryService:
    """Detects moral foundations asymmetry — dismissing others' moral frameworks."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        disagreement: str,
        *,
        own_position: str = "",
        other_position: str = "",
        characterization: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect moral foundations asymmetry."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MORAL_FOUNDATIONS_ASYMMETRY_PROMPT.format(
                disagreement=disagreement,
                own_position=own_position or "Not specified",
                other_position=other_position or "Not specified",
                characterization=characterization or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MORAL_FOUNDATIONS_ASYMMETRY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "disagreement": disagreement[:200],
            "moral_foundations_asymmetry_present": data.get("moral_foundations_asymmetry_present", False),
            "severity": data.get("severity", ""),
            "own_foundations": data.get("own_foundations", ""),
            "other_foundations": data.get("other_foundations", ""),
            "dismissal_mechanism": data.get("dismissal_mechanism", ""),
            "charitable_interpretation": data.get("charitable_interpretation", ""),
            "structural_harm": data.get("structural_harm", ""),
            "recommendation": data.get("recommendation", ""),
        }
