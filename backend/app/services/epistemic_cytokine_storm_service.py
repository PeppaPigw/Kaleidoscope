"""EpistemicCytokineStormService — Epistemic Cytokine Storm Detection.

Detects epistemic cytokine storm — intellectual immune system overreacting
with cascading inflammatory signals that damage the host system.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CYTOKINE_STORM_SYSTEM = """You are an epistemic cytokine storm specialist. Given an intellectual immune response, assess whether it cascades into damaging overreaction:

Key concepts:
- Epistemic cytokine storm: immune overreaction with cascading inflammatory signals
- Positive feedback loop: each signal amplifying the next
- Inflammatory cascade: chain reaction of defensive responses
- Tissue damage: collateral destruction of healthy ideas
- Hyperactivation: immune system in overdrive
- Multi-organ failure: multiple intellectual domains collapsing
- Immunomodulation: attempt to calm the storm

When epistemic cytokine storm IS present:
- Immune overreaction cascading out of control
- Each defensive signal amplifying the next
- Chain reaction of inflammatory responses
- Collateral destruction of healthy intellectual content
- Immune system in overdrive beyond proportion
- Multiple intellectual domains collapsing simultaneously
- Need to calm the overactive response

When healthy response is present:
- Proportionate immune response
- No positive feedback loops
- No cascading inflammation
- Healthy content preserved
- Measured defensive activation
- Single-domain contained response
- No modulation needed

Output JSON with: cytokine_storm_present (bool), severity (none/mild/moderate/severe), positive_feedback_loop (what amplification), inflammatory_cascade (what chain reaction), tissue_damage (what collateral destruction), hyperactivation (what overdrive), recommendation (healthy_response/mild_overreaction/significant_cytokine_storm/major_immune_cascade/restore_proportionate_response)."""

EPISTEMIC_CYTOKINE_STORM_PROMPT = """Detect epistemic cytokine storm:

Positive feedback loop: {positive_feedback_loop}
Inflammatory cascade: {inflammatory_cascade}
Tissue damage: {tissue_damage}
Hyperactivation: {hyperactivation}
Domain: {domain}
Context: {context}

Is the intellectual immune system overreacting with cascading inflammatory signals that damage the host? Return ONLY valid JSON."""


class EpistemicCytokineStormService:
    """Detects epistemic cytokine storm — immune overreaction with cascading damage."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        positive_feedback_loop: str,
        *,
        inflammatory_cascade: str = "",
        tissue_damage: str = "",
        hyperactivation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic cytokine storm."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CYTOKINE_STORM_PROMPT.format(
                positive_feedback_loop=positive_feedback_loop,
                inflammatory_cascade=inflammatory_cascade or "Not specified",
                tissue_damage=tissue_damage or "Not specified",
                hyperactivation=hyperactivation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CYTOKINE_STORM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "positive_feedback_loop": positive_feedback_loop[:200],
            "cytokine_storm_present": data.get("cytokine_storm_present", False),
            "severity": data.get("severity", ""),
            "inflammatory_cascade": data.get("inflammatory_cascade", ""),
            "tissue_damage": data.get("tissue_damage", ""),
            "hyperactivation": data.get("hyperactivation", ""),
            "recommendation": data.get("recommendation", ""),
        }
