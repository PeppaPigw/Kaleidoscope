"""EpistemicSchizoidWithdrawalService — Epistemic Schizoid Withdrawal Detection.

Detects epistemic schizoid withdrawal — retreating from intellectual engagement
into protective isolation as a characterological pattern.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SCHIZOID_WITHDRAWAL_SYSTEM = """You are an epistemic schizoid withdrawal specialist. Given characterological retreat from intellectual engagement, assess schizoid withdrawal:

Key concepts:
- Epistemic schizoid withdrawal: characterological retreat from engagement
- Protective isolation: withdrawing to avoid intellectual harm
- Engagement avoidance: refusing to participate intellectually
- Inner retreat: going inside while appearing present
- Social intellectual withdrawal: avoiding intellectual community
- Shutdown: complete cessation of intellectual activity
- Safety through absence: feeling safe only when withdrawn

When epistemic schizoid withdrawal IS present:
- Characterological retreat from engagement
- Withdrawing to avoid harm
- Refusing to participate
- Going inside while present
- Avoiding intellectual community
- Complete cessation
- Safe only when withdrawn

When no schizoid withdrawal:
- Active engagement
- Present and participating
- Willing to engage
- Fully present
- Connected to community
- Ongoing activity
- Safe while engaged

Output JSON with: schizoid_withdrawal_detected (bool), severity (none/mild/moderate/severe), isolation_pattern (what retreating from), avoidance_trigger (what avoiding), shutdown_level (what ceasing), safety_strategy (what protecting from), recommendation (no_schizoid_withdrawal/mild_gradual_reengagement/significant_withdrawal_exploration/major_intensive_reconnection/emergency_complete_shutdown)."""

EPISTEMIC_SCHIZOID_WITHDRAWAL_PROMPT = """Detect epistemic schizoid withdrawal:

Isolation pattern: {isolation_pattern}
Avoidance trigger: {avoidance_trigger}
Shutdown level: {shutdown_level}
Safety strategy: {safety_strategy}
Domain: {domain}
Context: {context}

Is there characterological retreat from intellectual engagement into protective isolation? Return ONLY valid JSON."""


class EpistemicSchizoidWithdrawalService:
    """Detects epistemic schizoid withdrawal — characterological retreat from engagement."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        isolation_pattern: str,
        *,
        avoidance_trigger: str = "",
        shutdown_level: str = "",
        safety_strategy: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic schizoid withdrawal."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SCHIZOID_WITHDRAWAL_PROMPT.format(
                isolation_pattern=isolation_pattern,
                avoidance_trigger=avoidance_trigger or "Not specified",
                shutdown_level=shutdown_level or "Not specified",
                safety_strategy=safety_strategy or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SCHIZOID_WITHDRAWAL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "isolation_pattern": isolation_pattern[:200],
            "schizoid_withdrawal_detected": data.get("schizoid_withdrawal_detected", False),
            "severity": data.get("severity", ""),
            "avoidance_trigger": data.get("avoidance_trigger", ""),
            "shutdown_level": data.get("shutdown_level", ""),
            "safety_strategy": data.get("safety_strategy", ""),
            "recommendation": data.get("recommendation", ""),
        }
