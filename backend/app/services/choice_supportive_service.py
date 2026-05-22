"""ChoiceSupportiveService — Choice-Supportive Bias Detection.

Detects choice-supportive bias — retroactively attributing more
positive features to chosen options and more negative features
to rejected options. Mather & Johnson (2000). After making a
decision, memory distorts to make the choice seem better than
it was. Post-purchase rationalization, selective memory.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CHOICE_SUPPORTIVE_SYSTEM = """You are a choice-supportive bias specialist. Given a post-decision evaluation, assess whether memory and attribution are being distorted to support the choice:

Key concepts (Mather & Johnson, 2000):
- Choice-supportive bias: remembering chosen options as better than they were
- Post-decision dissonance reduction: reducing cognitive dissonance after choosing
- Selective memory: remembering positives of chosen, negatives of rejected
- Attribution distortion: attributing positive features to choice, negative to alternatives
- Effort justification overlap: the more effort invested, the stronger the bias
- Sunk cost interaction: past investment amplifies choice-supportive distortion

When choice-supportive bias IS present:
- Retroactively inflating the quality of a past decision
- Selectively remembering only positives of the chosen option
- Attributing negatives only to rejected alternatives
- "I always knew this was the right choice" (hindsight overlap)
- Dismissing evidence that the alternative might have been better
- Increasing satisfaction over time despite no new information

When positive evaluation IS warranted:
- The choice genuinely turned out well based on objective outcomes
- Both positives and negatives of the choice are acknowledged
- The evaluation is based on current evidence, not distorted memory
- Alternatives are fairly assessed rather than strawmanned
- The person can articulate what they'd do differently

Output JSON with: choice_supportive_present (bool), severity (none/mild/moderate/severe), decision (what was chosen), alternatives (what was rejected), positive_attribution (positives attributed to choice), negative_attribution (negatives attributed to alternatives), memory_distortion (bool — is memory being selectively recalled?), dissonance_reduction (bool — is this reducing post-decision dissonance?), effort_invested (how much was invested in the choice), objective_outcome (how did the choice actually turn out?), counterfactual_dismissed (bool — are "what ifs" being dismissed?), time_since_decision (how long ago was the choice made?), reversibility (can the decision still be changed?), recommendation (evaluation_fair/mild_choice_support/significant_distortion/major_choice_supportive_bias/reassess_objectively)."""

CHOICE_SUPPORTIVE_PROMPT = """Detect choice-supportive bias:

Decision made: {decision}
Current evaluation: {evaluation}
Alternatives rejected: {alternatives}
Evidence: {evidence}
Domain: {domain}
Context: {context}

Is the evaluation distorted to support the past choice? Return ONLY valid JSON."""


class ChoiceSupportiveService:
    """Detects choice-supportive bias — retroactive distortion favoring past choices."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        evaluation: str = "",
        alternatives: str = "",
        evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect choice-supportive bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CHOICE_SUPPORTIVE_PROMPT.format(
                decision=decision,
                evaluation=evaluation or "Not specified",
                alternatives=alternatives or "Not specified",
                evidence=evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CHOICE_SUPPORTIVE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "choice_supportive_present": data.get("choice_supportive_present", False),
            "severity": data.get("severity", ""),
            "positive_attribution": data.get("positive_attribution", ""),
            "negative_attribution": data.get("negative_attribution", ""),
            "memory_distortion": data.get("memory_distortion", False),
            "dissonance_reduction": data.get("dissonance_reduction", False),
            "effort_invested": data.get("effort_invested", ""),
            "objective_outcome": data.get("objective_outcome", ""),
            "counterfactual_dismissed": data.get("counterfactual_dismissed", False),
            "time_since_decision": data.get("time_since_decision", ""),
            "reversibility": data.get("reversibility", ""),
            "recommendation": data.get("recommendation", ""),
        }
