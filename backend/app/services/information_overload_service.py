"""InformationOverloadService — Information Overload Detection.

Detects information overload — when the volume of information
exceeds processing capacity, leading to degraded decision quality.
More information is not always better; beyond a threshold, it
causes confusion, paralysis, and worse outcomes.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

INFORMATION_OVERLOAD_SYSTEM = """You are an information overload specialist. Given a decision context, assess whether information volume is degrading decision quality:

Key concepts:
- Information overload: too much info degrades processing and decisions
- Cognitive bandwidth: limited capacity for simultaneous information
- Signal-to-noise ratio: useful info buried in irrelevant data
- Analysis paralysis: inability to decide due to too many inputs
- Satisficing threshold: when more info stops helping
- Attention allocation: spreading attention too thin
- Decision fatigue: quality degrades with volume of decisions/info

When information overload IS present:
- Decision quality declining despite more information
- Key signals lost in noise of irrelevant data
- Analysis paralysis — unable to decide due to too many inputs
- Contradictory information causing confusion rather than nuance
- Time spent gathering info exceeds value of marginal information
- Decision-maker overwhelmed and defaulting to heuristics
- Important distinctions lost in volume of detail

When information overload is NOT present:
- Information volume matched to decision complexity
- Key signals clearly identified and prioritized
- Additional information genuinely improving decision quality
- Decision-maker able to process and integrate inputs
- Clear framework for filtering relevant from irrelevant
- Diminishing returns recognized and info gathering stopped
- Appropriate level of detail for the decision at hand

Output JSON with: overload_present (bool), severity (none/mild/moderate/severe), information_volume (how much info is being processed), decision_complexity (how complex the decision is), signal_noise_ratio (ratio of useful to useless info), bottleneck (what's causing the overload), recommendation (no_overload/approaching_limit/significant_overload/severe_paralysis/simplify_and_filter)."""

INFORMATION_OVERLOAD_PROMPT = """Detect information overload:

Decision: {decision}
Information sources: {sources}
Volume: {volume}
Decision quality: {quality}
Domain: {domain}
Context: {context}

Is information volume degrading decision quality? Return ONLY valid JSON."""


class InformationOverloadService:
    """Detects information overload — when too much info degrades decisions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        sources: str = "",
        volume: str = "",
        quality: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect information overload."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=INFORMATION_OVERLOAD_PROMPT.format(
                decision=decision,
                sources=sources or "Not specified",
                volume=volume or "Not specified",
                quality=quality or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=INFORMATION_OVERLOAD_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "overload_present": data.get("overload_present", False),
            "severity": data.get("severity", ""),
            "information_volume": data.get("information_volume", ""),
            "signal_noise_ratio": data.get("signal_noise_ratio", ""),
            "bottleneck": data.get("bottleneck", ""),
            "recommendation": data.get("recommendation", ""),
        }
