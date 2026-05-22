"""DisagreementSuppressionService — Disagreement Suppression Detection.

Detects disagreement suppression — mechanisms that prevent
disagreement from being expressed or heard, creating false
appearance of consensus through silencing.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DISAGREEMENT_SUPPRESSION_SYSTEM = """You are a disagreement suppression specialist. Given a situation, assess whether mechanisms are preventing disagreement from being expressed:

Key concepts:
- Disagreement suppression: preventing dissent from being expressed
- Chilling effect: fear preventing expression of disagreement
- Social pressure: conformity pressure silencing dissent
- Institutional suppression: organizational mechanisms silencing critics
- False consensus through silence: agreement assumed from lack of dissent
- Voice suppression: mechanisms preventing speaking up
- Exit over voice: people leaving rather than disagreeing

When disagreement suppression IS present:
- Mechanisms prevent expression of disagreement
- Social costs of dissent discourage speaking up
- Institutional structures silence critics
- Absence of disagreement mistaken for consensus
- Fear prevents honest expression
- Dissent punished formally or informally
- Only agreement is safe to express

When consensus is genuine:
- Disagreement possible but not present
- Safe channels for dissent exist and are used
- Absence of disagreement reflects genuine agreement
- Dissent expressed without punishment
- Multiple perspectives actively sought
- Disagreement welcomed and engaged with
- Consensus tested through devil's advocacy

Output JSON with: suppression_present (bool), severity (none/mild/moderate/severe), situation (what situation exists), mechanism (what suppresses disagreement), false_consensus (what false consensus results), cost_of_dissent (what dissent costs), recommendation (genuine_consensus/mild_conformity_pressure/significant_disagreement_suppression/major_silencing/create_safe_dissent_channels)."""

DISAGREEMENT_SUPPRESSION_PROMPT = """Detect disagreement suppression:

Situation: {situation}
Consensus claimed: {consensus}
Dissent channels: {channels}
Cost of disagreement: {cost}
Domain: {domain}
Context: {context}

Are mechanisms preventing disagreement from being expressed, creating false consensus? Return ONLY valid JSON."""


class DisagreementSuppressionService:
    """Detects disagreement suppression — mechanisms preventing dissent."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        consensus: str = "",
        channels: str = "",
        cost: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect disagreement suppression."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DISAGREEMENT_SUPPRESSION_PROMPT.format(
                situation=situation,
                consensus=consensus or "Not specified",
                channels=channels or "Not specified",
                cost=cost or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DISAGREEMENT_SUPPRESSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "suppression_present": data.get("suppression_present", False),
            "severity": data.get("severity", ""),
            "mechanism": data.get("mechanism", ""),
            "false_consensus": data.get("false_consensus", ""),
            "cost_of_dissent": data.get("cost_of_dissent", ""),
            "recommendation": data.get("recommendation", ""),
        }
