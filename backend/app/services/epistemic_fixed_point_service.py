"""EpistemicFixedPointService — Epistemic Fixed Point Detection.

Detects epistemic fixed point — intellectual operations that when applied
repeatedly always converge to the same state regardless of starting position.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FIXED_POINT_SYSTEM = """You are an epistemic fixed point specialist. Given an intellectual operation, assess whether repeated application converges to a fixed state:

Key concepts:
- Epistemic fixed point: operation converging to same state
- Contraction mapping: operation bringing points closer
- Banach theorem: contraction guarantees unique fixed point
- Attracting fixed point: nearby points converge to it
- Repelling fixed point: nearby points diverge from it
- Basin of attraction: region converging to fixed point
- Iteration: repeated application of the operation

When epistemic fixed point IS present:
- Operations converging to same state regardless of start
- Operation bringing intellectual positions closer together
- Guaranteed convergence to unique position
- Nearby positions being attracted to the fixed point
- Some positions being repelled from unstable points
- Region of starting positions all converging
- Repeated application showing convergence

When divergent operation is present:
- Operations not converging to any state
- Operation spreading positions apart
- No guaranteed convergence
- No attracting positions
- No repelling positions
- No basin of attraction
- Repeated application showing divergence

Output JSON with: fixed_point_present (bool), severity (none/mild/moderate/severe), contraction (what brings closer), attracting (what draws in), basin (what region converges), iteration (what convergence pattern), recommendation (divergent_operation/mild_fixed_point/significant_fixed_point/major_convergence/escape_fixed_point)."""

EPISTEMIC_FIXED_POINT_PROMPT = """Detect epistemic fixed point:

Contraction: {contraction}
Attracting: {attracting}
Basin: {basin}
Iteration: {iteration}
Domain: {domain}
Context: {context}

Does this intellectual operation when applied repeatedly always converge to the same state regardless of starting position? Return ONLY valid JSON."""


class EpistemicFixedPointService:
    """Detects epistemic fixed point — operations converging to same state."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        contraction: str,
        *,
        attracting: str = "",
        basin: str = "",
        iteration: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic fixed point."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FIXED_POINT_PROMPT.format(
                contraction=contraction,
                attracting=attracting or "Not specified",
                basin=basin or "Not specified",
                iteration=iteration or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FIXED_POINT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "contraction": contraction[:200],
            "fixed_point_present": data.get("fixed_point_present", False),
            "severity": data.get("severity", ""),
            "attracting": data.get("attracting", ""),
            "basin": data.get("basin", ""),
            "iteration": data.get("iteration", ""),
            "recommendation": data.get("recommendation", ""),
        }
