"""EpistemicDepthIllusionService — Epistemic Depth Illusion Detection.

Detects epistemic depth illusion — surface appearance of depth
masking actual shallowness of understanding.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DEPTH_ILLUSION_SYSTEM = """You are an epistemic depth illusion specialist. Given a knowledge claim, assess whether apparent depth masks actual shallowness:

Key concepts:
- Epistemic depth illusion: appearance of depth masking shallowness
- Pseudo-profundity: appearing profound without substance
- Complexity theater: performing complexity without depth
- Jargon depth: using jargon to simulate understanding
- Surface sophistication: sophisticated surface hiding shallow core
- Depth performance: performing depth rather than having it
- Understanding theater: appearing to understand without actually doing so

When epistemic depth illusion IS present:
- Surface appearance of depth masking shallowness
- Appearing profound without actual substance
- Performing complexity without genuine depth
- Using jargon to simulate understanding
- Sophisticated surface hiding shallow core
- Performing depth rather than possessing it
- Appearing to understand without genuine comprehension

When genuine depth is present:
- Depth visible and substantive
- Profundity backed by genuine insight
- Complexity reflecting genuine understanding
- Terminology reflecting real knowledge
- Sophistication reflecting deep engagement
- Depth demonstrated through application
- Understanding proven through novel application

Output JSON with: depth_illusion_present (bool), severity (none/mild/moderate/severe), claim (what claim is made), appearance (what depth appears), reality (what shallowness exists), mechanism (how illusion is maintained), recommendation (genuine_depth/mild_superficiality/significant_depth_illusion/major_pseudo_profundity/develop_genuine_understanding)."""

EPISTEMIC_DEPTH_ILLUSION_PROMPT = """Detect epistemic depth illusion:

Claim: {claim}
Appearance: {appearance}
Reality: {reality}
Mechanism: {mechanism}
Domain: {domain}
Context: {context}

Does surface appearance of depth mask actual shallowness? Return ONLY valid JSON."""


class EpistemicDepthIllusionService:
    """Detects epistemic depth illusion — appearance of depth masking shallowness."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        appearance: str = "",
        reality: str = "",
        mechanism: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic depth illusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DEPTH_ILLUSION_PROMPT.format(
                claim=claim,
                appearance=appearance or "Not specified",
                reality=reality or "Not specified",
                mechanism=mechanism or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DEPTH_ILLUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "depth_illusion_present": data.get("depth_illusion_present", False),
            "severity": data.get("severity", ""),
            "appearance": data.get("appearance", ""),
            "reality": data.get("reality", ""),
            "mechanism": data.get("mechanism", ""),
            "recommendation": data.get("recommendation", ""),
        }
