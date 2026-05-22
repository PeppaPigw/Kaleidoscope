"""EpistemicCognitiveTunnelingService — Epistemic Cognitive Tunneling Detection.

Detects epistemic cognitive tunneling — narrowing attention under load
and missing critical information outside the tunnel.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COGNITIVE_TUNNELING_SYSTEM = """You are an epistemic cognitive tunneling specialist. Given narrowing attention under load, assess cognitive tunneling:

Key concepts:
- Epistemic cognitive tunneling: narrowing attention under load missing critical info
- Tunnel vision: seeing only what is directly ahead
- Peripheral blindness: missing information at the edges
- Stress narrowing: stress causing attention to narrow
- Urgency tunnel: urgency creating tunnel vision
- Focus lock: locked onto one thing unable to see others
- Context blindness: blind to broader context under pressure

When epistemic cognitive tunneling IS present:
- Attention narrowed under load
- Tunnel vision active
- Peripheral information missed
- Stress narrowing attention
- Urgency creating tunnel
- Focus locked on one thing
- Context invisible

When no cognitive tunneling:
- Attention appropriately broad
- Vision panoramic
- Peripheral information noticed
- Stress managed without narrowing
- Urgency without tunnel
- Focus flexible
- Context visible

Output JSON with: cognitive_tunneling_detected (bool), severity (none/mild/moderate/severe), tunnel_vision (what tunnel vision focused on), peripheral_blindness (what missed at periphery), stress_narrowing (what stress narrowing about), urgency_tunnel (what urgency creating tunnel about), recommendation (no_cognitive_tunneling/mild_broadening_practice/significant_peripheral_recovery/major_intensive_context_restoration/emergency_complete_cognitive_tunneling)."""

EPISTEMIC_COGNITIVE_TUNNELING_PROMPT = """Detect epistemic cognitive tunneling:

Tunnel vision: {tunnel_vision}
Peripheral blindness: {peripheral_blindness}
Stress narrowing: {stress_narrowing}
Urgency tunnel: {urgency_tunnel}
Domain: {domain}
Context: {context}

Is attention narrowing under load and missing critical information? Return ONLY valid JSON."""


class EpistemicCognitiveTunnelingService:
    """Detects epistemic cognitive tunneling — narrowing attention under load."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        tunnel_vision: str,
        *,
        peripheral_blindness: str = "",
        stress_narrowing: str = "",
        urgency_tunnel: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic cognitive tunneling."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COGNITIVE_TUNNELING_PROMPT.format(
                tunnel_vision=tunnel_vision,
                peripheral_blindness=peripheral_blindness or "Not specified",
                stress_narrowing=stress_narrowing or "Not specified",
                urgency_tunnel=urgency_tunnel or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COGNITIVE_TUNNELING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "tunnel_vision": tunnel_vision[:200],
            "cognitive_tunneling_detected": data.get("cognitive_tunneling_detected", False),
            "severity": data.get("severity", ""),
            "peripheral_blindness": data.get("peripheral_blindness", ""),
            "stress_narrowing": data.get("stress_narrowing", ""),
            "urgency_tunnel": data.get("urgency_tunnel", ""),
            "recommendation": data.get("recommendation", ""),
        }
