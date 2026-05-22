"""EpistemicSuperpositionService — Epistemic Superposition Detection.

Detects epistemic superposition — beliefs held in contradictory
states simultaneously without resolution.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SUPERPOSITION_SYSTEM = """You are an epistemic superposition specialist. Given a belief system, assess whether contradictory beliefs are held simultaneously without resolution:

Key concepts:
- Epistemic superposition: contradictory beliefs held simultaneously
- Unresolved contradiction: contradictions maintained without acknowledgment
- Belief duality: holding opposing positions at once
- Cognitive compartmentalization: keeping contradictions in separate compartments
- Doublethink: simultaneously accepting contradictory beliefs
- Selective activation: activating whichever belief is convenient
- Resolution avoidance: avoiding confrontation between contradictory beliefs

When epistemic superposition IS present:
- Contradictory beliefs held simultaneously without resolution
- Contradictions maintained without acknowledgment
- Opposing positions held at once without discomfort
- Contradictions kept in separate mental compartments
- Whichever belief is convenient gets activated
- Confrontation between contradictory beliefs avoided
- No effort to resolve fundamental contradictions

When nuanced thinking is present:
- Apparent contradictions reflect genuine complexity
- Tensions acknowledged and worked through
- Different contexts legitimately warrant different approaches
- Complexity held with awareness of tensions
- Contradictions recognized and being resolved
- Dialectical thinking producing synthesis
- Nuance rather than compartmentalization

Output JSON with: superposition_present (bool), severity (none/mild/moderate/severe), beliefs (what beliefs are in superposition), contradiction (what contradiction exists), compartmentalization (how contradictions are kept separate), activation (how selective activation works), recommendation (nuanced_thinking/mild_compartmentalization/significant_superposition/major_doublethink/resolve_contradictions)."""

EPISTEMIC_SUPERPOSITION_PROMPT = """Detect epistemic superposition:

Beliefs: {beliefs}
Contradiction: {contradiction}
Compartmentalization: {compartmentalization}
Activation: {activation}
Domain: {domain}
Context: {context}

Are contradictory beliefs held simultaneously without resolution? Return ONLY valid JSON."""


class EpistemicSuperpositionService:
    """Detects epistemic superposition — contradictory beliefs held simultaneously."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        beliefs: str,
        *,
        contradiction: str = "",
        compartmentalization: str = "",
        activation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic superposition."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SUPERPOSITION_PROMPT.format(
                beliefs=beliefs,
                contradiction=contradiction or "Not specified",
                compartmentalization=compartmentalization or "Not specified",
                activation=activation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SUPERPOSITION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "beliefs": beliefs[:200],
            "superposition_present": data.get("superposition_present", False),
            "severity": data.get("severity", ""),
            "contradiction": data.get("contradiction", ""),
            "compartmentalization": data.get("compartmentalization", ""),
            "activation": data.get("activation", ""),
            "recommendation": data.get("recommendation", ""),
        }
