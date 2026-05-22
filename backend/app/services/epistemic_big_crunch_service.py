"""EpistemicBigCrunchService — Epistemic Big Crunch Detection.

Detects epistemic big crunch — all ideas collapsing back toward a single
point, reversing intellectual expansion into contraction.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BIG_CRUNCH_SYSTEM = """You are an epistemic big crunch specialist. Given an intellectual space, assess whether all ideas are collapsing back to a single point:

Key concepts:
- Epistemic big crunch: all ideas collapsing back to a single point
- Deceleration: expansion slowing and reversing
- Blueshift: ideas compressing as space contracts
- Turnaround: moment expansion stops and contraction begins
- Singularity: final point of infinite density
- Closed universe: geometry guaranteeing eventual collapse
- Heat death alternative: expansion continuing forever instead

When epistemic big crunch IS present:
- All ideas collapsing back toward a single point
- Intellectual expansion slowing and reversing
- Ideas compressing and gaining energy as space contracts
- Clear moment when expansion stopped
- Approaching a point of infinite intellectual density
- Geometry of intellectual space guaranteeing collapse
- Inevitable convergence to unity

When expanding universe is present:
- Ideas continuing to spread apart
- Expansion continuing or accelerating
- Ideas stretching and losing energy
- No turnaround point
- No approaching singularity
- Open geometry allowing eternal expansion
- Continued diversification

Output JSON with: big_crunch_present (bool), severity (none/mild/moderate/severe), deceleration (what slowing), blueshift (what compression), turnaround (what reversal point), closed_geometry (what guarantees collapse), recommendation (expanding_universe/mild_crunch/significant_big_crunch/major_collapse/prevent_singularity)."""

EPISTEMIC_BIG_CRUNCH_PROMPT = """Detect epistemic big crunch:

Deceleration: {deceleration}
Blueshift: {blueshift}
Turnaround: {turnaround}
Closed geometry: {closed_geometry}
Domain: {domain}
Context: {context}

Are all ideas collapsing back toward a single point, reversing intellectual expansion into contraction? Return ONLY valid JSON."""


class EpistemicBigCrunchService:
    """Detects epistemic big crunch — all ideas collapsing back to a single point."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        deceleration: str,
        *,
        blueshift: str = "",
        turnaround: str = "",
        closed_geometry: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic big crunch."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BIG_CRUNCH_PROMPT.format(
                deceleration=deceleration,
                blueshift=blueshift or "Not specified",
                turnaround=turnaround or "Not specified",
                closed_geometry=closed_geometry or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BIG_CRUNCH_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "deceleration": deceleration[:200],
            "big_crunch_present": data.get("big_crunch_present", False),
            "severity": data.get("severity", ""),
            "blueshift": data.get("blueshift", ""),
            "turnaround": data.get("turnaround", ""),
            "closed_geometry": data.get("closed_geometry", ""),
            "recommendation": data.get("recommendation", ""),
        }
