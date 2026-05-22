"""ChillingEffectService — Chilling Effect Detection.

Detects chilling effects — self-censorship due to perceived
consequences of expression. When people anticipate punishment,
social sanction, or reputational damage for expressing certain
views, they self-censor — even when no explicit prohibition
exists. The effect is invisible: you can't see what wasn't said.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CHILLING_EFFECT_SYSTEM = """You are a chilling effect specialist. Given a communication environment, assess whether self-censorship is occurring due to perceived consequences:

Key concepts:
- Chilling effect: self-censorship due to anticipated consequences
- Invisible suppression: you can't see what wasn't said
- Preference falsification: publicly stating different views than held
- Spiral of silence: minority views become even more silent over time
- Overton window enforcement: social punishment for views outside bounds
- Prior restraint: censorship before expression rather than after
- Surveillance effect: being watched changes behavior

When chilling effect IS present:
- People avoid topics they have opinions on
- Views are expressed only in private/anonymous settings
- "I can't say this publicly, but..."
- Self-censorship on topics where honest discussion would be valuable
- Fear of social/professional consequences for honest expression
- Preference falsification in public while holding different private views
- Important information not shared due to anticipated backlash

When caution IS appropriate:
- The unexpressed views would genuinely cause harm
- Professional context appropriately limits personal expression
- The person is choosing tact, not suppressing truth
- Consequences are proportional to the expression
- The environment allows dissent through appropriate channels
- Self-restraint serves legitimate social functions

Output JSON with: chilling_effect_present (bool), severity (none/mild/moderate/severe), environment (what communication environment), suppressed_expression (what is being self-censored), perceived_consequence (what consequence is feared), proportionality (is the consequence proportional), information_loss (what valuable information is being suppressed), alternative_channels (are there safe channels for expression), recommendation (caution_appropriate/mild_self_censorship/significant_chilling_effect/major_expression_suppression/create_safe_channels)."""

CHILLING_EFFECT_PROMPT = """Detect chilling effect:

Environment: {environment}
Expression: {expression}
Consequences: {consequences}
Behavior change: {behavior}
Domain: {domain}
Context: {context}

Is self-censorship occurring due to perceived consequences of expression? Return ONLY valid JSON."""


class ChillingEffectService:
    """Detects chilling effects — self-censorship due to perceived consequences."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        environment: str,
        *,
        expression: str = "",
        consequences: str = "",
        behavior: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect chilling effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CHILLING_EFFECT_PROMPT.format(
                environment=environment,
                expression=expression or "Not specified",
                consequences=consequences or "Not specified",
                behavior=behavior or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CHILLING_EFFECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "environment": environment[:200],
            "chilling_effect_present": data.get("chilling_effect_present", False),
            "severity": data.get("severity", ""),
            "suppressed_expression": data.get("suppressed_expression", ""),
            "perceived_consequence": data.get("perceived_consequence", ""),
            "proportionality": data.get("proportionality", ""),
            "information_loss": data.get("information_loss", ""),
            "alternative_channels": data.get("alternative_channels", ""),
            "recommendation": data.get("recommendation", ""),
        }
