"""EpistemicTurbulenceService — Epistemic Turbulence Detection.

Detects epistemic turbulence — chaotic knowledge flow preventing
coherent understanding from forming.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TURBULENCE_SYSTEM = """You are an epistemic turbulence specialist. Given a knowledge flow pattern, assess whether chaotic flow prevents coherent understanding:

Key concepts:
- Epistemic turbulence: chaotic knowledge flow preventing coherence
- Chaotic mixing: ideas mixing chaotically without productive synthesis
- Vortex formation: knowledge spinning in unproductive circles
- Reynolds number: threshold where smooth flow becomes turbulent
- Unpredictable flow: knowledge moving in unpredictable directions
- Energy dissipation: energy wasted in turbulent eddies
- Coherence destruction: turbulence destroying coherent understanding

When epistemic turbulence IS present:
- Knowledge flowing chaotically preventing coherent understanding
- Ideas mixing chaotically without productive synthesis
- Knowledge spinning in unproductive circles
- Flow exceeding threshold for orderly processing
- Knowledge moving in unpredictable directions
- Energy wasted in turbulent intellectual eddies
- Turbulence destroying coherent understanding

When laminar flow is present:
- Knowledge flowing smoothly and coherently
- Ideas combining productively
- Knowledge moving in productive directions
- Flow within orderly processing capacity
- Knowledge moving predictably toward understanding
- Energy efficiently directed
- Coherent understanding forming naturally

Output JSON with: turbulence_present (bool), severity (none/mild/moderate/severe), flow (what knowledge flow is turbulent), chaos (what chaos results), vortices (what unproductive circles form), coherence_loss (what coherence is destroyed), recommendation (laminar_flow/mild_turbulence/significant_chaos/major_turbulence/reduce_flow_rate)."""

EPISTEMIC_TURBULENCE_PROMPT = """Detect epistemic turbulence:

Flow: {flow}
Chaos: {chaos}
Vortices: {vortices}
Coherence loss: {coherence_loss}
Domain: {domain}
Context: {context}

Is chaotic knowledge flow preventing coherent understanding? Return ONLY valid JSON."""


class EpistemicTurbulenceService:
    """Detects epistemic turbulence — chaotic flow preventing coherence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        flow: str,
        *,
        chaos: str = "",
        vortices: str = "",
        coherence_loss: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic turbulence."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TURBULENCE_PROMPT.format(
                flow=flow,
                chaos=chaos or "Not specified",
                vortices=vortices or "Not specified",
                coherence_loss=coherence_loss or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TURBULENCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "flow": flow[:200],
            "turbulence_present": data.get("turbulence_present", False),
            "severity": data.get("severity", ""),
            "chaos": data.get("chaos", ""),
            "vortices": data.get("vortices", ""),
            "coherence_loss": data.get("coherence_loss", ""),
            "recommendation": data.get("recommendation", ""),
        }
