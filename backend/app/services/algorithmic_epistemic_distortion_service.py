"""AlgorithmicEpistemicDistortionService — Algorithmic Epistemic Distortion Detection.

Detects algorithmic epistemic distortion — how algorithms shape
what we can know by filtering, ranking, and recommending information
in ways that create systematic blind spots.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ALGORITHMIC_EPISTEMIC_DISTORTION_SYSTEM = """You are an algorithmic epistemic distortion specialist. Given an information system, assess whether algorithms are distorting knowledge:

Key concepts:
- Algorithmic epistemic distortion: algorithms shaping what's knowable
- Filter bubble epistemology: algorithms creating knowledge silos
- Ranking as epistemology: what's ranked high treated as true
- Recommendation bias: algorithms reinforcing existing beliefs
- Algorithmic curation: machine decisions about what matters
- Search epistemology: findability determining knowability
- Algorithmic amplification: some knowledge amplified, some suppressed

When algorithmic epistemic distortion IS present:
- Algorithms systematically filter out important information
- Ranking creates false hierarchy of truth
- Recommendations reinforce existing beliefs
- Curation decisions invisible to users
- Findability determines what's known
- Amplification distorts importance
- Systematic blind spots created by design

When algorithmic curation is appropriate:
- Filtering serves user's genuine needs
- Ranking based on quality and relevance
- Recommendations expand rather than narrow
- Curation decisions transparent
- Multiple perspectives accessible
- Amplification proportional to importance
- Users aware of algorithmic influence

Output JSON with: distortion_present (bool), severity (none/mild/moderate/severe), system (what system is analyzed), mechanism (how algorithm distorts), blind_spots (what blind spots are created), invisible (what is made invisible), recommendation (appropriate_algorithmic_curation/mild_filter_bias/significant_algorithmic_distortion/major_epistemic_manipulation/transparent_algorithmic_curation)."""

ALGORITHMIC_EPISTEMIC_DISTORTION_PROMPT = """Detect algorithmic epistemic distortion:

System: {system}
Algorithm function: {algorithm}
Information filtered: {filtered}
User awareness: {awareness}
Domain: {domain}
Context: {context}

Are algorithms systematically distorting what can be known? Return ONLY valid JSON."""


class AlgorithmicEpistemicDistortionService:
    """Detects algorithmic epistemic distortion — algorithms shaping what's knowable."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        system: str,
        *,
        algorithm: str = "",
        filtered: str = "",
        awareness: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect algorithmic epistemic distortion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ALGORITHMIC_EPISTEMIC_DISTORTION_PROMPT.format(
                system=system,
                algorithm=algorithm or "Not specified",
                filtered=filtered or "Not specified",
                awareness=awareness or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ALGORITHMIC_EPISTEMIC_DISTORTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "system": system[:200],
            "distortion_present": data.get("distortion_present", False),
            "severity": data.get("severity", ""),
            "mechanism": data.get("mechanism", ""),
            "blind_spots": data.get("blind_spots", ""),
            "invisible": data.get("invisible", ""),
            "recommendation": data.get("recommendation", ""),
        }
