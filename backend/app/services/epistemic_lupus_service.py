"""EpistemicLupusService — Epistemic Lupus Detection.

Detects epistemic lupus — systemic autoimmune attack on multiple
intellectual organs simultaneously with unpredictable flares.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LUPUS_SYSTEM = """You are an epistemic lupus specialist. Given systemic autoimmune intellectual attack, assess lupus:

Key concepts:
- Epistemic lupus: systemic autoimmune attack on multiple organs
- Multi-organ involvement: attacking many systems simultaneously
- Flare-remission cycle: unpredictable worsening and improvement
- Butterfly rash: characteristic visible surface pattern
- Antinuclear antibodies: immune system targeting own core
- Photosensitivity: worsening with exposure to scrutiny
- Nephritis: kidney/filtering organ involvement

When epistemic lupus IS present:
- Systemic attack on multiple organs
- Many systems affected simultaneously
- Unpredictable flares occurring
- Characteristic surface patterns visible
- Immune system targeting own core
- Worsening with exposure to scrutiny
- Filtering organs involved

When no lupus:
- No systemic attack
- Single system if any
- Predictable course
- No characteristic patterns
- Immune system not self-targeting
- Normal scrutiny tolerance
- Filtering organs healthy

Output JSON with: lupus_detected (bool), severity (none/mild/moderate/severe), organ_involvement (what systems attacked), flare_pattern (what unpredictability), autoantibody_status (what self-targeting), photosensitivity (what scrutiny response), recommendation (no_lupus/mild_monitoring/significant_antimalarial/major_immunosuppression/emergency_organ_threatening)."""

EPISTEMIC_LUPUS_PROMPT = """Detect epistemic lupus:

Organ involvement: {organ_involvement}
Flare pattern: {flare_pattern}
Autoantibody status: {autoantibody_status}
Photosensitivity: {photosensitivity}
Domain: {domain}
Context: {context}

Is there systemic autoimmune attack on multiple intellectual organs with unpredictable flares? Return ONLY valid JSON."""


class EpistemicLupusService:
    """Detects epistemic lupus — systemic autoimmune attack on multiple organs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        organ_involvement: str,
        *,
        flare_pattern: str = "",
        autoantibody_status: str = "",
        photosensitivity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic lupus."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LUPUS_PROMPT.format(
                organ_involvement=organ_involvement,
                flare_pattern=flare_pattern or "Not specified",
                autoantibody_status=autoantibody_status or "Not specified",
                photosensitivity=photosensitivity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LUPUS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "organ_involvement": organ_involvement[:200],
            "lupus_detected": data.get("lupus_detected", False),
            "severity": data.get("severity", ""),
            "flare_pattern": data.get("flare_pattern", ""),
            "autoantibody_status": data.get("autoantibody_status", ""),
            "photosensitivity": data.get("photosensitivity", ""),
            "recommendation": data.get("recommendation", ""),
        }
