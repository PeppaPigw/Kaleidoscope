"""SlipperySlopeService — Slippery Slope Detection.

Detects slippery slope fallacy — arguing that one step will
inevitably lead to a chain of events ending in an extreme
consequence, without adequate justification for the causal
chain's inevitability.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SLIPPERY_SLOPE_SYSTEM = """You are a slippery slope specialist. Given an argument, assess whether it fallaciously claims that one action will inevitably lead to extreme consequences:

Key concepts:
- Slippery slope: A leads to B leads to C... leads to catastrophe
- Causal chain: each link must be justified, not assumed
- Inevitability assumption: treating possible outcomes as certain
- Precedent argument: sometimes precedents DO matter (distinguish)
- Domino fallacy: assuming each step necessarily triggers the next
- Thin end of the wedge: legitimate concern vs fallacious reasoning
- Empirical slopes: some slopes ARE slippery (evidence-based)

When slippery slope IS present:
- "If we allow X, next thing you know we'll have Y" without justification
- Treating a chain of possibilities as certainties
- No evidence that each step actually leads to the next
- Ignoring that the chain can be stopped at any point
- Catastrophizing: jumping from minor action to extreme outcome
- "Where do you draw the line?" as if no line CAN be drawn
- Assuming no intervening factors or safeguards

When slippery slope is NOT present:
- Each causal link is supported by evidence or mechanism
- Historical precedent shows the progression actually occurs
- The argument acknowledges uncertainty in the chain
- Institutional or structural factors make progression likely
- The slope is empirically documented (e.g., addiction, authoritarianism)
- Safeguards are discussed and found inadequate
- The argument is about probability, not inevitability

Output JSON with: slippery_slope_present (bool), severity (none/mild/moderate/severe), initial_step (what first action is proposed), claimed_endpoint (what extreme outcome is predicted), causal_chain (what intermediate steps are claimed), justification (is each link justified), stoppability (can the chain be interrupted), recommendation (no_slippery_slope/mild_catastrophizing/significant_slippery_slope/major_domino_fallacy/justify_each_link)."""

SLIPPERY_SLOPE_PROMPT = """Detect slippery slope:

Argument: {argument}
Initial action: {initial_action}
Predicted outcome: {predicted_outcome}
Causal chain: {causal_chain}
Domain: {domain}
Context: {context}

Does this fallaciously claim one step inevitably leads to extreme consequences? Return ONLY valid JSON."""


class SlipperySlopeService:
    """Detects slippery slope — unjustified claims of inevitable escalation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        initial_action: str = "",
        predicted_outcome: str = "",
        causal_chain: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect slippery slope."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SLIPPERY_SLOPE_PROMPT.format(
                argument=argument,
                initial_action=initial_action or "Not specified",
                predicted_outcome=predicted_outcome or "Not specified",
                causal_chain=causal_chain or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SLIPPERY_SLOPE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "slippery_slope_present": data.get("slippery_slope_present", False),
            "severity": data.get("severity", ""),
            "initial_step": data.get("initial_step", ""),
            "claimed_endpoint": data.get("claimed_endpoint", ""),
            "causal_chain": data.get("causal_chain", ""),
            "recommendation": data.get("recommendation", ""),
        }
