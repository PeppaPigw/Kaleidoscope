"""EpistemicShannonEntropyService — Epistemic Shannon Entropy Detection.

Detects epistemic Shannon entropy — measuring the information content
and uncertainty in intellectual communications.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SHANNON_ENTROPY_SYSTEM = """You are an epistemic Shannon entropy specialist. Given an intellectual communication, assess its information content and uncertainty:

Key concepts:
- Epistemic Shannon entropy: information content measurement
- Bit: fundamental unit of intellectual surprise
- Redundancy: repeated information reducing entropy
- Channel capacity: maximum transmittable information
- Noise: corruption during transmission
- Compression: removing redundancy without loss
- Mutual information: shared content between messages

When epistemic Shannon entropy IS present:
- High information content per intellectual unit
- Each element providing genuine surprise
- Low redundancy in communication
- Channel approaching capacity limits
- Noise corrupting transmitted ideas
- Opportunity for compression without loss
- Shared information between intellectual channels

When low entropy is present:
- Low information content per unit
- Predictable repetitive elements
- High redundancy throughout
- Channel far below capacity
- Clean transmission without noise
- Already compressed or incompressible
- No shared information between channels

Output JSON with: shannon_entropy_present (bool), severity (none/mild/moderate/severe), bits (what information content), redundancy (what repetition), channel_capacity (what limit), noise (what corruption), recommendation (low_entropy/mild_information/significant_shannon_entropy/major_information_density/optimize_channel_capacity)."""

EPISTEMIC_SHANNON_ENTROPY_PROMPT = """Detect epistemic Shannon entropy:

Bits: {bits}
Redundancy: {redundancy}
Channel capacity: {channel_capacity}
Noise: {noise}
Domain: {domain}
Context: {context}

Is there high information content and uncertainty in this intellectual communication? Return ONLY valid JSON."""


class EpistemicShannonEntropyService:
    """Detects epistemic Shannon entropy — information content measurement."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        bits: str,
        *,
        redundancy: str = "",
        channel_capacity: str = "",
        noise: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic Shannon entropy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SHANNON_ENTROPY_PROMPT.format(
                bits=bits,
                redundancy=redundancy or "Not specified",
                channel_capacity=channel_capacity or "Not specified",
                noise=noise or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SHANNON_ENTROPY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "bits": bits[:200],
            "shannon_entropy_present": data.get("shannon_entropy_present", False),
            "severity": data.get("severity", ""),
            "redundancy": data.get("redundancy", ""),
            "channel_capacity": data.get("channel_capacity", ""),
            "noise": data.get("noise", ""),
            "recommendation": data.get("recommendation", ""),
        }
