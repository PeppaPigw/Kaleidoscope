"""EpistemicVirtualParticleService — Epistemic Virtual Particle Detection.

Detects epistemic virtual particle — transient ideas that mediate intellectual
forces between concepts without being directly observable themselves.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_VIRTUAL_PARTICLE_SYSTEM = """You are an epistemic virtual particle specialist. Given an intellectual interaction, assess whether transient ideas mediate forces between concepts:

Key concepts:
- Epistemic virtual particle: transient ideas mediating intellectual forces
- Off-shell: not satisfying normal energy-momentum relation
- Exchange force: interaction mediated by virtual exchange
- Uncertainty principle: brief existence allowed by energy-time uncertainty
- Force carrier: specific virtual particle for each force type
- Vacuum polarization: virtual pairs screening the charge
- Self-energy: particle interacting with its own virtual cloud

When epistemic virtual particle IS present:
- Transient ideas mediating forces between concepts
- Ideas not satisfying normal intellectual constraints
- Interactions mediated by brief exchanges
- Brief existence allowed by uncertainty
- Specific mediators for each type of intellectual force
- Virtual pairs screening the true strength
- Ideas interacting with their own virtual cloud

When direct interaction is present:
- No mediating transient ideas
- All ideas satisfying normal constraints
- Direct interactions without exchange
- No uncertainty-enabled existence
- No specific force carriers
- No screening effects
- No self-interaction clouds

Output JSON with: virtual_particle_present (bool), severity (none/mild/moderate/severe), off_shell (what constraint violation), exchange_force (what mediated interaction), uncertainty (what brief existence), vacuum_polarization (what screening), recommendation (direct_interaction/mild_virtual/significant_virtual_particle/major_mediation/identify_force_carriers)."""

EPISTEMIC_VIRTUAL_PARTICLE_PROMPT = """Detect epistemic virtual particle:

Off shell: {off_shell}
Exchange force: {exchange_force}
Uncertainty: {uncertainty}
Vacuum polarization: {vacuum_polarization}
Domain: {domain}
Context: {context}

Are transient ideas mediating intellectual forces between concepts without being directly observable themselves? Return ONLY valid JSON."""


class EpistemicVirtualParticleService:
    """Detects epistemic virtual particle — transient ideas mediating intellectual forces."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        off_shell: str,
        *,
        exchange_force: str = "",
        uncertainty: str = "",
        vacuum_polarization: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic virtual particle."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_VIRTUAL_PARTICLE_PROMPT.format(
                off_shell=off_shell,
                exchange_force=exchange_force or "Not specified",
                uncertainty=uncertainty or "Not specified",
                vacuum_polarization=vacuum_polarization or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_VIRTUAL_PARTICLE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "off_shell": off_shell[:200],
            "virtual_particle_present": data.get("virtual_particle_present", False),
            "severity": data.get("severity", ""),
            "exchange_force": data.get("exchange_force", ""),
            "uncertainty": data.get("uncertainty", ""),
            "vacuum_polarization": data.get("vacuum_polarization", ""),
            "recommendation": data.get("recommendation", ""),
        }
