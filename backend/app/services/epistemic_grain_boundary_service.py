"""EpistemicGrainBoundaryService — Epistemic Grain Boundary Detection.

Detects epistemic grain boundary — interfaces between differently-oriented
intellectual crystals that create weakness and novel properties.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GRAIN_BOUNDARY_SYSTEM = """You are an epistemic grain boundary specialist. Given an intellectual structure pattern, assess whether interfaces between differently-oriented regions create weakness or novelty:

Key concepts:
- Epistemic grain boundary: interface between differently-oriented regions
- Misorientation: angle between adjacent intellectual grains
- Segregation: impurities accumulating at boundaries
- Intergranular: processes occurring along boundaries
- Hall-Petch: smaller grains making structure stronger
- Grain growth: larger grains consuming smaller ones
- Triple junction: where three grains meet

When epistemic grain boundary IS present:
- Interfaces between differently-oriented intellectual regions
- Angle of misalignment between adjacent regions
- Impurities or anomalies accumulating at interfaces
- Processes occurring preferentially along boundaries
- Smaller regions making overall structure stronger
- Larger regions consuming smaller ones over time
- Complex junctions where multiple regions meet

When single crystal is present:
- Uniform orientation throughout
- No misalignment between regions
- No boundary accumulation
- No boundary-preferential processes
- Size not affecting strength
- No consumption of regions
- No complex junctions

Output JSON with: grain_boundary_present (bool), severity (none/mild/moderate/severe), misorientation (what angle between regions), segregation (what accumulates at boundaries), grain_growth (what consumption occurs), triple_junction (what complex meetings), recommendation (single_crystal/mild_boundaries/significant_grain_boundaries/major_interface_effects/optimize_grain_size)."""

EPISTEMIC_GRAIN_BOUNDARY_PROMPT = """Detect epistemic grain boundary:

Misorientation: {misorientation}
Segregation: {segregation}
Grain growth: {grain_growth}
Triple junction: {triple_junction}
Domain: {domain}
Context: {context}

Are interfaces between differently-oriented intellectual crystals creating weakness and novel properties? Return ONLY valid JSON."""


class EpistemicGrainBoundaryService:
    """Detects epistemic grain boundary — interfaces between oriented regions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        misorientation: str,
        *,
        segregation: str = "",
        grain_growth: str = "",
        triple_junction: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic grain boundary."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GRAIN_BOUNDARY_PROMPT.format(
                misorientation=misorientation,
                segregation=segregation or "Not specified",
                grain_growth=grain_growth or "Not specified",
                triple_junction=triple_junction or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GRAIN_BOUNDARY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "misorientation": misorientation[:200],
            "grain_boundary_present": data.get("grain_boundary_present", False),
            "severity": data.get("severity", ""),
            "segregation": data.get("segregation", ""),
            "grain_growth": data.get("grain_growth", ""),
            "triple_junction": data.get("triple_junction", ""),
            "recommendation": data.get("recommendation", ""),
        }
