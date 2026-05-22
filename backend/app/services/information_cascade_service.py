"""InformationCascadeService — Information Cascade Detection.

Detects information cascades — situations where people follow others'
actions rather than their own private information, leading to herding
behavior that can be rational individually but collectively fragile.
Bikhchandani, Hirshleifer & Welch (1992).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

INFORMATION_CASCADE_SYSTEM = """You are an information cascade specialist. Given a decision-making pattern, assess whether an information cascade is occurring — people following others rather than their own information:

Key concepts (Bikhchandani, Hirshleifer & Welch, 1992):
- Information cascade: ignoring private info to follow observed actions
- Herding: rational imitation that aggregates poorly
- Fragility: cascades can reverse suddenly with new public information
- Sequential decision-making: later actors observe earlier choices
- Private vs public information: what you know vs what you see others do
- Rational herding: individually rational but collectively suboptimal
- Cascade breakage: when new information shatters the cascade

When information cascade IS present:
- People are following others' choices rather than their own assessment
- Private information is being suppressed in favor of observed behavior
- "Everyone else is doing it" as primary justification
- Sequential decisions show herding pattern
- Dissenting private information is not being expressed
- The consensus is fragile and could reverse suddenly
- People would choose differently if they couldn't observe others

When following others IS appropriate:
- Others genuinely have more information or expertise
- The observed behavior reflects aggregated private information
- Independent assessment confirms the popular choice
- The person has considered their own information and still agrees
- The decision accounts for the possibility of cascade
- Diversity of information sources is maintained
- The person can articulate reasons beyond "others are doing it"

Output JSON with: information_cascade_present (bool), severity (none/mild/moderate/severe), decision (what decision is being made), herding_pattern (evidence of herding), private_information (what private info is suppressed), fragility (how fragile is the consensus), independence (are decisions independent), recommendation (decision_independent/mild_herding/significant_information_cascade/major_fragile_consensus/express_private_information)."""

INFORMATION_CASCADE_PROMPT = """Detect information cascade:

Decision pattern: {decision}
Herding evidence: {herding}
Private information: {private_info}
Independence: {independence}
Domain: {domain}
Context: {context}

Are people following others' actions rather than their own information? Return ONLY valid JSON."""


class InformationCascadeService:
    """Detects information cascades — herding behavior suppressing private information."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        herding: str = "",
        private_info: str = "",
        independence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect information cascade."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=INFORMATION_CASCADE_PROMPT.format(
                decision=decision,
                herding=herding or "Not specified",
                private_info=private_info or "Not specified",
                independence=independence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=INFORMATION_CASCADE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "information_cascade_present": data.get("information_cascade_present", False),
            "severity": data.get("severity", ""),
            "herding_pattern": data.get("herding_pattern", ""),
            "private_information": data.get("private_information", ""),
            "fragility": data.get("fragility", ""),
            "recommendation": data.get("recommendation", ""),
        }
