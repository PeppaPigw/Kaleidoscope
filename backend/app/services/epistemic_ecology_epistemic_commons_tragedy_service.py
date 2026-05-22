"""EpistemicEcologyEpistemicCommonsTragedyService - Epistemic Commons Tragedy Detection.

Detects tragedy of the epistemic commons where shared knowledge resources are degraded.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ECOLOGY_EPISTEMIC_COMMONS_TRAGEDY_SYSTEM = """You are an epistemic ecology epistemic commons tragedy specialist. Given commons degradation, assess whether shared knowledge resources are being degraded:

Key concepts:
- Epistemic commons tragedy: shared knowledge resources degraded by individually rational behavior
- Commons degradation: shared epistemic resources losing reliability or availability
- Free-riding on trust: exploiting shared trust without maintaining it
- Norm erosion: practices that sustain knowledge commons weakening
- Collective action failure: inability to coordinate maintenance of shared epistemic goods

When epistemic commons tragedy IS present:
- Shared knowledge resources are degraded
- Participants free-ride on trust or credibility
- Norms supporting reliable inquiry erode
- Collective action fails to maintain shared epistemic goods
- Individual incentives undermine collective knowledge capacity

When no commons tragedy:
- Shared knowledge resources are maintained
- Trust is reciprocally supported
- Epistemic norms remain effective
- Collective action sustains shared goods
- Individual incentives are aligned with commons maintenance

Output JSON with: tragedy_detected (bool), severity (none/mild/moderate/severe), free_riding_on_trust (how trust is exploited), norm_erosion (what norms are eroding), collective_action_failure (how coordination fails), recommendation (no_tragedy/mild_commons_maintenance/significant_norm_repair/major_commons_restoration/emergency_collective_action)."""

EPISTEMIC_ECOLOGY_EPISTEMIC_COMMONS_TRAGEDY_PROMPT = """Detect epistemic ecology epistemic commons tragedy:

Commons degradation: {commons_degradation}
Free-riding on trust: {free_riding_on_trust}
Norm erosion: {norm_erosion}
Collective action failure: {collective_action_failure}
Domain: {domain}
Context: {context}

Are shared knowledge resources being degraded by epistemic commons tragedy? Return ONLY valid JSON."""


class EpistemicEcologyEpistemicCommonsTragedyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        commons_degradation: str,
        *,
        free_riding_on_trust: str = "",
        norm_erosion: str = "",
        collective_action_failure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ECOLOGY_EPISTEMIC_COMMONS_TRAGEDY_PROMPT.format(
                commons_degradation=commons_degradation,
                free_riding_on_trust=free_riding_on_trust or "Not specified",
                norm_erosion=norm_erosion or "Not specified",
                collective_action_failure=collective_action_failure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ECOLOGY_EPISTEMIC_COMMONS_TRAGEDY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "commons_degradation": commons_degradation[:200],
            "tragedy_detected": data.get("tragedy_detected", False),
            "severity": data.get("severity", ""),
            "free_riding_on_trust": data.get("free_riding_on_trust", ""),
            "norm_erosion": data.get("norm_erosion", ""),
            "collective_action_failure": data.get("collective_action_failure", ""),
            "recommendation": data.get("recommendation", ""),
        }
