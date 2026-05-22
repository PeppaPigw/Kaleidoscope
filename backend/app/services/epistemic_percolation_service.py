"""EpistemicPercolationService — Epistemic Percolation Detection.

Detects epistemic percolation — ideas spreading through an intellectual
network only when connectivity exceeds a critical threshold.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PERCOLATION_SYSTEM = """You are an epistemic percolation specialist. Given an intellectual network, assess whether ideas spread only above a connectivity threshold:

Key concepts:
- Epistemic percolation: spreading only above critical connectivity
- Percolation threshold: critical connectivity for spreading
- Giant component: largest connected cluster
- Phase transition: sudden shift from isolated to connected
- Bond percolation: connections enabling spread
- Site percolation: nodes enabling spread
- Cluster size distribution: how groups form

When epistemic percolation IS present:
- Ideas spreading only when connectivity exceeds threshold
- Critical connectivity level for idea propagation
- Largest cluster suddenly spanning the network
- Sudden shift from isolated pockets to connected whole
- Connections between ideas enabling spread
- Key nodes enabling propagation
- Characteristic distribution of cluster sizes

When sub-threshold isolation is present:
- Ideas not spreading regardless of connectivity
- No critical threshold observable
- No giant component forming
- No phase transition occurring
- Connections insufficient for spread
- Nodes isolated from each other
- Only small disconnected clusters

Output JSON with: percolation_present (bool), severity (none/mild/moderate/severe), threshold (what critical connectivity), giant_component (what largest cluster), phase_transition (what sudden shift), bond (what connections), recommendation (sub_threshold/mild_percolation/significant_percolation/major_threshold_crossing/increase_connectivity)."""

EPISTEMIC_PERCOLATION_PROMPT = """Detect epistemic percolation:

Threshold: {threshold}
Giant component: {giant_component}
Phase transition: {phase_transition}
Bond: {bond}
Domain: {domain}
Context: {context}

Do ideas spread through the intellectual network only when connectivity exceeds a critical threshold? Return ONLY valid JSON."""


class EpistemicPercolationService:
    """Detects epistemic percolation — spreading above critical connectivity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        threshold: str,
        *,
        giant_component: str = "",
        phase_transition: str = "",
        bond: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic percolation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PERCOLATION_PROMPT.format(
                threshold=threshold,
                giant_component=giant_component or "Not specified",
                phase_transition=phase_transition or "Not specified",
                bond=bond or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PERCOLATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "threshold": threshold[:200],
            "percolation_present": data.get("percolation_present", False),
            "severity": data.get("severity", ""),
            "giant_component": data.get("giant_component", ""),
            "phase_transition": data.get("phase_transition", ""),
            "bond": data.get("bond", ""),
            "recommendation": data.get("recommendation", ""),
        }
