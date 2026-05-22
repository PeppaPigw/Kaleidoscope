"""EpistemicBoundaryDissolutionService — Epistemic Boundary Dissolution Detection.

Detects epistemic boundary dissolution — loss of intellectual boundaries
where one can't distinguish own thoughts from others'.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BOUNDARY_DISSOLUTION_SYSTEM = """You are an epistemic boundary dissolution specialist. Given loss of intellectual boundaries, assess boundary dissolution:

Key concepts:
- Epistemic boundary dissolution: can't distinguish own thoughts from others'
- Thought merger: own ideas blending indistinguishably with others'
- Attribution confusion: not knowing whose idea is whose
- Intellectual absorption: absorbing others' views as own without awareness
- Identity diffusion: losing sense of own intellectual identity
- Belief contagion: catching beliefs without conscious adoption
- Cognitive fusion: merging with information sources

When epistemic boundary dissolution IS present:
- Can't distinguish own thoughts from others'
- Ideas blending indistinguishably
- Not knowing whose idea is whose
- Absorbing views without awareness
- Losing intellectual identity
- Catching beliefs unconsciously
- Merging with sources

When no boundary dissolution:
- Clear thought ownership
- Distinct ideas
- Clear attribution
- Conscious adoption
- Strong intellectual identity
- Deliberate belief formation
- Separate from sources

Output JSON with: boundary_dissolution_detected (bool), severity (none/mild/moderate/severe), thought_merger (what blending with), attribution_confusion (what can't attribute), intellectual_absorption (what absorbing without awareness), identity_diffusion (what losing identity about), recommendation (no_boundary_dissolution/mild_boundary_awareness/significant_boundary_rebuilding/major_intensive_identity_work/emergency_complete_dissolution)."""

EPISTEMIC_BOUNDARY_DISSOLUTION_PROMPT = """Detect epistemic boundary dissolution:

Thought merger: {thought_merger}
Attribution confusion: {attribution_confusion}
Intellectual absorption: {intellectual_absorption}
Identity diffusion: {identity_diffusion}
Domain: {domain}
Context: {context}

Is there loss of intellectual boundaries where own thoughts can't be distinguished from others'? Return ONLY valid JSON."""


class EpistemicBoundaryDissolutionService:
    """Detects epistemic boundary dissolution — loss of intellectual boundaries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        thought_merger: str,
        *,
        attribution_confusion: str = "",
        intellectual_absorption: str = "",
        identity_diffusion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic boundary dissolution."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BOUNDARY_DISSOLUTION_PROMPT.format(
                thought_merger=thought_merger,
                attribution_confusion=attribution_confusion or "Not specified",
                intellectual_absorption=intellectual_absorption or "Not specified",
                identity_diffusion=identity_diffusion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BOUNDARY_DISSOLUTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "thought_merger": thought_merger[:200],
            "boundary_dissolution_detected": data.get("boundary_dissolution_detected", False),
            "severity": data.get("severity", ""),
            "attribution_confusion": data.get("attribution_confusion", ""),
            "intellectual_absorption": data.get("intellectual_absorption", ""),
            "identity_diffusion": data.get("identity_diffusion", ""),
            "recommendation": data.get("recommendation", ""),
        }
