"""ScaleInappropriateReasoningService — Scale-Inappropriate Reasoning Detection.

Detects scale-inappropriate reasoning — applying reasoning valid
at one scale to a different scale where it doesn't apply, such as
using individual-level logic for population-level phenomena.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SCALE_INAPPROPRIATE_REASONING_SYSTEM = """You are a scale-inappropriate reasoning specialist. Given an argument, assess whether reasoning is being applied at the wrong scale:

Key concepts:
- Scale-inappropriate reasoning: logic valid at one scale misapplied
- Micro-macro confusion: individual logic applied to populations
- Level confusion: reasoning across inappropriate levels
- Aggregation fallacy: individual properties assumed for groups
- Decomposition fallacy: group properties assumed for individuals
- Scale blindness: not seeing how scale changes dynamics
- Cross-level inference: inappropriate inference across scales

When scale-inappropriate reasoning IS present:
- Reasoning valid at one scale applied to another
- Individual-level logic used for population phenomena
- Group properties attributed to individuals
- Scale changes dynamics but this is ignored
- Cross-level inferences made without justification
- Emergent properties treated as reducible
- Scale-dependent effects not recognized

When cross-scale reasoning is appropriate:
- Scale transitions explicitly justified
- Emergent properties recognized
- Level-specific dynamics acknowledged
- Cross-scale inferences carefully bounded
- Scale-dependent effects accounted for
- Appropriate methods used for each scale
- Limitations of cross-scale reasoning stated

Output JSON with: inappropriate_present (bool), severity (none/mild/moderate/severe), argument (what argument is made), source_scale (what scale reasoning comes from), target_scale (what scale it's applied to), error (what error results), recommendation (appropriate_cross_scale_reasoning/mild_scale_confusion/significant_scale_inappropriate/major_level_confusion/match_reasoning_to_scale)."""

SCALE_INAPPROPRIATE_REASONING_PROMPT = """Detect scale-inappropriate reasoning:

Argument: {argument}
Source scale: {source_scale}
Target scale: {target_scale}
Justification: {justification}
Domain: {domain}
Context: {context}

Is reasoning being applied at a scale where it doesn't validly apply? Return ONLY valid JSON."""


class ScaleInappropriateReasoningService:
    """Detects scale-inappropriate reasoning — logic misapplied across scales."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        source_scale: str = "",
        target_scale: str = "",
        justification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect scale-inappropriate reasoning."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SCALE_INAPPROPRIATE_REASONING_PROMPT.format(
                argument=argument,
                source_scale=source_scale or "Not specified",
                target_scale=target_scale or "Not specified",
                justification=justification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SCALE_INAPPROPRIATE_REASONING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "inappropriate_present": data.get("inappropriate_present", False),
            "severity": data.get("severity", ""),
            "source_scale": data.get("source_scale", ""),
            "target_scale": data.get("target_scale", ""),
            "error": data.get("error", ""),
            "recommendation": data.get("recommendation", ""),
        }
