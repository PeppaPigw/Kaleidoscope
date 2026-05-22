"""EpistemicDisenfranchisedGriefService — Epistemic Disenfranchised Grief Detection.

Detects epistemic disenfranchised grief — intellectual loss that is not
socially recognized or validated, grief others dismiss as illegitimate.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DISENFRANCHISED_GRIEF_SYSTEM = """You are an epistemic disenfranchised grief specialist. Given unrecognized intellectual loss, assess disenfranchised grief:

Key concepts:
- Epistemic disenfranchised grief: loss not socially recognized
- Invalidation: others dismiss the loss as trivial
- Hidden mourning: grieving in secret
- Lack of support: no social acknowledgment
- Delegitimized loss: told the loss doesn't count
- Isolation: alone in grief
- Compounded pain: grief plus rejection of grief

When epistemic disenfranchised grief IS present:
- Loss not socially recognized
- Others dismiss as trivial
- Grieving in secret
- No social acknowledgment
- Told loss doesn't count
- Alone in grief
- Pain compounded by rejection

When no disenfranchised grief:
- Loss recognized
- Others validate
- Open mourning
- Social support present
- Loss acknowledged
- Community in grief
- Pain not compounded

Output JSON with: disenfranchised_grief_detected (bool), severity (none/mild/moderate/severe), invalidation_source (what dismissal), hidden_mourning (what secret grief), support_deficit (what lacking), delegitimization (what rejection), recommendation (no_disenfranchised_grief/mild_validation_seeking/significant_grief_advocacy/major_intensive_support/emergency_complete_isolation)."""

EPISTEMIC_DISENFRANCHISED_GRIEF_PROMPT = """Detect epistemic disenfranchised grief:

Invalidation source: {invalidation_source}
Hidden mourning: {hidden_mourning}
Support deficit: {support_deficit}
Delegitimization: {delegitimization}
Domain: {domain}
Context: {context}

Is there intellectual loss that is not socially recognized or validated? Return ONLY valid JSON."""


class EpistemicDisenfranchisedGriefService:
    """Detects epistemic disenfranchised grief — unrecognized intellectual loss."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        invalidation_source: str,
        *,
        hidden_mourning: str = "",
        support_deficit: str = "",
        delegitimization: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic disenfranchised grief."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DISENFRANCHISED_GRIEF_PROMPT.format(
                invalidation_source=invalidation_source,
                hidden_mourning=hidden_mourning or "Not specified",
                support_deficit=support_deficit or "Not specified",
                delegitimization=delegitimization or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DISENFRANCHISED_GRIEF_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "invalidation_source": invalidation_source[:200],
            "disenfranchised_grief_detected": data.get("disenfranchised_grief_detected", False),
            "severity": data.get("severity", ""),
            "hidden_mourning": data.get("hidden_mourning", ""),
            "support_deficit": data.get("support_deficit", ""),
            "delegitimization": data.get("delegitimization", ""),
            "recommendation": data.get("recommendation", ""),
        }
