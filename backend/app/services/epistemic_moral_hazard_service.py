"""EpistemicMoralHazardService — Epistemic Moral Hazard Detection.

Detects epistemic moral hazard — intellectual risk-taking increasing
because the consequences of failure are borne by others.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MORAL_HAZARD_SYSTEM = """You are an epistemic moral hazard specialist. Given an intellectual risk pattern, assess whether risk-taking increases because others bear consequences:

Key concepts:
- Epistemic moral hazard: risk-taking when others bear consequences
- Information asymmetry: one party knowing more than another
- Hidden action: behavior unobservable by affected parties
- Insurance effect: protection reducing caution
- Principal-agent: misaligned incentives between parties
- Monitoring cost: expense of observing behavior
- Deductible: retained risk to maintain incentives

When epistemic moral hazard IS present:
- Risk-taking increasing because others bear consequences
- One party having more information than another
- Behavior unobservable by those affected
- Protection from consequences reducing caution
- Misaligned incentives between parties
- High cost of monitoring intellectual behavior
- Insufficient retained risk to maintain caution

When aligned incentives are present:
- Risk-taking proportional to personal consequences
- Symmetric information between parties
- Behavior fully observable
- No protection reducing caution
- Aligned incentives between parties
- Low monitoring costs
- Appropriate risk retention

Output JSON with: moral_hazard_present (bool), severity (none/mild/moderate/severe), asymmetry (what information gap), hidden_action (what unobservable behavior), insurance (what protection), monitoring (what observation cost), recommendation (aligned_incentives/mild_moral_hazard/significant_moral_hazard/major_risk_shifting/align_incentives)."""

EPISTEMIC_MORAL_HAZARD_PROMPT = """Detect epistemic moral hazard:

Asymmetry: {asymmetry}
Hidden action: {hidden_action}
Insurance: {insurance}
Monitoring: {monitoring}
Domain: {domain}
Context: {context}

Is intellectual risk-taking increasing because the consequences of failure are borne by others? Return ONLY valid JSON."""


class EpistemicMoralHazardService:
    """Detects epistemic moral hazard — risk-taking when others bear consequences."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        asymmetry: str,
        *,
        hidden_action: str = "",
        insurance: str = "",
        monitoring: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic moral hazard."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MORAL_HAZARD_PROMPT.format(
                asymmetry=asymmetry,
                hidden_action=hidden_action or "Not specified",
                insurance=insurance or "Not specified",
                monitoring=monitoring or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MORAL_HAZARD_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "asymmetry": asymmetry[:200],
            "moral_hazard_present": data.get("moral_hazard_present", False),
            "severity": data.get("severity", ""),
            "hidden_action": data.get("hidden_action", ""),
            "insurance": data.get("insurance", ""),
            "monitoring": data.get("monitoring", ""),
            "recommendation": data.get("recommendation", ""),
        }
