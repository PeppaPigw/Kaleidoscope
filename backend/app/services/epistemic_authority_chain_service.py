"""EpistemicAuthorityChainService — Epistemic Authority Chain Detection.

Detects epistemic authority chain — authority claims based on chains of
citation rather than direct evidence, where authority degrades through links.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_AUTHORITY_CHAIN_SYSTEM = """You are an epistemic authority chain specialist. Given authority chain claims, assess citation-chain authority:

Key concepts:
- Epistemic authority chain: authority based on citation chains not direct evidence
- Citation telephone: claims degrading through citation chains
- Secondary source authority: treating secondary sources as primary
- Review authority inflation: reviews treated as more authoritative than primaries
- Citation context loss: losing context through citation chains
- Authority amplification: authority growing through chain length
- Circular citation: authority manufactured through circular citation

When epistemic authority chain IS present:
- Authority based on citation chains
- Citation telephone degrading claims
- Secondary sources treated as primary
- Reviews inflated over primaries
- Context lost through chains
- Authority amplified by chain length
- Circular citation present

When no authority chain problem:
- Authority traced to primary sources
- Citation chains verified
- Primary sources consulted
- Reviews contextualized
- Context preserved through citation
- Authority proportional to evidence
- Citation networks organic

Output JSON with: authority_chain_detected (bool), severity (none/mild/moderate/severe), citation_telephone (what citation telephone), secondary_source_authority (what secondary treated as primary), citation_context_loss (what context lost), circular_citation (what circular citation), recommendation (no_authority_chain/mild_source_tracing/significant_primary_consultation/major_intensive_chain_verification/emergency_complete_authority_chain)."""

EPISTEMIC_AUTHORITY_CHAIN_PROMPT = """Detect epistemic authority chain:

Citation telephone: {citation_telephone}
Secondary source authority: {secondary_source_authority}
Citation context loss: {citation_context_loss}
Circular citation: {circular_citation}
Domain: {domain}
Context: {context}

Is authority being claimed through citation chains rather than direct evidence? Return ONLY valid JSON."""


class EpistemicAuthorityChainService:
    """Detects epistemic authority chain — citation-chain authority."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        citation_telephone: str,
        *,
        secondary_source_authority: str = "",
        citation_context_loss: str = "",
        circular_citation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic authority chain."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_AUTHORITY_CHAIN_PROMPT.format(
                citation_telephone=citation_telephone,
                secondary_source_authority=secondary_source_authority or "Not specified",
                citation_context_loss=citation_context_loss or "Not specified",
                circular_citation=circular_citation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_AUTHORITY_CHAIN_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "citation_telephone": citation_telephone[:200],
            "authority_chain_detected": data.get("authority_chain_detected", False),
            "severity": data.get("severity", ""),
            "secondary_source_authority": data.get("secondary_source_authority", ""),
            "citation_context_loss": data.get("citation_context_loss", ""),
            "circular_citation": data.get("circular_citation", ""),
            "recommendation": data.get("recommendation", ""),
        }
