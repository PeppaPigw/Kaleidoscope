"""EpistemicEntanglementService — Epistemic Entanglement Detection.

Detects epistemic entanglement — beliefs inappropriately linked so
changing one forces change in an unrelated other.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ENTANGLEMENT_SYSTEM = """You are an epistemic entanglement specialist. Given a belief network, assess whether beliefs are inappropriately linked:

Key concepts:
- Epistemic entanglement: beliefs inappropriately linked together
- Forced correlation: changing one belief forces change in unrelated other
- Inappropriate coupling: beliefs coupled without logical connection
- Package deal thinking: beliefs bundled as inseparable package
- Identity bundling: beliefs tied to identity rather than evidence
- Tribal epistemics: beliefs linked by group membership not logic
- Cascade vulnerability: one belief change cascading through unrelated beliefs

When epistemic entanglement IS present:
- Beliefs inappropriately linked without logical connection
- Changing one belief forces change in unrelated other
- Beliefs coupled without evidential basis for coupling
- Beliefs bundled as inseparable package deal
- Beliefs tied to identity rather than individual evidence
- Group membership determining belief correlations
- One belief change cascading through unrelated beliefs

When legitimate connection is present:
- Beliefs connected through genuine logical implication
- Related beliefs appropriately updated together
- Connections based on evidential relationships
- Beliefs grouped by shared evidence base
- Connections reflect genuine causal relationships
- Updates propagate through legitimate inference chains
- Belief network reflects actual logical structure

Output JSON with: entanglement_present (bool), severity (none/mild/moderate/severe), network (what belief network exists), coupling (what inappropriate coupling exists), mechanism (how entanglement operates), cascade (what cascades result), recommendation (legitimate_connection/mild_bundling/significant_entanglement/major_package_deal/decouple_beliefs)."""

EPISTEMIC_ENTANGLEMENT_PROMPT = """Detect epistemic entanglement:

Network: {network}
Coupling: {coupling}
Mechanism: {mechanism}
Cascade: {cascade}
Domain: {domain}
Context: {context}

Are beliefs inappropriately linked so changing one forces change in unrelated others? Return ONLY valid JSON."""


class EpistemicEntanglementService:
    """Detects epistemic entanglement — beliefs inappropriately linked."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        network: str,
        *,
        coupling: str = "",
        mechanism: str = "",
        cascade: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic entanglement."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ENTANGLEMENT_PROMPT.format(
                network=network,
                coupling=coupling or "Not specified",
                mechanism=mechanism or "Not specified",
                cascade=cascade or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ENTANGLEMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "network": network[:200],
            "entanglement_present": data.get("entanglement_present", False),
            "severity": data.get("severity", ""),
            "coupling": data.get("coupling", ""),
            "mechanism": data.get("mechanism", ""),
            "cascade": data.get("cascade", ""),
            "recommendation": data.get("recommendation", ""),
        }
