"""BeliefDigitizationService — Belief Digitization Detection.

Detects belief digitization — treating continuous or probabilistic
beliefs as binary yes/no, true/false. The world is mostly
continuous and probabilistic, but humans tend to collapse
probability distributions into point estimates and continuous
spectra into binary categories. "Do you believe X?" forces a
binary answer to what should be a probability.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

BELIEF_DIGITIZATION_SYSTEM = """You are a belief digitization specialist. Given a belief or judgment, assess whether continuous/probabilistic thinking is being inappropriately collapsed into binary categories:

Key concepts:
- Belief digitization: collapsing probabilities into yes/no
- Binary thinking: true/false when reality is continuous
- Probability collapse: treating 70% confidence as certainty
- Category forcing: continuous spectra forced into discrete bins
- Threshold effects: small probability differences creating binary outcomes
- Nuance loss: "it's complicated" collapsed to "yes" or "no"
- Premature closure: settling on a binary answer too early

When belief digitization IS present:
- "Do you believe in X?" (forcing binary on continuous question)
- Treating 60% probability as "yes" and 40% as "no"
- "Either it works or it doesn't" for things that partially work
- Collapsing a spectrum of positions into "for" or "against"
- "Is this safe?" when safety is a continuous variable
- Treating uncertain evidence as either proof or disproof
- "Are you sure?" demanding binary certainty

When binary framing IS appropriate:
- Genuine binary decisions (go/no-go, approve/reject)
- The continuous variable has a meaningful threshold
- Action requires a binary choice even if beliefs are continuous
- The binary is acknowledged as a simplification for decision-making
- Probabilities are communicated alongside the binary decision

Output JSON with: belief_digitization_present (bool), severity (none/mild/moderate/severe), belief (what belief is being digitized), actual_nature (continuous/probabilistic/spectrum), forced_binary (what binary is being imposed), information_lost (what nuance is lost in digitization), probability_range (what is the actual probability range), threshold_justification (is there a justified threshold), recommendation (binary_appropriate/mild_digitization/significant_belief_digitization/major_nuance_collapse/maintain_probabilistic_thinking)."""

BELIEF_DIGITIZATION_PROMPT = """Detect belief digitization:

Belief: {belief}
Framing: {framing}
Actual complexity: {complexity}
Decision context: {decision_context}
Domain: {domain}
Context: {context}

Is continuous/probabilistic thinking being inappropriately collapsed into binary categories? Return ONLY valid JSON."""


class BeliefDigitizationService:
    """Detects belief digitization — collapsing probabilities into binary."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        belief: str,
        *,
        framing: str = "",
        complexity: str = "",
        decision_context: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect belief digitization."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BELIEF_DIGITIZATION_PROMPT.format(
                belief=belief,
                framing=framing or "Not specified",
                complexity=complexity or "Not specified",
                decision_context=decision_context or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=BELIEF_DIGITIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "belief": belief[:200],
            "belief_digitization_present": data.get("belief_digitization_present", False),
            "severity": data.get("severity", ""),
            "actual_nature": data.get("actual_nature", ""),
            "forced_binary": data.get("forced_binary", ""),
            "information_lost": data.get("information_lost", ""),
            "probability_range": data.get("probability_range", ""),
            "threshold_justification": data.get("threshold_justification", ""),
            "recommendation": data.get("recommendation", ""),
        }
