"""AnchoringCascadeService — Anchoring Cascade Detection.

Detects anchoring cascades — when an initial anchor propagates
through a chain of judgments, with each subsequent estimate
anchored to the previous one. This compounds anchoring bias
across multiple steps, making the final estimate heavily
dependent on the initial arbitrary value.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ANCHORING_CASCADE_SYSTEM = """You are an anchoring cascade specialist. Given a chain of judgments, assess whether anchoring is propagating through the chain:

Key concepts:
- Anchoring cascade: initial anchor propagates through sequential judgments
- Compounding bias: each step anchored to previous biased estimate
- Information cascade: sequential decisions influenced by predecessors
- Path dependence: final answer depends on order of estimation
- Insufficient adjustment: each step adjusts insufficiently from anchor
- Propagation: bias amplifies or maintains through the chain
- Independence violation: judgments should be independent but aren't

When anchoring cascade IS present:
- Sequential estimates each anchored to the previous one
- Initial arbitrary value influencing final conclusion through chain
- Insufficient adjustment at each step compounding through sequence
- Order of estimation affecting final answer
- Early estimate constraining all subsequent judgments
- Chain of reasoning where each link is anchored to predecessor
- Final estimate traceable back to initial arbitrary anchor

When anchoring cascade is NOT present:
- Each judgment made independently of previous estimates
- Initial values don't propagate through the chain
- Adequate adjustment at each step
- Order of estimation doesn't affect final answer
- Independent evidence used at each stage
- Chain of reasoning with independently grounded links
- Final estimate robust to changes in initial values

Output JSON with: cascade_present (bool), severity (none/mild/moderate/severe), initial_anchor (what started the cascade), chain_length (how many steps in the cascade), propagation (how the anchor propagates), final_distortion (how far final estimate is from independent estimate), recommendation (no_cascade/mild_propagation/significant_cascade/major_compounding/break_chain_and_re_estimate)."""

ANCHORING_CASCADE_PROMPT = """Detect anchoring cascade:

Judgment chain: {chain}
Initial value: {initial_value}
Sequential estimates: {estimates}
Final conclusion: {final_conclusion}
Domain: {domain}
Context: {context}

Is an initial anchor propagating through a chain of judgments? Return ONLY valid JSON."""


class AnchoringCascadeService:
    """Detects anchoring cascades — anchors propagating through judgment chains."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        chain: str,
        *,
        initial_value: str = "",
        estimates: str = "",
        final_conclusion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect anchoring cascade."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ANCHORING_CASCADE_PROMPT.format(
                chain=chain,
                initial_value=initial_value or "Not specified",
                estimates=estimates or "Not specified",
                final_conclusion=final_conclusion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ANCHORING_CASCADE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "chain": chain[:200],
            "cascade_present": data.get("cascade_present", False),
            "severity": data.get("severity", ""),
            "initial_anchor": data.get("initial_anchor", ""),
            "chain_length": data.get("chain_length", ""),
            "propagation": data.get("propagation", ""),
            "recommendation": data.get("recommendation", ""),
        }
