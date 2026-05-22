"""EpistemicLossyCompressionService — Epistemic Lossy Compression Detection.

Detects epistemic lossy compression — ideas being compressed by
discarding details deemed unimportant, with irreversible information loss.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LOSSY_COMPRESSION_SYSTEM = """You are an epistemic lossy compression specialist. Given an intellectual simplification, assess whether important details are being irreversibly discarded:

Key concepts:
- Epistemic lossy compression: irreversible detail discarding
- Perceptual model: what details humans notice
- Quantization: reducing precision of values
- Transform coding: converting to frequency domain
- Rate-distortion: tradeoff between size and quality
- Artifact: visible damage from compression
- Psychoacoustic model: what the mind ignores

When epistemic lossy compression IS present:
- Details being discarded as unimportant
- Model of what intellectual consumers notice
- Precision being reduced in representations
- Ideas converted to different domains for compression
- Explicit tradeoff between brevity and fidelity
- Visible artifacts from over-compression
- Model of what the mind can safely ignore

When lossless representation is present:
- All details preserved
- No perceptual model needed
- Full precision maintained
- Ideas in native domain
- No brevity-fidelity tradeoff
- No compression artifacts
- Nothing safely ignorable

Output JSON with: lossy_compression_present (bool), severity (none/mild/moderate/severe), quantization (what precision loss), artifacts (what visible damage), rate_distortion (what tradeoff), perceptual_model (what is ignored), recommendation (lossless_representation/mild_compression/significant_lossy_compression/major_detail_loss/reduce_compression_ratio)."""

EPISTEMIC_LOSSY_COMPRESSION_PROMPT = """Detect epistemic lossy compression:

Quantization: {quantization}
Artifacts: {artifacts}
Rate distortion: {rate_distortion}
Perceptual model: {perceptual_model}
Domain: {domain}
Context: {context}

Are ideas being compressed by discarding details deemed unimportant, with irreversible information loss? Return ONLY valid JSON."""


class EpistemicLossyCompressionService:
    """Detects epistemic lossy compression — irreversible detail discarding."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        quantization: str,
        *,
        artifacts: str = "",
        rate_distortion: str = "",
        perceptual_model: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic lossy compression."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LOSSY_COMPRESSION_PROMPT.format(
                quantization=quantization,
                artifacts=artifacts or "Not specified",
                rate_distortion=rate_distortion or "Not specified",
                perceptual_model=perceptual_model or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LOSSY_COMPRESSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "quantization": quantization[:200],
            "lossy_compression_present": data.get("lossy_compression_present", False),
            "severity": data.get("severity", ""),
            "artifacts": data.get("artifacts", ""),
            "rate_distortion": data.get("rate_distortion", ""),
            "perceptual_model": data.get("perceptual_model", ""),
            "recommendation": data.get("recommendation", ""),
        }
