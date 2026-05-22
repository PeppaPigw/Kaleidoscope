"""EpistemicSpinalCompressionService — Epistemic Spinal Compression Detection.

Detects epistemic spinal compression — central intellectual support structure
under excessive load, risking collapse of the core framework.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SPINAL_COMPRESSION_SYSTEM = """You are an epistemic spinal compression specialist. Given central intellectual support, assess whether excessive load threatens collapse:

Key concepts:
- Epistemic spinal compression: central support under excessive load
- Vertebral body collapse: individual support units failing
- Disc herniation: cushioning material extruding under pressure
- Nerve impingement: compressed support affecting downstream function
- Kyphosis: forward curvature from compression
- Decompression surgery: relieving pressure on central structure
- Load redistribution: shifting weight to prevent further collapse

When epistemic spinal compression IS present:
- Central intellectual support under excessive load
- Individual support units failing under pressure
- Cushioning material extruding between supports
- Compressed structure affecting downstream function
- Forward curvature from accumulated compression
- Need for pressure relief interventions
- Weight shifting to prevent further collapse

When healthy spine is present:
- Central support handling load well
- All support units intact
- Cushioning material contained
- No downstream impingement
- Normal curvature maintained
- No decompression needed
- Balanced load distribution

Output JSON with: spinal_compression_present (bool), severity (none/mild/moderate/severe), vertebral_collapse (what unit failure), disc_herniation (what cushion extrusion), nerve_impingement (what downstream effect), kyphosis (what curvature), recommendation (healthy_spine/mild_compression/significant_spinal_compression/major_central_collapse/decompress_and_redistribute)."""

EPISTEMIC_SPINAL_COMPRESSION_PROMPT = """Detect epistemic spinal compression:

Vertebral collapse: {vertebral_collapse}
Disc herniation: {disc_herniation}
Nerve impingement: {nerve_impingement}
Kyphosis: {kyphosis}
Domain: {domain}
Context: {context}

Is the central intellectual support structure under excessive load risking collapse? Return ONLY valid JSON."""


class EpistemicSpinalCompressionService:
    """Detects epistemic spinal compression — central support under excessive load."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        vertebral_collapse: str,
        *,
        disc_herniation: str = "",
        nerve_impingement: str = "",
        kyphosis: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic spinal compression."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SPINAL_COMPRESSION_PROMPT.format(
                vertebral_collapse=vertebral_collapse,
                disc_herniation=disc_herniation or "Not specified",
                nerve_impingement=nerve_impingement or "Not specified",
                kyphosis=kyphosis or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SPINAL_COMPRESSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "vertebral_collapse": vertebral_collapse[:200],
            "spinal_compression_present": data.get("spinal_compression_present", False),
            "severity": data.get("severity", ""),
            "disc_herniation": data.get("disc_herniation", ""),
            "nerve_impingement": data.get("nerve_impingement", ""),
            "kyphosis": data.get("kyphosis", ""),
            "recommendation": data.get("recommendation", ""),
        }
