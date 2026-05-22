"""EpistemicCommunicationAuthorityInflationService — Epistemic Communication Authority Inflation Detection.

Detects epistemic communication authority inflation — inflating authority
of claims through communication chains.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMMUNICATION_AUTHORITY_INFLATION_SYSTEM = """You are an epistemic communication authority inflation specialist. Given inflated authority through communication, assess authority inflation:

Key concepts:
- Epistemic communication authority inflation: claims gaining authority through retelling
- Source upgrading: sources upgraded in retelling (blog becomes study)
- Certainty escalation: uncertain claims becoming certain through chain
- Expert attribution creep: claims attributed to increasingly authoritative sources
- Consensus manufacturing through repetition: repetition creating false consensus
- Citation chain inflation: authority inflating through citation chains
- Institutional authority transfer: claims gaining institutional backing they lack

When epistemic communication authority inflation IS present:
- Authority inflated through communication
- Sources upgraded
- Certainty escalated
- Expert attribution creeping
- Consensus manufactured by repetition
- Citation chains inflating
- Institutional authority transferred

When no authority inflation:
- Authority maintained accurately
- Sources preserved
- Certainty calibrated
- Attribution accurate
- Consensus genuine
- Citations direct
- Institutional backing genuine

Output JSON with: authority_inflation_detected (bool), severity (none/mild/moderate/severe), source_upgrading (what sources upgraded), certainty_escalation (what certainty escalated), expert_attribution_creep (what attribution creeping), consensus_by_repetition (what consensus manufactured), recommendation (no_authority_inflation/mild_source_checking/significant_authority_deflation/major_intensive_provenance_tracking/emergency_complete_authority_inflation)."""

EPISTEMIC_COMMUNICATION_AUTHORITY_INFLATION_PROMPT = """Detect epistemic communication authority inflation:

Source upgrading: {source_upgrading}
Certainty escalation: {certainty_escalation}
Expert attribution creep: {expert_attribution_creep}
Consensus by repetition: {consensus_by_repetition}
Domain: {domain}
Context: {context}

Is authority of claims being inflated through communication chains? Return ONLY valid JSON."""


class EpistemicCommunicationAuthorityInflationService:
    """Detects epistemic communication authority inflation — false authority."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        source_upgrading: str,
        *,
        certainty_escalation: str = "",
        expert_attribution_creep: str = "",
        consensus_by_repetition: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic communication authority inflation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMMUNICATION_AUTHORITY_INFLATION_PROMPT.format(
                source_upgrading=source_upgrading,
                certainty_escalation=certainty_escalation or "Not specified",
                expert_attribution_creep=expert_attribution_creep or "Not specified",
                consensus_by_repetition=consensus_by_repetition or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMMUNICATION_AUTHORITY_INFLATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "source_upgrading": source_upgrading[:200],
            "authority_inflation_detected": data.get("authority_inflation_detected", False),
            "severity": data.get("severity", ""),
            "certainty_escalation": data.get("certainty_escalation", ""),
            "expert_attribution_creep": data.get("expert_attribution_creep", ""),
            "consensus_by_repetition": data.get("consensus_by_repetition", ""),
            "recommendation": data.get("recommendation", ""),
        }
