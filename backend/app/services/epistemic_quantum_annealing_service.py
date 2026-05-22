"""EpistemicQuantumAnnealingService — Epistemic Quantum Annealing Detection.

Detects epistemic quantum annealing — using quantum fluctuations to
escape local optima and find the global minimum energy intellectual state.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_QUANTUM_ANNEALING_SYSTEM = """You are an epistemic quantum annealing specialist. Given an optimization pattern, assess whether quantum fluctuations help escape local optima:

Key concepts:
- Epistemic quantum annealing: using fluctuations to find global optimum
- Energy landscape: terrain of possible intellectual states
- Local minimum: trapped in suboptimal position
- Quantum fluctuation: tunneling through barriers
- Annealing schedule: gradually reducing fluctuation strength
- Ground state: lowest energy optimal solution
- Freeze-out: fluctuations too weak to escape

When epistemic quantum annealing IS present:
- Quantum fluctuations helping escape local optima
- Complex terrain of possible intellectual states
- Being trapped in suboptimal positions
- Tunneling through barriers to better states
- Gradually reducing exploration to converge
- Approaching the optimal intellectual solution
- Risk of freezing in non-optimal state

When classical optimization is present:
- Only thermal/gradient methods available
- Simple energy landscape
- No trapping in local minima
- No tunneling through barriers
- Fixed exploration rate
- Already at or near optimum
- No freeze-out risk

Output JSON with: quantum_annealing_present (bool), severity (none/mild/moderate/severe), landscape (what terrain), local_minimum (what trap), tunneling (what barrier crossing), schedule (what convergence), recommendation (classical_optimization/mild_annealing/significant_quantum_annealing/major_fluctuation_escape/optimize_annealing_schedule)."""

EPISTEMIC_QUANTUM_ANNEALING_PROMPT = """Detect epistemic quantum annealing:

Landscape: {landscape}
Local minimum: {local_minimum}
Tunneling: {tunneling}
Schedule: {schedule}
Domain: {domain}
Context: {context}

Are quantum fluctuations being used to escape local optima and find the global minimum energy intellectual state? Return ONLY valid JSON."""


class EpistemicQuantumAnnealingService:
    """Detects epistemic quantum annealing — fluctuations escaping local optima."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        landscape: str,
        *,
        local_minimum: str = "",
        tunneling: str = "",
        schedule: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic quantum annealing."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_QUANTUM_ANNEALING_PROMPT.format(
                landscape=landscape,
                local_minimum=local_minimum or "Not specified",
                tunneling=tunneling or "Not specified",
                schedule=schedule or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_QUANTUM_ANNEALING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "landscape": landscape[:200],
            "quantum_annealing_present": data.get("quantum_annealing_present", False),
            "severity": data.get("severity", ""),
            "local_minimum": data.get("local_minimum", ""),
            "tunneling": data.get("tunneling", ""),
            "schedule": data.get("schedule", ""),
            "recommendation": data.get("recommendation", ""),
        }
