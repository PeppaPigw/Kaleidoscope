"""EpistemicSelectiveTrustService — Epistemic Selective Trust Detection.

Detects epistemic selective trust — trusting only certain sources while
blanket-rejecting others without merit-based evaluation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SELECTIVE_TRUST_SYSTEM = """You are an epistemic selective trust specialist. Given selective trust patterns, assess selective trust:

Key concepts:
- Epistemic selective trust: trusting only certain sources blanket-rejecting others
- In-group trust: only trusting those in one's intellectual tribe
- Source-based filtering: accepting/rejecting based on source not content
- Authority worship: trusting certain authorities uncritically
- Blanket rejection: dismissing entire categories of sources
- Trust heuristics: using shortcuts instead of evaluation
- Tribal epistemology: truth determined by group membership

When epistemic selective trust IS present:
- Trusting only certain sources
- Only trusting in-group
- Filtering by source not content
- Trusting authorities uncritically
- Dismissing entire categories
- Using shortcuts not evaluation
- Truth by group membership

When no selective trust:
- Evaluating all sources on merit
- Trusting across groups
- Filtering by content quality
- Critical of all authorities
- Evaluating individually
- Careful evaluation
- Truth by evidence

Output JSON with: selective_trust_detected (bool), severity (none/mild/moderate/severe), ingroup_trust (what only trusting), blanket_rejection (what dismissing entirely), authority_worship (what trusting uncritically), tribal_epistemology (what determining by membership), recommendation (no_selective_trust/mild_source_diversification/significant_evaluation_practice/major_intensive_trust_calibration/emergency_severe_tribal_epistemology)."""

EPISTEMIC_SELECTIVE_TRUST_PROMPT = """Detect epistemic selective trust:

Ingroup trust: {ingroup_trust}
Blanket rejection: {blanket_rejection}
Authority worship: {authority_worship}
Tribal epistemology: {tribal_epistemology}
Domain: {domain}
Context: {context}

Is there trusting only certain sources while blanket-rejecting others? Return ONLY valid JSON."""


class EpistemicSelectiveTrustService:
    """Detects epistemic selective trust — trusting only certain sources."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        ingroup_trust: str,
        *,
        blanket_rejection: str = "",
        authority_worship: str = "",
        tribal_epistemology: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic selective trust."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SELECTIVE_TRUST_PROMPT.format(
                ingroup_trust=ingroup_trust,
                blanket_rejection=blanket_rejection or "Not specified",
                authority_worship=authority_worship or "Not specified",
                tribal_epistemology=tribal_epistemology or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SELECTIVE_TRUST_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "ingroup_trust": ingroup_trust[:200],
            "selective_trust_detected": data.get("selective_trust_detected", False),
            "severity": data.get("severity", ""),
            "blanket_rejection": data.get("blanket_rejection", ""),
            "authority_worship": data.get("authority_worship", ""),
            "tribal_epistemology": data.get("tribal_epistemology", ""),
            "recommendation": data.get("recommendation", ""),
        }
