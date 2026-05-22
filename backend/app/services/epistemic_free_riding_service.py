"""EpistemicFreeRidingService — Epistemic Free Riding Detection.

Detects epistemic free riding — benefiting from the epistemic
commons (shared knowledge, verification norms, trust) without
contributing to its maintenance or quality.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FREE_RIDING_SYSTEM = """You are an epistemic free riding specialist. Given a knowledge practice, assess whether it free-rides on epistemic infrastructure without contributing:

Key concepts:
- Epistemic commons: shared knowledge, norms, trust, verification
- Free riding: benefiting without contributing to maintenance
- Citation without verification: using claims without checking
- Trust exploitation: leveraging institutional trust without earning it
- Peer review avoidance: claiming authority without subjecting to scrutiny
- Replication crisis: benefiting from assumed replication without replicating
- Epistemic labor: work of verifying, checking, maintaining knowledge quality

When epistemic free riding IS present:
- Claims made without verification effort
- Institutional trust leveraged without meeting standards
- Others' epistemic labor used without reciprocation
- Peer review or scrutiny avoided while claiming authority
- Knowledge commons degraded by low-quality contributions
- Verification burden shifted to others
- Benefits of epistemic norms taken while violating them

When epistemic contribution is present:
- Claims verified before propagation
- Standards met or exceeded
- Epistemic labor contributed (verification, review, replication)
- Trust earned through demonstrated reliability
- Knowledge commons maintained or improved
- Scrutiny welcomed and responded to
- Verification burden shared fairly

Output JSON with: free_riding_present (bool), severity (none/mild/moderate/severe), practice (what knowledge practice), commons_used (what epistemic commons is leveraged), contribution_absent (what epistemic labor is missing), trust_exploited (what trust is leveraged without earning), recommendation (epistemic_contributor/mild_free_riding/significant_exploitation/major_commons_degradation/contribute_verification)."""

EPISTEMIC_FREE_RIDING_PROMPT = """Detect epistemic free riding:

Practice: {practice}
Claims made: {claims}
Verification done: {verification}
Standards met: {standards}
Domain: {domain}
Context: {context}

Is this practice free-riding on epistemic commons without contributing? Return ONLY valid JSON."""


class EpistemicFreeRidingService:
    """Detects epistemic free riding — benefiting from epistemic commons without contributing."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        practice: str,
        *,
        claims: str = "",
        verification: str = "",
        standards: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic free riding."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FREE_RIDING_PROMPT.format(
                practice=practice,
                claims=claims or "Not specified",
                verification=verification or "Not specified",
                standards=standards or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FREE_RIDING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "practice": practice[:200],
            "free_riding_present": data.get("free_riding_present", False),
            "severity": data.get("severity", ""),
            "commons_used": data.get("commons_used", ""),
            "contribution_absent": data.get("contribution_absent", ""),
            "trust_exploited": data.get("trust_exploited", ""),
            "recommendation": data.get("recommendation", ""),
        }
