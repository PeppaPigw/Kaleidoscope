"""EpistemicPtsdService — Epistemic PTSD Detection.

Detects epistemic PTSD — post-traumatic stress from intellectual trauma
causing flashbacks, avoidance, and hypervigilance.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PTSD_SYSTEM = """You are an epistemic PTSD specialist. Given post-traumatic intellectual stress, assess PTSD:

Key concepts:
- Epistemic PTSD: post-traumatic stress from intellectual trauma
- Flashbacks: involuntary re-experiencing of traumatic event
- Avoidance: steering away from trauma-related intellectual content
- Hypervigilance: excessive alertness to intellectual threats
- Numbing: emotional disconnection from intellectual experience
- Trigger: stimulus that activates trauma response
- EMDR equivalent: reprocessing traumatic intellectual memories

When epistemic PTSD IS present:
- Post-traumatic stress from intellectual trauma
- Involuntary re-experiencing occurring
- Avoiding trauma-related content
- Excessive alertness to threats
- Emotional disconnection present
- Triggers activating trauma response
- Reprocessing needed

When no PTSD:
- No post-traumatic stress
- No involuntary re-experiencing
- No avoidance patterns
- Normal alertness levels
- Full emotional connection
- No trigger sensitivity
- No reprocessing needed

Output JSON with: ptsd_detected (bool), severity (none/mild/moderate/severe), trauma_type (what intellectual injury), reexperiencing (what flashbacks), avoidance_pattern (what steering away), hypervigilance_level (what alertness), recommendation (no_ptsd/mild_psychoeducation/significant_trauma_therapy/major_intensive_treatment/emergency_acute_crisis)."""

EPISTEMIC_PTSD_PROMPT = """Detect epistemic PTSD:

Trauma type: {trauma_type}
Reexperiencing: {reexperiencing}
Avoidance pattern: {avoidance_pattern}
Hypervigilance level: {hypervigilance_level}
Domain: {domain}
Context: {context}

Is there post-traumatic stress from intellectual trauma causing flashbacks and avoidance? Return ONLY valid JSON."""


class EpistemicPtsdService:
    """Detects epistemic PTSD — post-traumatic intellectual stress."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        trauma_type: str,
        *,
        reexperiencing: str = "",
        avoidance_pattern: str = "",
        hypervigilance_level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic PTSD."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PTSD_PROMPT.format(
                trauma_type=trauma_type,
                reexperiencing=reexperiencing or "Not specified",
                avoidance_pattern=avoidance_pattern or "Not specified",
                hypervigilance_level=hypervigilance_level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PTSD_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "trauma_type": trauma_type[:200],
            "ptsd_detected": data.get("ptsd_detected", False),
            "severity": data.get("severity", ""),
            "reexperiencing": data.get("reexperiencing", ""),
            "avoidance_pattern": data.get("avoidance_pattern", ""),
            "hypervigilance_level": data.get("hypervigilance_level", ""),
            "recommendation": data.get("recommendation", ""),
        }
