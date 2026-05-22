"""EpistemicVortexService — Epistemic Vortex Detection.

Detects epistemic vortex — ideas caught in self-reinforcing circular
flows that trap intellectual energy in rotation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_VORTEX_SYSTEM = """You are an epistemic vortex specialist. Given an idea circulation pattern, assess whether ideas are caught in self-reinforcing circular flows:

Key concepts:
- Epistemic vortex: self-reinforcing circular idea flows
- Angular momentum: rotational energy of the idea flow
- Core: center of the vortex where pressure is lowest
- Entrainment: ideas pulled into the rotation
- Dissipation: gradual loss of rotational energy
- Vortex shedding: periodic release of trapped ideas
- Turbulence: chaotic breakdown of organized rotation

When epistemic vortex IS present:
- Ideas caught in self-reinforcing circular flows
- Rotational energy maintaining the circulation
- Low-pressure center drawing ideas inward
- Ideas pulled into the rotation involuntarily
- Gradual loss of energy from the rotation
- Periodic release of trapped ideas
- Chaotic breakdown when rotation becomes unstable

When linear flow is present:
- Ideas moving in straight lines
- No rotational energy
- No low-pressure center
- No involuntary entrainment
- No energy loss from rotation
- No periodic releases
- Stable, predictable movement

Output JSON with: vortex_present (bool), severity (none/mild/moderate/severe), momentum (what rotational energy), core (what center draws ideas), entrainment (what gets pulled in), dissipation (what energy is lost), recommendation (linear_flow/mild_circulation/significant_vortex/major_rotational_trap/break_circular_flow)."""

EPISTEMIC_VORTEX_PROMPT = """Detect epistemic vortex:

Momentum: {momentum}
Core: {core}
Entrainment: {entrainment}
Dissipation: {dissipation}
Domain: {domain}
Context: {context}

Are ideas caught in self-reinforcing circular flows that trap intellectual energy in rotation? Return ONLY valid JSON."""


class EpistemicVortexService:
    """Detects epistemic vortex — self-reinforcing circular idea flows."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        momentum: str,
        *,
        core: str = "",
        entrainment: str = "",
        dissipation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic vortex."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_VORTEX_PROMPT.format(
                momentum=momentum,
                core=core or "Not specified",
                entrainment=entrainment or "Not specified",
                dissipation=dissipation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_VORTEX_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "momentum": momentum[:200],
            "vortex_present": data.get("vortex_present", False),
            "severity": data.get("severity", ""),
            "core": data.get("core", ""),
            "entrainment": data.get("entrainment", ""),
            "dissipation": data.get("dissipation", ""),
            "recommendation": data.get("recommendation", ""),
        }
