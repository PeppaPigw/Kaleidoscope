"""EpistemicTopologicalInsulatorService — Epistemic Topological Insulator Detection.

Detects epistemic topological insulator — ideas conducting on the surface
but insulating in the bulk, with protected boundary states.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TOPOLOGICAL_INSULATOR_SYSTEM = """You are an epistemic topological insulator specialist. Given an intellectual system, assess whether ideas conduct on the surface but insulate in the bulk:

Key concepts:
- Epistemic topological insulator: conducting surface, insulating bulk
- Edge state: protected conducting channel at boundary
- Bulk gap: energy gap preventing bulk conduction
- Topological invariant: number characterizing the topology
- Time-reversal symmetry: protection mechanism for edge states
- Dirac cone: linear dispersion at the surface
- Robustness: edge states surviving disorder

When epistemic topological insulator IS present:
- Ideas flowing freely on boundaries but blocked in interior
- Protected channels at intellectual boundaries
- Energy gap preventing interior flow
- Topological number characterizing the state
- Symmetry protecting the boundary channels
- Linear relationship at the surface
- Boundary flow surviving disruption

When uniform conductor is present:
- Ideas flowing equally everywhere
- No special boundary channels
- No interior gap
- No topological characterization
- No symmetry protection
- No special surface behavior
- No robustness to disorder

Output JSON with: topological_insulator_present (bool), severity (none/mild/moderate/severe), edge_state (what boundary channel), bulk_gap (what interior blocking), topological_invariant (what characterizing number), robustness (what disorder survival), recommendation (uniform_conductor/mild_topological/significant_topological_insulator/major_bulk_surface_split/exploit_edge_states)."""

EPISTEMIC_TOPOLOGICAL_INSULATOR_PROMPT = """Detect epistemic topological insulator:

Edge state: {edge_state}
Bulk gap: {bulk_gap}
Topological invariant: {topological_invariant}
Robustness: {robustness}
Domain: {domain}
Context: {context}

Are ideas conducting on the surface but insulating in the bulk, with protected boundary states? Return ONLY valid JSON."""


class EpistemicTopologicalInsulatorService:
    """Detects epistemic topological insulator — conducting surface, insulating bulk."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        edge_state: str,
        *,
        bulk_gap: str = "",
        topological_invariant: str = "",
        robustness: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic topological insulator."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TOPOLOGICAL_INSULATOR_PROMPT.format(
                edge_state=edge_state,
                bulk_gap=bulk_gap or "Not specified",
                topological_invariant=topological_invariant or "Not specified",
                robustness=robustness or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TOPOLOGICAL_INSULATOR_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "edge_state": edge_state[:200],
            "topological_insulator_present": data.get("topological_insulator_present", False),
            "severity": data.get("severity", ""),
            "bulk_gap": data.get("bulk_gap", ""),
            "topological_invariant": data.get("topological_invariant", ""),
            "robustness": data.get("robustness", ""),
            "recommendation": data.get("recommendation", ""),
        }
