"""AutonomyUnderminingService — Autonomy Undermining Detection.

Detects autonomy undermining — systematically undermining someone's
epistemic self-trust and ability to think independently.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

AUTONOMY_UNDERMINING_SYSTEM = """You are an autonomy undermining specialist. Given an interaction pattern, assess whether someone's epistemic self-trust is being systematically undermined:

Key concepts:
- Autonomy undermining: undermining epistemic self-trust
- Confidence erosion: eroding confidence in own judgment
- Self-trust destruction: destroying trust in own thinking
- Independence suppression: suppressing independent thought
- Doubt induction: inducing doubt about own capabilities
- Competence questioning: questioning competence to undermine
- Dependency creation: creating dependency by undermining autonomy

When autonomy undermining IS present:
- Epistemic self-trust systematically undermined
- Confidence in own judgment eroded
- Trust in own thinking destroyed
- Independent thought suppressed
- Doubt about own capabilities induced
- Competence questioned to undermine not help
- Dependency created through undermining

When appropriate feedback is present:
- Feedback given to improve not undermine
- Confidence calibrated honestly
- Self-trust adjusted proportionately
- Independent thought encouraged
- Capabilities honestly assessed
- Competence feedback constructive
- Autonomy supported through feedback

Output JSON with: undermining_present (bool), severity (none/mild/moderate/severe), interaction (what interaction occurs), self_trust_targeted (what self-trust is targeted), method (how undermining works), dependency_created (what dependency results), recommendation (appropriate_feedback/mild_overcorrection/significant_autonomy_undermining/major_self_trust_destruction/support_epistemic_autonomy)."""

AUTONOMY_UNDERMINING_PROMPT = """Detect autonomy undermining:

Interaction: {interaction}
Self-trust targeted: {self_trust}
Method: {method}
Effect: {effect}
Domain: {domain}
Context: {context}

Is someone's epistemic self-trust being systematically undermined? Return ONLY valid JSON."""


class AutonomyUnderminingService:
    """Detects autonomy undermining — undermining epistemic self-trust."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        interaction: str,
        *,
        self_trust: str = "",
        method: str = "",
        effect: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect autonomy undermining."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=AUTONOMY_UNDERMINING_PROMPT.format(
                interaction=interaction,
                self_trust=self_trust or "Not specified",
                method=method or "Not specified",
                effect=effect or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=AUTONOMY_UNDERMINING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "interaction": interaction[:200],
            "undermining_present": data.get("undermining_present", False),
            "severity": data.get("severity", ""),
            "self_trust_targeted": data.get("self_trust_targeted", ""),
            "method": data.get("method", ""),
            "dependency_created": data.get("dependency_created", ""),
            "recommendation": data.get("recommendation", ""),
        }
