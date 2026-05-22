"""EpistemicExpertEntrenchmentService — Epistemic Expert Entrenchment Detection.

Detects epistemic expert entrenchment — experts entrenched in paradigms,
unable to see alternatives due to deep investment in current frameworks.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EXPERT_ENTRENCHMENT_SYSTEM = """You are an epistemic expert entrenchment specialist. Given experts entrenched in paradigms, assess entrenchment:

Key concepts:
- Epistemic expert entrenchment: experts unable to see beyond their paradigm
- Paradigm lock-in: locked into current paradigm by investment
- Career investment bias: career built on paradigm creates resistance to change
- Theoretical commitment: deep commitment to theory prevents seeing alternatives
- Methodological rigidity: rigid adherence to established methods
- Peer reinforcement: peers reinforce entrenchment through shared paradigm
- Anomaly dismissal: dismissing anomalies that challenge the paradigm

When epistemic expert entrenchment IS present:
- Experts entrenched in paradigm
- Locked in by investment
- Career biasing judgment
- Theory commitment blinding
- Methods rigid
- Peers reinforcing
- Anomalies dismissed

When no expert entrenchment:
- Experts open to paradigm change
- Investment not biasing
- Career not constraining judgment
- Theory held provisionally
- Methods flexible
- Peers challenging constructively
- Anomalies investigated

Output JSON with: expert_entrenchment_detected (bool), severity (none/mild/moderate/severe), paradigm_lock_in (what paradigm locked into), career_investment_bias (what career investment biases), anomaly_dismissal (what anomalies dismissed), methodological_rigidity (what methods rigid), recommendation (no_expert_entrenchment/mild_openness_practice/significant_paradigm_flexibility/major_intensive_framework_questioning/emergency_complete_expert_entrenchment)."""

EPISTEMIC_EXPERT_ENTRENCHMENT_PROMPT = """Detect epistemic expert entrenchment:

Paradigm lock-in: {paradigm_lock_in}
Career investment bias: {career_investment_bias}
Anomaly dismissal: {anomaly_dismissal}
Methodological rigidity: {methodological_rigidity}
Domain: {domain}
Context: {context}

Are experts entrenched in paradigms, unable to see alternatives? Return ONLY valid JSON."""


class EpistemicExpertEntrenchmentService:
    """Detects epistemic expert entrenchment — paradigm lock-in."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        paradigm_lock_in: str,
        *,
        career_investment_bias: str = "",
        anomaly_dismissal: str = "",
        methodological_rigidity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic expert entrenchment."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EXPERT_ENTRENCHMENT_PROMPT.format(
                paradigm_lock_in=paradigm_lock_in,
                career_investment_bias=career_investment_bias or "Not specified",
                anomaly_dismissal=anomaly_dismissal or "Not specified",
                methodological_rigidity=methodological_rigidity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EXPERT_ENTRENCHMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "paradigm_lock_in": paradigm_lock_in[:200],
            "expert_entrenchment_detected": data.get("expert_entrenchment_detected", False),
            "severity": data.get("severity", ""),
            "career_investment_bias": data.get("career_investment_bias", ""),
            "anomaly_dismissal": data.get("anomaly_dismissal", ""),
            "methodological_rigidity": data.get("methodological_rigidity", ""),
            "recommendation": data.get("recommendation", ""),
        }
