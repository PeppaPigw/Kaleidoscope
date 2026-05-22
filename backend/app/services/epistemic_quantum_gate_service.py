"""EpistemicQuantumGateService — Epistemic Quantum Gate Detection.

Detects epistemic quantum gate — operations that transform intellectual
states through reversible unitary transformations.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_QUANTUM_GATE_SYSTEM = """You are an epistemic quantum gate specialist. Given an intellectual transformation, assess whether reversible unitary operations are being applied:

Key concepts:
- Epistemic quantum gate: reversible transformation of idea states
- Hadamard gate: creating equal superposition from definite state
- CNOT gate: conditional transformation based on control idea
- Phase gate: rotating the relative phase between states
- Toffoli gate: conditional-conditional transformation
- Universality: ability to compose any transformation
- Reversibility: every operation can be undone

When epistemic quantum gate IS present:
- Reversible transformations of intellectual states
- Creating equal superposition from definite positions
- Conditional transformations based on control ideas
- Rotating relative relationships between states
- Multi-conditional transformations
- Composable operations building complex changes
- Every transformation undoable

When irreversible operation is present:
- One-way transformations destroying information
- No superposition creation
- Unconditional transformations
- Fixed relationships between states
- Simple single-condition operations
- Non-composable isolated changes
- Permanent irreversible modifications

Output JSON with: quantum_gate_present (bool), severity (none/mild/moderate/severe), hadamard (what superposition creation), cnot (what conditional transform), phase (what rotation), reversibility (what undoability), recommendation (irreversible_operation/mild_gate/significant_quantum_gate/major_unitary_transform/compose_gate_sequence)."""

EPISTEMIC_QUANTUM_GATE_PROMPT = """Detect epistemic quantum gate:

Hadamard: {hadamard}
CNOT: {cnot}
Phase: {phase}
Reversibility: {reversibility}
Domain: {domain}
Context: {context}

Are reversible unitary transformations being applied to intellectual states? Return ONLY valid JSON."""


class EpistemicQuantumGateService:
    """Detects epistemic quantum gate — reversible state transformations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        hadamard: str,
        *,
        cnot: str = "",
        phase: str = "",
        reversibility: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic quantum gate."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_QUANTUM_GATE_PROMPT.format(
                hadamard=hadamard,
                cnot=cnot or "Not specified",
                phase=phase or "Not specified",
                reversibility=reversibility or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_QUANTUM_GATE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "hadamard": hadamard[:200],
            "quantum_gate_present": data.get("quantum_gate_present", False),
            "severity": data.get("severity", ""),
            "cnot": data.get("cnot", ""),
            "phase": data.get("phase", ""),
            "reversibility": data.get("reversibility", ""),
            "recommendation": data.get("recommendation", ""),
        }
