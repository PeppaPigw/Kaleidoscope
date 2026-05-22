"""EpistemicQubitService — Epistemic Qubit Detection.

Detects epistemic qubit — an idea existing in superposition of multiple
states simultaneously until observation forces a definite position.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_QUBIT_SYSTEM = """You are an epistemic qubit specialist. Given an intellectual state, assess whether ideas exist in superposition until observed:

Key concepts:
- Epistemic qubit: idea in superposition of multiple states
- Superposition: existing in multiple states simultaneously
- Measurement: observation forcing a definite state
- Decoherence: environment destroying superposition
- Entanglement: ideas linked across distance
- Gate operation: transforming the qubit state
- Error correction: protecting against decoherence

When epistemic qubit IS present:
- Ideas existing in multiple states simultaneously
- Observation forcing a definite intellectual position
- Environment destroying the multi-state existence
- Ideas linked such that measuring one determines another
- Operations transforming the superposed state
- Mechanisms protecting against state collapse

When classical bit is present:
- Ideas in definite single states
- Observation revealing pre-existing state
- No environmental sensitivity
- Ideas independent of each other
- Simple state flips only
- No protection needed against collapse

Output JSON with: qubit_present (bool), severity (none/mild/moderate/severe), superposition (what multiple states), measurement (what forces collapse), decoherence (what destroys superposition), entanglement (what linkage), recommendation (classical_bit/mild_superposition/significant_qubit/major_quantum_state/maintain_coherence)."""

EPISTEMIC_QUBIT_PROMPT = """Detect epistemic qubit:

Superposition: {superposition}
Measurement: {measurement}
Decoherence: {decoherence}
Entanglement: {entanglement}
Domain: {domain}
Context: {context}

Is an idea existing in superposition of multiple states simultaneously until observation forces a definite position? Return ONLY valid JSON."""


class EpistemicQubitService:
    """Detects epistemic qubit — idea in superposition of states."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        superposition: str,
        *,
        measurement: str = "",
        decoherence: str = "",
        entanglement: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic qubit."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_QUBIT_PROMPT.format(
                superposition=superposition,
                measurement=measurement or "Not specified",
                decoherence=decoherence or "Not specified",
                entanglement=entanglement or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_QUBIT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "superposition": superposition[:200],
            "qubit_present": data.get("qubit_present", False),
            "severity": data.get("severity", ""),
            "measurement": data.get("measurement", ""),
            "decoherence": data.get("decoherence", ""),
            "entanglement": data.get("entanglement", ""),
            "recommendation": data.get("recommendation", ""),
        }
