"""EpistemicBridgeCollapseService — Epistemic Bridge Collapse Detection.

Detects epistemic bridge collapse — loss of connections between
knowledge domains that previously enabled cross-domain understanding.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BRIDGE_COLLAPSE_SYSTEM = """You are an epistemic bridge collapse specialist. Given a knowledge landscape, assess whether connections between domains are being lost:

Key concepts:
- Epistemic bridge collapse: loss of cross-domain connections
- Interdisciplinary breakdown: breakdown of interdisciplinary understanding
- Siloization: knowledge becoming siloed and disconnected
- Translation loss: loss of ability to translate between domains
- Boundary hardening: boundaries between domains becoming impermeable
- Cross-pollination failure: failure of ideas to cross domain boundaries
- Integration decay: decay of previously integrated understanding

When epistemic bridge collapse IS present:
- Connections between knowledge domains being lost
- Interdisciplinary understanding breaking down
- Knowledge becoming increasingly siloed
- Translation between domains failing
- Boundaries between domains hardening
- Cross-pollination of ideas failing
- Previously integrated understanding decaying

When healthy specialization is present:
- Specialization with maintained connections
- Interdisciplinary bridges actively maintained
- Knowledge specialized but connected
- Translation between domains functioning
- Boundaries permeable to relevant ideas
- Cross-pollination actively supported
- Integration maintained alongside depth

Output JSON with: collapse_present (bool), severity (none/mild/moderate/severe), domains (what domains are disconnecting), bridge_lost (what connection is lost), consequence (what understanding is lost), cause (why collapse occurs), recommendation (healthy_specialization/mild_siloization/significant_bridge_collapse/major_domain_disconnection/maintain_cross_domain_bridges)."""

EPISTEMIC_BRIDGE_COLLAPSE_PROMPT = """Detect epistemic bridge collapse:

Domains: {domains}
Bridge lost: {bridge}
Consequence: {consequence}
Cause: {cause}
Domain: {domain}
Context: {context}

Are connections between knowledge domains being lost? Return ONLY valid JSON."""


class EpistemicBridgeCollapseService:
    """Detects epistemic bridge collapse — loss of cross-domain connections."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        domains: str,
        *,
        bridge: str = "",
        consequence: str = "",
        cause: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic bridge collapse."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BRIDGE_COLLAPSE_PROMPT.format(
                domains=domains,
                bridge=bridge or "Not specified",
                consequence=consequence or "Not specified",
                cause=cause or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BRIDGE_COLLAPSE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "domains": domains[:200],
            "collapse_present": data.get("collapse_present", False),
            "severity": data.get("severity", ""),
            "bridge_lost": data.get("bridge_lost", ""),
            "consequence": data.get("consequence", ""),
            "cause": data.get("cause", ""),
            "recommendation": data.get("recommendation", ""),
        }
