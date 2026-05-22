"""EpistemicSpinGlassService — Epistemic Spin Glass Detection.

Detects epistemic spin glass — frustrated intellectual system with many
competing ground states, unable to settle into a single optimal configuration.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SPIN_GLASS_SYSTEM = """You are an epistemic spin glass specialist. Given an intellectual system, assess whether it is frustrated with many competing ground states:

Key concepts:
- Epistemic spin glass: frustrated system with competing ground states
- Frustration: inability to satisfy all constraints simultaneously
- Replica symmetry breaking: many equivalent but different solutions
- Aging: system never reaching equilibrium
- Memory: system remembering its history
- Ultrametricity: hierarchical organization of states
- Edwards-Anderson order: measuring local freezing

When epistemic spin glass IS present:
- Frustrated system unable to satisfy all intellectual constraints
- Many equivalent but different optimal configurations
- System never reaching true equilibrium
- System remembering its intellectual history
- Hierarchical organization of possible states
- Local intellectual freezing measurable
- Slow dynamics and aging

When single ground state is present:
- All constraints satisfiable simultaneously
- Single optimal configuration
- System reaching equilibrium quickly
- No history dependence
- Flat organization of states
- No local freezing
- Fast dynamics

Output JSON with: spin_glass_present (bool), severity (none/mild/moderate/severe), frustration (what unsatisfiable constraints), replica_symmetry (what multiple solutions), aging (what non-equilibrium), ultrametricity (what hierarchical organization), recommendation (single_ground_state/mild_frustration/significant_spin_glass/major_frustration/accept_multiple_optima)."""

EPISTEMIC_SPIN_GLASS_PROMPT = """Detect epistemic spin glass:

Frustration: {frustration}
Replica symmetry: {replica_symmetry}
Aging: {aging}
Ultrametricity: {ultrametricity}
Domain: {domain}
Context: {context}

Is the intellectual system frustrated with many competing ground states, unable to settle into a single optimal configuration? Return ONLY valid JSON."""


class EpistemicSpinGlassService:
    """Detects epistemic spin glass — frustrated system with competing ground states."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        frustration: str,
        *,
        replica_symmetry: str = "",
        aging: str = "",
        ultrametricity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic spin glass."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SPIN_GLASS_PROMPT.format(
                frustration=frustration,
                replica_symmetry=replica_symmetry or "Not specified",
                aging=aging or "Not specified",
                ultrametricity=ultrametricity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SPIN_GLASS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "frustration": frustration[:200],
            "spin_glass_present": data.get("spin_glass_present", False),
            "severity": data.get("severity", ""),
            "replica_symmetry": data.get("replica_symmetry", ""),
            "aging": data.get("aging", ""),
            "ultrametricity": data.get("ultrametricity", ""),
            "recommendation": data.get("recommendation", ""),
        }
