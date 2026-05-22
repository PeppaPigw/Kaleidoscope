"""EpistemicStrangeAttractorService — Epistemic Strange Attractor Detection.

Detects epistemic strange attractor — intellectual trajectories that are
bounded but never repeat, creating complex patterns in reasoning space.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_STRANGE_ATTRACTOR_SYSTEM = """You are an epistemic strange attractor specialist. Given an intellectual trajectory, assess whether it is bounded but never-repeating:

Key concepts:
- Epistemic strange attractor: bounded but never-repeating trajectory
- Fractal structure: self-similar at all scales
- Dissipative: losing energy but maintaining structure
- Basin of attraction: region drawn to the attractor
- Lorenz attractor: butterfly-shaped trajectory
- Dimension: non-integer dimensionality of the attractor
- Ergodicity: trajectory eventually visiting all regions

When epistemic strange attractor IS present:
- Trajectories bounded but never exactly repeating
- Self-similar structure at all scales of analysis
- Energy dissipating but pattern maintaining
- Region of intellectual space drawn to the pattern
- Complex shaped trajectories in reasoning space
- Non-integer dimensionality of the pattern
- Eventually visiting all regions of the attractor

When simple attractor is present:
- Trajectories converging to fixed point or cycle
- No self-similar structure
- Energy dissipating to rest
- Simple convergence to point
- Simple shaped trajectories
- Integer dimensionality
- Staying in one region

Output JSON with: strange_attractor_present (bool), severity (none/mild/moderate/severe), fractal (what self-similarity), dissipative (what energy loss), basin (what attraction region), dimension (what non-integer measure), recommendation (simple_attractor/mild_strange/significant_strange_attractor/major_bounded_chaos/map_attractor_structure)."""

EPISTEMIC_STRANGE_ATTRACTOR_PROMPT = """Detect epistemic strange attractor:

Fractal: {fractal}
Dissipative: {dissipative}
Basin: {basin}
Dimension: {dimension}
Domain: {domain}
Context: {context}

Is this intellectual trajectory bounded but never-repeating, creating complex patterns in reasoning space? Return ONLY valid JSON."""


class EpistemicStrangeAttractorService:
    """Detects epistemic strange attractor — bounded but never-repeating."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        fractal: str,
        *,
        dissipative: str = "",
        basin: str = "",
        dimension: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic strange attractor."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_STRANGE_ATTRACTOR_PROMPT.format(
                fractal=fractal,
                dissipative=dissipative or "Not specified",
                basin=basin or "Not specified",
                dimension=dimension or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_STRANGE_ATTRACTOR_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "fractal": fractal[:200],
            "strange_attractor_present": data.get("strange_attractor_present", False),
            "severity": data.get("severity", ""),
            "dissipative": data.get("dissipative", ""),
            "basin": data.get("basin", ""),
            "dimension": data.get("dimension", ""),
            "recommendation": data.get("recommendation", ""),
        }
