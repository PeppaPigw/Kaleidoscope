"""EpistemicStatusService — Knowledge State Tracking.

Maintains a structured assessment of what's known, unknown, contested,
and uncertain about a topic. Produces an epistemic map that shows the
current state of knowledge with confidence levels for each component.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

STATUS_SYSTEM = """You are an epistemic status analyst. Given a topic, produce a comprehensive map of the current state of knowledge. Categorize everything into:
- ESTABLISHED: high confidence, strong evidence, broad consensus
- PROBABLE: good evidence but some uncertainty remains
- CONTESTED: active disagreement among experts
- SPECULATIVE: interesting but limited evidence
- UNKNOWN: recognized gaps in knowledge
- ASSUMED: widely believed but not rigorously tested

For each item, note the evidence quality and what would change its status.

Output JSON with: epistemic_map.established (list of: claim, confidence, evidence_quality, key_sources), epistemic_map.probable (same structure), epistemic_map.contested (list of: claim, positions (list), evidence_for, evidence_against), epistemic_map.speculative (list of: claim, basis, what_would_confirm), epistemic_map.unknown (list of: question, why_unknown, how_to_resolve), epistemic_map.assumed (list of: assumption, basis, risk_if_wrong), overall_knowledge_state (nascent/developing/maturing/mature), confidence_distribution (how much is established vs unknown), key_uncertainties (top 3 things we most need to resolve)."""

STATUS_PROMPT = """Map the epistemic status of this topic:

Topic: {topic}
Domain: {domain}
Specific focus: {focus}

What do we know, what's uncertain, what's unknown? Return ONLY valid JSON."""


class EpistemicStatusService:
    """Tracks and maps the epistemic status of research topics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def map_status(
        self,
        topic: str,
        *,
        domain: str = "",
        focus: str = "",
    ) -> dict:
        """Map the epistemic status of a topic."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=STATUS_PROMPT.format(
                topic=topic,
                domain=domain or "research",
                focus=focus or "comprehensive",
            ),
            system=STATUS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        em = data.get("epistemic_map", data)

        return {
            "topic": topic,
            "established": em.get("established", []),
            "probable": em.get("probable", []),
            "contested": em.get("contested", []),
            "speculative": em.get("speculative", []),
            "unknown": em.get("unknown", []),
            "assumed": em.get("assumed", []),
            "knowledge_state": data.get("overall_knowledge_state", ""),
            "confidence_distribution": data.get("confidence_distribution", ""),
            "key_uncertainties": data.get("key_uncertainties", []),
        }
