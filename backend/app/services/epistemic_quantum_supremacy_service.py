"""EpistemicQuantumSupremacyService — Epistemic Quantum Supremacy Detection.

Detects epistemic quantum supremacy — intellectual problems that can only
be solved by quantum-like parallel exploration, not classical sequential reasoning.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_QUANTUM_SUPREMACY_SYSTEM = """You are an epistemic quantum supremacy specialist. Given an intellectual problem, assess whether it requires quantum-like parallel exploration:

Key concepts:
- Epistemic quantum supremacy: problems requiring parallel exploration
- Exponential speedup: quantum approach vastly faster than classical
- Sampling problem: generating from complex distributions
- Verification: checking quantum results classically
- Noise threshold: errors preventing supremacy
- Classical simulation: whether classical methods suffice
- Advantage boundary: where quantum surpasses classical

When epistemic quantum supremacy IS present:
- Problems requiring parallel exploration of many states
- Quantum approach vastly outperforming sequential reasoning
- Need to sample from complex intellectual distributions
- Results verifiable but not reproducible classically
- Noise threatening to eliminate the advantage
- Classical methods provably insufficient
- Clear boundary where parallel surpasses sequential

When classical sufficiency is present:
- Problems solvable by sequential reasoning
- No speedup from parallel exploration
- Simple distributions easily sampled
- Results reproducible by any method
- No noise sensitivity
- Classical methods fully sufficient
- No advantage boundary crossed

Output JSON with: quantum_supremacy_present (bool), severity (none/mild/moderate/severe), speedup (what exponential advantage), sampling (what complex distribution), verification (what classical check), noise (what error threshold), recommendation (classical_sufficient/mild_advantage/significant_quantum_supremacy/major_parallel_requirement/exploit_quantum_advantage)."""

EPISTEMIC_QUANTUM_SUPREMACY_PROMPT = """Detect epistemic quantum supremacy:

Speedup: {speedup}
Sampling: {sampling}
Verification: {verification}
Noise: {noise}
Domain: {domain}
Context: {context}

Does this intellectual problem require quantum-like parallel exploration that cannot be solved by classical sequential reasoning? Return ONLY valid JSON."""


class EpistemicQuantumSupremacyService:
    """Detects epistemic quantum supremacy — problems requiring parallel exploration."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        speedup: str,
        *,
        sampling: str = "",
        verification: str = "",
        noise: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic quantum supremacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_QUANTUM_SUPREMACY_PROMPT.format(
                speedup=speedup,
                sampling=sampling or "Not specified",
                verification=verification or "Not specified",
                noise=noise or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_QUANTUM_SUPREMACY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "speedup": speedup[:200],
            "quantum_supremacy_present": data.get("quantum_supremacy_present", False),
            "severity": data.get("severity", ""),
            "sampling": data.get("sampling", ""),
            "verification": data.get("verification", ""),
            "noise": data.get("noise", ""),
            "recommendation": data.get("recommendation", ""),
        }
