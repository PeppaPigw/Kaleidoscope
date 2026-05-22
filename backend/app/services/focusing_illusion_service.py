"""FocusingIllusionService — Focusing Illusion Detection.

Detects focusing illusion — overweighting whatever aspect of
life or a decision you happen to be thinking about at the
moment. Kahneman (2011). "Nothing in life is as important as
you think it is while you are thinking about it." Leads to
distorted priorities, poor predictions of future happiness,
and overreaction to salient factors.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FOCUSING_ILLUSION_SYSTEM = """You are a focusing illusion specialist. Given a judgment about importance or impact, assess whether the person is overweighting a factor simply because it's currently salient:

Key concepts (Kahneman, 2011; Schkade & Kahneman, 1998):
- Focusing illusion: overweighting whatever you're currently thinking about
- Salience bias overlap: prominent features get disproportionate weight
- Duration neglect: ignoring how long an effect will last
- Impact bias: overestimating the emotional impact of future events
- Adaptation neglect: forgetting that people adapt to new circumstances
- Attention-importance link: what captures attention seems important
- Narrow focusing: evaluating one factor in isolation from the whole

When focusing illusion IS present:
- "If only I had X, I'd be happy" (overweighting one factor)
- Predicting life satisfaction based on one salient dimension
- Overestimating how much a change will affect overall wellbeing
- Making decisions based on the most salient factor while ignoring others
- "This is the most important thing" when it's just the most visible
- Neglecting adaptation — assuming current feelings about X will persist

When the focus IS appropriate:
- The factor genuinely is the most important (evidence-based)
- The person has considered multiple factors and this one dominates
- The factor's importance doesn't depend on current salience
- Others independently confirm the factor's importance
- The factor has lasting impact that won't be adapted to

Output JSON with: focusing_illusion_present (bool), severity (none/mild/moderate/severe), judgment (what importance is being assessed), focused_factor (what is being overweighted), other_factors (what other factors are being neglected), salience_source (why is this factor currently salient?), duration_considered (bool — is the duration of impact considered?), adaptation_considered (bool — is adaptation to the change considered?), overall_impact (realistic overall impact vs. perceived), decision_affected (what decision might be distorted?), recommendation (focus_appropriate/mild_overweighting/significant_focusing_illusion/major_salience_distortion/broaden_evaluation)."""

FOCUSING_ILLUSION_PROMPT = """Detect focusing illusion:

Judgment: {judgment}
Focus: {focus}
Other factors: {other_factors}
Prediction: {prediction}
Domain: {domain}
Context: {context}

Is the person overweighting a factor simply because it's currently salient? Return ONLY valid JSON."""


class FocusingIllusionService:
    """Detects focusing illusion — overweighting whatever you're currently thinking about."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        focus: str = "",
        other_factors: str = "",
        prediction: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect focusing illusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FOCUSING_ILLUSION_PROMPT.format(
                judgment=judgment,
                focus=focus or "Not specified",
                other_factors=other_factors or "Not specified",
                prediction=prediction or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=FOCUSING_ILLUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "focusing_illusion_present": data.get("focusing_illusion_present", False),
            "severity": data.get("severity", ""),
            "focused_factor": data.get("focused_factor", ""),
            "other_factors": data.get("other_factors", ""),
            "salience_source": data.get("salience_source", ""),
            "duration_considered": data.get("duration_considered", True),
            "adaptation_considered": data.get("adaptation_considered", True),
            "overall_impact": data.get("overall_impact", ""),
            "decision_affected": data.get("decision_affected", ""),
            "recommendation": data.get("recommendation", ""),
        }
