"""EpistemicStandingWaveService — Epistemic Standing Wave Detection.

Detects epistemic standing waves — ideas that appear stationary because
two opposing flows of equal strength cancel each other's movement.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_STANDING_WAVE_SYSTEM = """You are an epistemic standing wave specialist. Given an idea stasis pattern, assess whether opposing flows create apparent stationarity:

Key concepts:
- Epistemic standing wave: opposing flows creating apparent stasis
- Node: point of zero movement where flows cancel
- Antinode: point of maximum oscillation
- Interference: two flows combining constructively or destructively
- Fundamental: lowest frequency standing wave
- Harmonic: higher frequency standing waves
- Boundary condition: what constrains the wave at edges

When epistemic standing wave IS present:
- Ideas appearing stationary from opposing equal flows
- Points of zero movement where flows cancel
- Points of maximum oscillation between nodes
- Two flows combining to create pattern
- Lowest frequency pattern dominating
- Higher frequency patterns also present
- Constraints at boundaries shaping the wave

When free propagation is present:
- Ideas moving freely without opposition
- No points of cancellation
- No oscillation pattern
- No combining flows
- No dominant frequency
- No harmonic patterns
- No boundary constraints

Output JSON with: standing_wave_present (bool), severity (none/mild/moderate/severe), nodes (what points of zero movement), antinodes (what points of maximum oscillation), interference (what opposing flows), boundary (what constrains the pattern), recommendation (free_propagation/mild_interference/significant_standing_wave/major_stasis_pattern/remove_opposing_flow)."""

EPISTEMIC_STANDING_WAVE_PROMPT = """Detect epistemic standing wave:

Nodes: {nodes}
Antinodes: {antinodes}
Interference: {interference}
Boundary: {boundary}
Domain: {domain}
Context: {context}

Are ideas appearing stationary because two opposing flows of equal strength cancel each other's movement? Return ONLY valid JSON."""


class EpistemicStandingWaveService:
    """Detects epistemic standing waves — opposing flows creating stasis."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        nodes: str,
        *,
        antinodes: str = "",
        interference: str = "",
        boundary: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic standing wave."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_STANDING_WAVE_PROMPT.format(
                nodes=nodes,
                antinodes=antinodes or "Not specified",
                interference=interference or "Not specified",
                boundary=boundary or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_STANDING_WAVE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "nodes": nodes[:200],
            "standing_wave_present": data.get("standing_wave_present", False),
            "severity": data.get("severity", ""),
            "antinodes": data.get("antinodes", ""),
            "interference": data.get("interference", ""),
            "boundary": data.get("boundary", ""),
            "recommendation": data.get("recommendation", ""),
        }
