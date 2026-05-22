"""EpistemicSpacetimeCurvatureService — Epistemic Spacetime Curvature Detection.

Detects epistemic spacetime curvature — massive ideas warping the
intellectual landscape so that nearby reasoning follows curved paths.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SPACETIME_CURVATURE_SYSTEM = """You are an epistemic spacetime curvature specialist. Given an intellectual landscape, assess whether massive ideas warp reasoning paths:

Key concepts:
- Epistemic spacetime curvature: massive ideas warping intellectual landscape
- Geodesic deviation: parallel paths converging near mass
- Ricci curvature: volume compression near massive ideas
- Weyl curvature: tidal stretching and squeezing
- Metric tensor: measuring distances in curved space
- Christoffel symbols: how coordinates change along paths
- Einstein equation: mass-energy determining curvature

When epistemic spacetime curvature IS present:
- Massive ideas warping the intellectual landscape
- Parallel reasoning paths converging near dominant ideas
- Volume of intellectual space compressed near mass
- Tidal stretching and squeezing of arguments
- Distances measured differently in curved regions
- Coordinates changing along intellectual paths
- Mass-energy of ideas determining local curvature

When flat spacetime is present:
- No warping of intellectual landscape
- Parallel paths remaining parallel
- Uniform volume throughout
- No tidal effects
- Uniform distance measurement
- Coordinates constant along paths
- No curvature from any source

Output JSON with: spacetime_curvature_present (bool), severity (none/mild/moderate/severe), geodesic_deviation (what path convergence), ricci (what volume compression), weyl (what tidal effect), metric (what distance distortion), recommendation (flat_spacetime/mild_curvature/significant_spacetime_curvature/major_warping/navigate_geodesics)."""

EPISTEMIC_SPACETIME_CURVATURE_PROMPT = """Detect epistemic spacetime curvature:

Geodesic deviation: {geodesic_deviation}
Ricci: {ricci}
Weyl: {weyl}
Metric: {metric}
Domain: {domain}
Context: {context}

Are massive ideas warping the intellectual landscape so that nearby reasoning follows curved paths? Return ONLY valid JSON."""


class EpistemicSpacetimeCurvatureService:
    """Detects epistemic spacetime curvature — massive ideas warping reasoning."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        geodesic_deviation: str,
        *,
        ricci: str = "",
        weyl: str = "",
        metric: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic spacetime curvature."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SPACETIME_CURVATURE_PROMPT.format(
                geodesic_deviation=geodesic_deviation,
                ricci=ricci or "Not specified",
                weyl=weyl or "Not specified",
                metric=metric or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SPACETIME_CURVATURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "geodesic_deviation": geodesic_deviation[:200],
            "spacetime_curvature_present": data.get("spacetime_curvature_present", False),
            "severity": data.get("severity", ""),
            "ricci": data.get("ricci", ""),
            "weyl": data.get("weyl", ""),
            "metric": data.get("metric", ""),
            "recommendation": data.get("recommendation", ""),
        }
