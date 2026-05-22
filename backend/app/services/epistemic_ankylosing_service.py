"""EpistemicAnkylosingService — Epistemic Ankylosing Spondylitis Detection.

Detects epistemic ankylosing spondylitis — progressive fusion of
intellectual spine reducing flexibility until completely rigid.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ANKYLOSING_SYSTEM = """You are an epistemic ankylosing spondylitis specialist. Given progressive intellectual spine fusion, assess AS:

Key concepts:
- Epistemic AS: progressive fusion of intellectual spine
- Bamboo spine: complete fusion into rigid rod
- Sacroiliitis: inflammation at base of spine
- Enthesitis: inflammation where structures attach to bone
- Reduced range of motion: progressive flexibility loss
- HLA-B27: genetic predisposition marker
- Exercise therapy: maintaining remaining flexibility

When epistemic AS IS present:
- Progressive fusion of intellectual spine
- Moving toward complete rigidity
- Inflammation at base of spine
- Inflammation at attachment points
- Progressive flexibility loss
- Genetic predisposition present
- Remaining flexibility needs maintenance

When no AS:
- No spinal fusion
- Normal flexibility maintained
- No base inflammation
- No attachment point inflammation
- Full range of motion
- No genetic predisposition
- No maintenance needed

Output JSON with: ankylosing_detected (bool), severity (none/mild/moderate/severe), fusion_extent (what rigidity), flexibility_remaining (what range), inflammation_sites (what attachment points), progression_rate (what speed), recommendation (no_as/mild_exercise/significant_biologic/major_combination/emergency_fracture_risk)."""

EPISTEMIC_ANKYLOSING_PROMPT = """Detect epistemic ankylosing spondylitis:

Fusion extent: {fusion_extent}
Flexibility remaining: {flexibility_remaining}
Inflammation sites: {inflammation_sites}
Progression rate: {progression_rate}
Domain: {domain}
Context: {context}

Is there progressive fusion of intellectual spine reducing flexibility until rigid? Return ONLY valid JSON."""


class EpistemicAnkylosingService:
    """Detects epistemic AS — progressive fusion of intellectual spine."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        fusion_extent: str,
        *,
        flexibility_remaining: str = "",
        inflammation_sites: str = "",
        progression_rate: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic ankylosing spondylitis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ANKYLOSING_PROMPT.format(
                fusion_extent=fusion_extent,
                flexibility_remaining=flexibility_remaining or "Not specified",
                inflammation_sites=inflammation_sites or "Not specified",
                progression_rate=progression_rate or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ANKYLOSING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "fusion_extent": fusion_extent[:200],
            "ankylosing_detected": data.get("ankylosing_detected", False),
            "severity": data.get("severity", ""),
            "flexibility_remaining": data.get("flexibility_remaining", ""),
            "inflammation_sites": data.get("inflammation_sites", ""),
            "progression_rate": data.get("progression_rate", ""),
            "recommendation": data.get("recommendation", ""),
        }
