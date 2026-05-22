"""EpistemicHostageTakingService — Epistemic Hostage Taking Detection.

Detects epistemic hostage taking — holding knowledge or information
hostage for leverage or control.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_HOSTAGE_SYSTEM = """You are an epistemic hostage taking specialist. Given a knowledge-sharing situation, assess whether information is being held hostage:

Key concepts:
- Epistemic hostage taking: holding knowledge hostage for leverage
- Information withholding: strategically withholding needed information
- Knowledge as leverage: using knowledge possession for power
- Conditional sharing: sharing only if demands are met
- Information ransom: demanding payment for needed knowledge
- Strategic opacity: being opaque to maintain power
- Knowledge gatekeeping: controlling access to knowledge for leverage

When epistemic hostage taking IS present:
- Knowledge held hostage for leverage
- Information strategically withheld for power
- Knowledge used as bargaining chip
- Sharing conditional on non-epistemic demands
- Information access used for control
- Opacity maintained for strategic advantage
- Knowledge gatekept for leverage not quality

When appropriate information management is present:
- Information shared appropriately for context
- Knowledge protected for legitimate reasons
- Sharing governed by relevance and timing
- Access managed for quality not power
- Opacity reflecting genuine complexity
- Gatekeeping serving knowledge quality

Output JSON with: hostage_present (bool), severity (none/mild/moderate/severe), situation (what situation exists), knowledge_held (what knowledge is held hostage), leverage_sought (what leverage is sought), mechanism (how hostage taking works), recommendation (appropriate_management/mild_withholding/significant_epistemic_hostage/major_knowledge_ransom/share_knowledge_freely)."""

EPISTEMIC_HOSTAGE_PROMPT = """Detect epistemic hostage taking:

Situation: {situation}
Knowledge held: {knowledge}
Leverage sought: {leverage}
Mechanism: {mechanism}
Domain: {domain}
Context: {context}

Is knowledge being held hostage for leverage? Return ONLY valid JSON."""


class EpistemicHostageTakingService:
    """Detects epistemic hostage taking — holding knowledge hostage for leverage."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        knowledge: str = "",
        leverage: str = "",
        mechanism: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic hostage taking."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_HOSTAGE_PROMPT.format(
                situation=situation,
                knowledge=knowledge or "Not specified",
                leverage=leverage or "Not specified",
                mechanism=mechanism or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_HOSTAGE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "hostage_present": data.get("hostage_present", False),
            "severity": data.get("severity", ""),
            "knowledge_held": data.get("knowledge_held", ""),
            "leverage_sought": data.get("leverage_sought", ""),
            "mechanism": data.get("mechanism", ""),
            "recommendation": data.get("recommendation", ""),
        }
