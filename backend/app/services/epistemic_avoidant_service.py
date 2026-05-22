"""EpistemicAvoidantService — Epistemic Avoidant Detection.

Detects epistemic avoidant personality — pervasive intellectual inhibition,
feelings of inadequacy, and hypersensitivity to negative evaluation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_AVOIDANT_SYSTEM = """You are an epistemic avoidant personality specialist. Given intellectual inhibition, assess avoidant patterns:

Key concepts:
- Epistemic avoidant: pervasive intellectual inhibition
- Inadequacy feelings: believing own ideas are inferior
- Hypersensitivity: extreme reaction to intellectual criticism
- Social inhibition: avoiding intellectual exchange
- Risk aversion: refusing to share ideas unless certain of acceptance
- Self-deprecation: minimizing own intellectual contributions
- Isolation: withdrawing from intellectual community

When epistemic avoidant IS present:
- Pervasive intellectual inhibition
- Believing own ideas are inferior
- Extreme reaction to criticism
- Avoiding intellectual exchange
- Refusing to share unless certain
- Minimizing own contributions
- Withdrawing from community

When no avoidant:
- Intellectual engagement
- Realistic self-assessment
- Proportionate reaction to criticism
- Active intellectual exchange
- Willing to share ideas
- Appropriate self-valuation
- Connected to community

Output JSON with: avoidant_detected (bool), severity (none/mild/moderate/severe), inhibition_level (what restraint), inadequacy_belief (what inferiority), criticism_sensitivity (what reaction), social_withdrawal (what isolation), recommendation (no_avoidant/mild_gradual_exposure/significant_cbt/major_intensive_therapy/emergency_complete_withdrawal)."""

EPISTEMIC_AVOIDANT_PROMPT = """Detect epistemic avoidant:

Inhibition level: {inhibition_level}
Inadequacy belief: {inadequacy_belief}
Criticism sensitivity: {criticism_sensitivity}
Social withdrawal: {social_withdrawal}
Domain: {domain}
Context: {context}

Is there pervasive intellectual inhibition with feelings of inadequacy? Return ONLY valid JSON."""


class EpistemicAvoidantService:
    """Detects epistemic avoidant — pervasive intellectual inhibition."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        inhibition_level: str,
        *,
        inadequacy_belief: str = "",
        criticism_sensitivity: str = "",
        social_withdrawal: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic avoidant."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_AVOIDANT_PROMPT.format(
                inhibition_level=inhibition_level,
                inadequacy_belief=inadequacy_belief or "Not specified",
                criticism_sensitivity=criticism_sensitivity or "Not specified",
                social_withdrawal=social_withdrawal or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_AVOIDANT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "inhibition_level": inhibition_level[:200],
            "avoidant_detected": data.get("avoidant_detected", False),
            "severity": data.get("severity", ""),
            "inadequacy_belief": data.get("inadequacy_belief", ""),
            "criticism_sensitivity": data.get("criticism_sensitivity", ""),
            "social_withdrawal": data.get("social_withdrawal", ""),
            "recommendation": data.get("recommendation", ""),
        }
