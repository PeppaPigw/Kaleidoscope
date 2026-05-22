"""EpistemicPartitionFunctionService — Epistemic Partition Function Detection.

Detects epistemic partition function — summing over all possible intellectual
states to determine macroscopic behavior from microscopic possibilities.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PARTITION_FUNCTION_SYSTEM = """You are an epistemic partition function specialist. Given an intellectual system, assess whether behavior is determined by summing over all possible states:

Key concepts:
- Epistemic partition function: summing over all possible states
- Microstate: individual possible configuration
- Macrostate: observable aggregate behavior
- Boltzmann weight: probability of each state
- Free energy: useful work extractable from the system
- Ensemble: collection of all possible states
- Thermodynamic limit: behavior in large systems

When epistemic partition function IS present:
- Behavior determined by summing over all possible states
- Many individual possible configurations
- Observable behavior emerging from aggregate
- Different states having different probabilities
- Useful intellectual work extractable
- Full collection of possible states identifiable
- Large-system behavior dominating

When single state is present:
- Behavior determined by single state
- Only one configuration
- No aggregation needed
- No probability distribution
- No free energy concept
- No ensemble
- No thermodynamic limit

Output JSON with: partition_function_present (bool), severity (none/mild/moderate/severe), microstate (what individual configurations), boltzmann_weight (what probability distribution), free_energy (what extractable work), ensemble (what state collection), recommendation (single_state/mild_partition/significant_partition_function/major_state_sum/compute_partition_function)."""

EPISTEMIC_PARTITION_FUNCTION_PROMPT = """Detect epistemic partition function:

Microstate: {microstate}
Boltzmann weight: {boltzmann_weight}
Free energy: {free_energy}
Ensemble: {ensemble}
Domain: {domain}
Context: {context}

Is behavior determined by summing over all possible intellectual states? Return ONLY valid JSON."""


class EpistemicPartitionFunctionService:
    """Detects epistemic partition function — summing over all possible states."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        microstate: str,
        *,
        boltzmann_weight: str = "",
        free_energy: str = "",
        ensemble: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic partition function."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PARTITION_FUNCTION_PROMPT.format(
                microstate=microstate,
                boltzmann_weight=boltzmann_weight or "Not specified",
                free_energy=free_energy or "Not specified",
                ensemble=ensemble or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PARTITION_FUNCTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "microstate": microstate[:200],
            "partition_function_present": data.get("partition_function_present", False),
            "severity": data.get("severity", ""),
            "boltzmann_weight": data.get("boltzmann_weight", ""),
            "free_energy": data.get("free_energy", ""),
            "ensemble": data.get("ensemble", ""),
            "recommendation": data.get("recommendation", ""),
        }
