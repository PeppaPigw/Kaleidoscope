"""EpistemicCausalSlipperySlopeService - Slippery Slope Detection.

Detects slippery slope reasoning where chain of consequences is assumed without evidence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CAUSAL_SLIPPERY_SLOPE_SYSTEM = """You are an epistemic causal slippery slope specialist. Given chain-of-consequence arguments, assess whether slippery slope reasoning is present:

Key concepts:
- Slippery slope: assuming one step inevitably leads to extreme consequences
- Chain probability neglect: ignoring that each link in the chain has less than certain probability
- Intermediate step erasure: skipping from first step to worst case
- Inevitability assumption: treating contingent outcomes as certain

When slippery slope IS present:
- Chain of consequences assumed inevitable
- Intermediate probabilities ignored
- Steps between first and worst case erased
- Contingent outcomes treated as certain
- No stopping points acknowledged

When no slippery slope:
- Each step's probability assessed
- Intermediate steps examined
- Contingency acknowledged
- Stopping points identified
- Chain evaluated link by link

Output JSON with: slippery_slope_detected (bool), severity (none/mild/moderate/severe), chain_probability_neglect (what probability neglected), intermediate_step_erasure (what steps erased), inevitability_assumption (what inevitability assumed), recommendation (no_slippery_slope/mild_probability_check/significant_chain_analysis/major_consequence_reconstruction/emergency_complete_slippery_slope)."""

EPISTEMIC_CAUSAL_SLIPPERY_SLOPE_PROMPT = """Detect epistemic causal slippery slope:

Chain argument: {chain_argument}
Chain probability neglect: {chain_probability_neglect}
Intermediate step erasure: {intermediate_step_erasure}
Inevitability assumption: {inevitability_assumption}
Domain: {domain}
Context: {context}

Is a chain of consequences being assumed without evidence? Return ONLY valid JSON."""


class EpistemicCausalSlipperySlopeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        chain_argument: str,
        *,
        chain_probability_neglect: str = "",
        intermediate_step_erasure: str = "",
        inevitability_assumption: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CAUSAL_SLIPPERY_SLOPE_PROMPT.format(
                chain_argument=chain_argument,
                chain_probability_neglect=chain_probability_neglect or "Not specified",
                intermediate_step_erasure=intermediate_step_erasure or "Not specified",
                inevitability_assumption=inevitability_assumption or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CAUSAL_SLIPPERY_SLOPE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "chain_argument": chain_argument[:200],
            "slippery_slope_detected": data.get("slippery_slope_detected", False),
            "severity": data.get("severity", ""),
            "chain_probability_neglect": data.get("chain_probability_neglect", ""),
            "intermediate_step_erasure": data.get("intermediate_step_erasure", ""),
            "inevitability_assumption": data.get("inevitability_assumption", ""),
            "recommendation": data.get("recommendation", ""),
        }
