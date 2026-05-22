"""EpistemicEntropyIncreaseService — Epistemic Entropy Increase Detection.

Detects epistemic entropy increase — knowledge systems trending
toward disorder, losing structure and usefulness over time.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ENTROPY_INCREASE_SYSTEM = """You are an epistemic entropy specialist. Given a knowledge system, assess whether it is trending toward disorder:

Key concepts:
- Epistemic entropy increase: knowledge trending toward disorder
- Structure loss: organized knowledge becoming disorganized
- Usefulness decay: knowledge becoming less useful over time
- Information degradation: information quality degrading
- Order dissolution: ordered systems dissolving into chaos
- Irreversible degradation: degradation that cannot be reversed
- Maximum entropy: state of maximum disorder

When entropy increase IS present:
- Knowledge system trending toward disorder
- Organized knowledge becoming disorganized
- Knowledge becoming less useful over time
- Information quality degrading
- Ordered systems dissolving into chaos
- Degradation that cannot easily be reversed
- System approaching maximum disorder

When maintained order is present:
- Knowledge system maintaining structure
- Organization preserved over time
- Knowledge remaining useful
- Information quality maintained
- Order preserved through active maintenance
- Degradation prevented or reversed
- System far from maximum disorder

Output JSON with: entropy_increase (bool), severity (none/mild/moderate/severe), system (what system shows entropy), disorder (what disorder emerges), structure_loss (what structure is lost), irreversibility (how irreversible), recommendation (maintained_order/mild_entropy/significant_disorder/major_entropy_increase/restore_structure)."""

EPISTEMIC_ENTROPY_INCREASE_PROMPT = """Detect epistemic entropy increase:

System: {system}
Disorder: {disorder}
Structure loss: {structure_loss}
Irreversibility: {irreversibility}
Domain: {domain}
Context: {context}

Is the knowledge system trending toward disorder and losing structure? Return ONLY valid JSON."""


class EpistemicEntropyIncreaseService:
    """Detects epistemic entropy increase — knowledge trending toward disorder."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        system: str,
        *,
        disorder: str = "",
        structure_loss: str = "",
        irreversibility: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic entropy increase."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ENTROPY_INCREASE_PROMPT.format(
                system=system,
                disorder=disorder or "Not specified",
                structure_loss=structure_loss or "Not specified",
                irreversibility=irreversibility or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ENTROPY_INCREASE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "system": system[:200],
            "entropy_increase": data.get("entropy_increase", False),
            "severity": data.get("severity", ""),
            "disorder": data.get("disorder", ""),
            "structure_loss": data.get("structure_loss", ""),
            "irreversibility": data.get("irreversibility", ""),
            "recommendation": data.get("recommendation", ""),
        }
