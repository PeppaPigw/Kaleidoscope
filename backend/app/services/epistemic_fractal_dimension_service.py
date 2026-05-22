"""EpistemicFractalDimensionService — Epistemic Fractal Dimension Detection.

Detects epistemic fractal dimension — intellectual structures with
non-integer dimensionality, exhibiting self-similarity at every scale.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FRACTAL_DIMENSION_SYSTEM = """You are an epistemic fractal dimension specialist. Given an intellectual structure, assess whether it has non-integer dimensionality with self-similarity:

Key concepts:
- Epistemic fractal dimension: non-integer dimensionality
- Self-similarity: same pattern at every scale
- Hausdorff dimension: measuring fractal complexity
- Scale invariance: no characteristic scale
- Coastline paradox: length depending on measurement scale
- Cantor set: removing middle thirds recursively
- Julia set: boundary between convergence and divergence

When epistemic fractal dimension IS present:
- Structures with non-integer dimensionality
- Same pattern appearing at every scale of analysis
- Complexity between integer dimensions
- No characteristic scale of the structure
- Measurement depending on resolution
- Recursive removal creating gaps
- Boundary between intellectual convergence and divergence

When integer-dimensional structure is present:
- Structures with clean integer dimensions
- Different patterns at different scales
- Complexity matching integer dimensions
- Clear characteristic scale
- Measurement independent of resolution
- No recursive gap creation
- Clear boundaries without fractal edges

Output JSON with: fractal_dimension_present (bool), severity (none/mild/moderate/severe), self_similarity (what repeating pattern), hausdorff (what complexity measure), scale_invariance (what lacks characteristic scale), coastline (what resolution dependence), recommendation (integer_dimensional/mild_fractal/significant_fractal_dimension/major_self_similarity/identify_characteristic_scale)."""

EPISTEMIC_FRACTAL_DIMENSION_PROMPT = """Detect epistemic fractal dimension:

Self-similarity: {self_similarity}
Hausdorff: {hausdorff}
Scale invariance: {scale_invariance}
Coastline: {coastline}
Domain: {domain}
Context: {context}

Does this intellectual structure have non-integer dimensionality, exhibiting self-similarity at every scale? Return ONLY valid JSON."""


class EpistemicFractalDimensionService:
    """Detects epistemic fractal dimension — non-integer dimensionality."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        self_similarity: str,
        *,
        hausdorff: str = "",
        scale_invariance: str = "",
        coastline: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic fractal dimension."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FRACTAL_DIMENSION_PROMPT.format(
                self_similarity=self_similarity,
                hausdorff=hausdorff or "Not specified",
                scale_invariance=scale_invariance or "Not specified",
                coastline=coastline or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FRACTAL_DIMENSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "self_similarity": self_similarity[:200],
            "fractal_dimension_present": data.get("fractal_dimension_present", False),
            "severity": data.get("severity", ""),
            "hausdorff": data.get("hausdorff", ""),
            "scale_invariance": data.get("scale_invariance", ""),
            "coastline": data.get("coastline", ""),
            "recommendation": data.get("recommendation", ""),
        }
