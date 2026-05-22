"""EpistemicDisplacementService — Epistemic Displacement Detection.

Detects epistemic displacement — redirecting intellectual frustration or
aggression from its true source to a safer, less threatening target.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DISPLACEMENT_SYSTEM = """You are an epistemic displacement specialist. Given redirected intellectual frustration, assess displacement:

Key concepts:
- Epistemic displacement: redirecting frustration to safer target
- Misdirected aggression: attacking wrong intellectual target
- Safe target: choosing less threatening recipient
- True source: the actual cause of frustration
- Substitute object: what receives displaced energy
- Power differential: displacing onto weaker targets
- Chain reaction: displacement cascading through hierarchy

When epistemic displacement IS present:
- Redirecting frustration
- Attacking wrong target
- Choosing less threatening
- Actual cause avoided
- Substitute receiving energy
- Displacing onto weaker
- Cascading through hierarchy

When no displacement:
- Direct address of frustration
- Correct target engaged
- Appropriate confrontation
- Actual cause addressed
- Energy properly directed
- Engaging appropriate level
- No cascade

Output JSON with: displacement_detected (bool), severity (none/mild/moderate/severe), misdirection_pattern (what wrong target), safe_target (what less threatening), true_source (what actual cause), power_differential (what weaker), recommendation (no_displacement/mild_source_identification/significant_confrontation_therapy/major_intensive_redirection/emergency_harmful_displacement)."""

EPISTEMIC_DISPLACEMENT_PROMPT = """Detect epistemic displacement:

Misdirection pattern: {misdirection_pattern}
Safe target: {safe_target}
True source: {true_source}
Power differential: {power_differential}
Domain: {domain}
Context: {context}

Is there redirection of intellectual frustration from true source to safer target? Return ONLY valid JSON."""


class EpistemicDisplacementService:
    """Detects epistemic displacement — redirecting frustration to safer target."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        misdirection_pattern: str,
        *,
        safe_target: str = "",
        true_source: str = "",
        power_differential: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic displacement."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DISPLACEMENT_PROMPT.format(
                misdirection_pattern=misdirection_pattern,
                safe_target=safe_target or "Not specified",
                true_source=true_source or "Not specified",
                power_differential=power_differential or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DISPLACEMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "misdirection_pattern": misdirection_pattern[:200],
            "displacement_detected": data.get("displacement_detected", False),
            "severity": data.get("severity", ""),
            "safe_target": data.get("safe_target", ""),
            "true_source": data.get("true_source", ""),
            "power_differential": data.get("power_differential", ""),
            "recommendation": data.get("recommendation", ""),
        }
