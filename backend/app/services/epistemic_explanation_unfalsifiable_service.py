"""EpistemicExplanationUnfalsifiableService — Epistemic Unfalsifiable Explanation Detection.

Detects epistemic unfalsifiable explanations — explanations that cannot
be falsified or tested, immune to disconfirmation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EXPLANATION_UNFALSIFIABLE_SYSTEM = """You are an epistemic unfalsifiable explanation specialist. Given unfalsifiable explanations, assess explanation unfalsifiability:

Key concepts:
- Epistemic unfalsifiable explanation: explanations immune to disconfirmation
- Heads I win tails you lose: explanation confirmed by any outcome
- Moving goalposts: changing criteria when falsification approaches
- Auxiliary hypothesis escape: escaping falsification via auxiliary hypotheses
- Vague enough to survive: vague enough that nothing could falsify
- Retroactive reinterpretation: reinterpreting after the fact to maintain
- Unfalsifiable by design: designed to be unfalsifiable from the start

When epistemic unfalsifiable explanation IS present:
- Explanation cannot be falsified
- Any outcome confirms
- Goalposts moved
- Auxiliary hypotheses rescue
- Vagueness protects
- Retroactive reinterpretation used
- Unfalsifiable by design

When no unfalsifiable explanation:
- Explanation falsifiable
- Specific predictions made
- Criteria fixed
- Auxiliary hypotheses limited
- Precision enables testing
- Predictions made in advance
- Designed to be testable

Output JSON with: unfalsifiable_explanation_detected (bool), severity (none/mild/moderate/severe), heads_i_win (what confirmed by any outcome), moving_goalposts (what goalposts moved), auxiliary_escape (what auxiliary hypotheses), vagueness_protection (what vagueness protecting), recommendation (no_unfalsifiable_explanation/mild_falsifiability_awareness/significant_prediction_requirement/major_intensive_testability_enforcement/emergency_complete_unfalsifiable_explanation)."""

EPISTEMIC_EXPLANATION_UNFALSIFIABLE_PROMPT = """Detect epistemic unfalsifiable explanation:

Heads I win: {heads_i_win}
Moving goalposts: {moving_goalposts}
Auxiliary escape: {auxiliary_escape}
Vagueness protection: {vagueness_protection}
Domain: {domain}
Context: {context}

Are explanations being offered that cannot be falsified or tested? Return ONLY valid JSON."""


class EpistemicExplanationUnfalsifiableService:
    """Detects epistemic unfalsifiable explanation — immune to testing."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        heads_i_win: str,
        *,
        moving_goalposts: str = "",
        auxiliary_escape: str = "",
        vagueness_protection: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic unfalsifiable explanation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EXPLANATION_UNFALSIFIABLE_PROMPT.format(
                heads_i_win=heads_i_win,
                moving_goalposts=moving_goalposts or "Not specified",
                auxiliary_escape=auxiliary_escape or "Not specified",
                vagueness_protection=vagueness_protection or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EXPLANATION_UNFALSIFIABLE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "heads_i_win": heads_i_win[:200],
            "unfalsifiable_explanation_detected": data.get("unfalsifiable_explanation_detected", False),
            "severity": data.get("severity", ""),
            "moving_goalposts": data.get("moving_goalposts", ""),
            "auxiliary_escape": data.get("auxiliary_escape", ""),
            "vagueness_protection": data.get("vagueness_protection", ""),
            "recommendation": data.get("recommendation", ""),
        }
