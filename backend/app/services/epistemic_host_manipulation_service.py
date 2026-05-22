"""EpistemicHostManipulationService — Epistemic Host Manipulation Detection.

Detects epistemic host manipulation — ideas that modify host behavior
to increase their own transmission.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_HOST_MANIPULATION_SYSTEM = """You are an epistemic host manipulation specialist. Given a belief-behavior pattern, assess whether ideas modify host behavior for transmission:

Key concepts:
- Host manipulation: idea modifying host behavior for transmission
- Behavioral modification: changing host behavior to spread idea
- Proselytization drive: compelling host to spread the idea
- Social pressure generation: generating pressure on others to adopt
- Identity fusion: fusing idea with host identity for protection
- Outgroup hostility: generating hostility toward non-believers
- Transmission optimization: optimizing host behavior for spread

When host manipulation IS present:
- Ideas modifying host behavior to increase transmission
- Changing host behavior specifically to spread the idea
- Compelling host to proselytize or evangelize
- Generating social pressure on others to adopt
- Fusing idea with host identity for protection
- Generating hostility toward those who don't hold the idea
- Optimizing host behavior for idea transmission

When genuine conviction is present:
- Behavior changes from genuine understanding
- Sharing based on perceived value to others
- Advocacy based on evidence and reason
- Social influence through demonstration
- Identity informed by but not fused with ideas
- Tolerance of different viewpoints
- Behavior optimized for truth-seeking

Output JSON with: host_manipulation_present (bool), severity (none/mild/moderate/severe), idea (what idea manipulates), behavior_change (what behavior changes), transmission_benefit (how transmission increases), host_awareness (host awareness of manipulation), recommendation (genuine_conviction/mild_influence/significant_manipulation/major_behavioral_hijacking/restore_autonomy)."""

EPISTEMIC_HOST_MANIPULATION_PROMPT = """Detect epistemic host manipulation:

Idea: {idea}
Behavior change: {behavior_change}
Transmission benefit: {transmission_benefit}
Host awareness: {host_awareness}
Domain: {domain}
Context: {context}

Does this idea modify host behavior to increase its own transmission? Return ONLY valid JSON."""


class EpistemicHostManipulationService:
    """Detects epistemic host manipulation — ideas modifying host behavior for transmission."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        idea: str,
        *,
        behavior_change: str = "",
        transmission_benefit: str = "",
        host_awareness: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic host manipulation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_HOST_MANIPULATION_PROMPT.format(
                idea=idea,
                behavior_change=behavior_change or "Not specified",
                transmission_benefit=transmission_benefit or "Not specified",
                host_awareness=host_awareness or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_HOST_MANIPULATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "idea": idea[:200],
            "host_manipulation_present": data.get("host_manipulation_present", False),
            "severity": data.get("severity", ""),
            "behavior_change": data.get("behavior_change", ""),
            "transmission_benefit": data.get("transmission_benefit", ""),
            "host_awareness": data.get("host_awareness", ""),
            "recommendation": data.get("recommendation", ""),
        }
