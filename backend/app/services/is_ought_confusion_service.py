"""IsOughtConfusionService — Is-Ought Confusion Detection.

Detects is-ought confusion — conflating descriptive and normative
claims, sliding between facts and values without acknowledgment,
treating what is as what should be or vice versa.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

IS_OUGHT_CONFUSION_SYSTEM = """You are an is-ought confusion specialist. Given an argument, assess whether descriptive and normative claims are being conflated:

Key concepts:
- Is-ought gap: logical gap between facts and values
- Hume's guillotine: cannot derive ought from is alone
- Descriptive-normative conflation: mixing fact and value claims
- Status quo justification: what is treated as what should be
- Normative smuggling: hiding value judgments in factual claims
- Fact-value entanglement: unclear boundary between description and prescription
- Hidden normativity: prescriptive claims disguised as descriptive

When is-ought confusion IS present:
- Descriptive claims slide into normative without bridge
- Facts presented as if they entail values
- Value judgments hidden in apparently factual statements
- Status quo described as if it were normatively justified
- Normative conclusions drawn from purely descriptive premises
- 'Is' and 'ought' used interchangeably
- Prescriptive force smuggled into descriptive language

When fact-value integration is appropriate:
- Normative premises made explicit
- Bridge principles stated clearly
- Distinction between is and ought maintained
- Values acknowledged as values, facts as facts
- Thick concepts used with awareness of dual nature
- Fact-value interaction explored, not conflated
- Prescriptive conclusions clearly marked as such

Output JSON with: confusion_present (bool), severity (none/mild/moderate/severe), argument (what is argued), descriptive (what factual claims are made), normative (what value claims are made), conflation_point (where is and ought are confused), recommendation (appropriate_integration/mild_is_ought_blur/significant_conflation/major_normative_smuggling/maintain_is_ought_distinction)."""

IS_OUGHT_CONFUSION_PROMPT = """Detect is-ought confusion:

Argument: {argument}
Descriptive claims: {descriptive}
Normative claims: {normative}
Bridge principles: {bridge}
Domain: {domain}
Context: {context}

Are descriptive and normative claims being conflated without adequate bridge principles? Return ONLY valid JSON."""


class IsOughtConfusionService:
    """Detects is-ought confusion — conflating descriptive and normative claims."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        descriptive: str = "",
        normative: str = "",
        bridge: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect is-ought confusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=IS_OUGHT_CONFUSION_PROMPT.format(
                argument=argument,
                descriptive=descriptive or "Not specified",
                normative=normative or "Not specified",
                bridge=bridge or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=IS_OUGHT_CONFUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "confusion_present": data.get("confusion_present", False),
            "severity": data.get("severity", ""),
            "descriptive": data.get("descriptive", ""),
            "normative": data.get("normative", ""),
            "conflation_point": data.get("conflation_point", ""),
            "recommendation": data.get("recommendation", ""),
        }
