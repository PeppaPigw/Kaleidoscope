"""EpistemicDualityService — Epistemic Duality Detection.

Detects epistemic duality — two seemingly different intellectual descriptions
being secretly the same theory viewed from different perspectives.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DUALITY_SYSTEM = """You are an epistemic duality specialist. Given intellectual descriptions, assess whether seemingly different theories are secretly the same:

Key concepts:
- Epistemic duality: different descriptions being the same theory
- Strong-weak duality: strong coupling in one = weak in the other
- T-duality: large radius equivalent to small radius
- S-duality: electric-magnetic interchange
- Mirror symmetry: two different geometries giving same physics
- Holographic duality: boundary theory encoding bulk
- Web of dualities: network connecting all descriptions

When epistemic duality IS present:
- Two seemingly different descriptions being the same theory
- Strong regime in one mapping to weak regime in the other
- Large scale in one equivalent to small scale in the other
- Fundamental roles interchanged between descriptions
- Different structures giving identical predictions
- Lower-dimensional theory encoding higher-dimensional one
- Network of equivalences connecting descriptions

When genuinely different theories is present:
- Descriptions being truly different theories
- No mapping between regimes
- No scale equivalence
- Roles not interchangeable
- Different structures giving different predictions
- No holographic encoding
- No equivalence network

Output JSON with: duality_present (bool), severity (none/mild/moderate/severe), strong_weak (what coupling interchange), t_duality (what scale equivalence), mirror (what geometric equivalence), holographic (what dimensional encoding), recommendation (genuinely_different/mild_duality/significant_duality/major_equivalence/exploit_dual_description)."""

EPISTEMIC_DUALITY_PROMPT = """Detect epistemic duality:

Strong-weak: {strong_weak}
T-duality: {t_duality}
Mirror: {mirror}
Holographic: {holographic}
Domain: {domain}
Context: {context}

Are two seemingly different intellectual descriptions secretly the same theory viewed from different perspectives? Return ONLY valid JSON."""


class EpistemicDualityService:
    """Detects epistemic duality — different descriptions being the same theory."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        strong_weak: str,
        *,
        t_duality: str = "",
        mirror: str = "",
        holographic: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic duality."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DUALITY_PROMPT.format(
                strong_weak=strong_weak,
                t_duality=t_duality or "Not specified",
                mirror=mirror or "Not specified",
                holographic=holographic or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DUALITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "strong_weak": strong_weak[:200],
            "duality_present": data.get("duality_present", False),
            "severity": data.get("severity", ""),
            "t_duality": data.get("t_duality", ""),
            "mirror": data.get("mirror", ""),
            "holographic": data.get("holographic", ""),
            "recommendation": data.get("recommendation", ""),
        }
