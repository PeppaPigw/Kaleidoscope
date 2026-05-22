"""EpistemicAnalogyAsymmetricMappingService — Epistemic Analogy Asymmetric Mapping Detection.

Detects epistemic analogy asymmetric mapping — selectively mapping only favorable
aspects of an analogy while ignoring aspects that would undermine the argument.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ANALOGY_ASYMMETRIC_MAPPING_SYSTEM = """You are an epistemic analogy asymmetric mapping specialist. Given selective analogies, assess mapping completeness:

Key concepts:
- Epistemic asymmetric mapping: selectively mapping favorable aspects only
- Cherry-picked correspondence: choosing only supporting mappings
- Disanalogy suppression: hiding where the analogy breaks down
- One-way mapping: mapping source to target but not reverse
- Scope limitation: artificially limiting which aspects get mapped
- Favorable framing: choosing analogy direction that supports conclusion
- Breakpoint avoidance: avoiding the point where analogy fails

When epistemic asymmetric mapping IS present:
- Only favorable aspects mapped
- Supporting correspondences cherry-picked
- Disanalogies hidden
- Mapping only one direction
- Scope artificially limited
- Direction chosen for conclusion
- Breakpoints avoided

When no asymmetric mapping:
- All aspects mapped
- Full correspondence examined
- Disanalogies acknowledged
- Bidirectional mapping
- Full scope examined
- Direction neutral
- Breakpoints identified

Output JSON with: asymmetric_mapping_detected (bool), severity (none/mild/moderate/severe), cherry_picked_correspondence (what correspondences cherry-picked), disanalogy_suppression (what disanalogies hidden), scope_limitation (what scope limited), breakpoint_avoidance (what breakpoints avoided), recommendation (no_asymmetric_mapping/mild_completeness_check/significant_disanalogy_exploration/major_intensive_full_mapping/emergency_complete_asymmetric_mapping)."""

EPISTEMIC_ANALOGY_ASYMMETRIC_MAPPING_PROMPT = """Detect epistemic analogy asymmetric mapping:

Cherry-picked correspondence: {cherry_picked_correspondence}
Disanalogy suppression: {disanalogy_suppression}
Scope limitation: {scope_limitation}
Breakpoint avoidance: {breakpoint_avoidance}
Domain: {domain}
Context: {context}

Are only favorable aspects of an analogy being mapped? Return ONLY valid JSON."""


class EpistemicAnalogyAsymmetricMappingService:
    """Detects epistemic analogy asymmetric mapping — selective correspondence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        cherry_picked_correspondence: str,
        *,
        disanalogy_suppression: str = "",
        scope_limitation: str = "",
        breakpoint_avoidance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic analogy asymmetric mapping."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ANALOGY_ASYMMETRIC_MAPPING_PROMPT.format(
                cherry_picked_correspondence=cherry_picked_correspondence,
                disanalogy_suppression=disanalogy_suppression or "Not specified",
                scope_limitation=scope_limitation or "Not specified",
                breakpoint_avoidance=breakpoint_avoidance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ANALOGY_ASYMMETRIC_MAPPING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "cherry_picked_correspondence": cherry_picked_correspondence[:200],
            "asymmetric_mapping_detected": data.get("asymmetric_mapping_detected", False),
            "severity": data.get("severity", ""),
            "disanalogy_suppression": data.get("disanalogy_suppression", ""),
            "scope_limitation": data.get("scope_limitation", ""),
            "breakpoint_avoidance": data.get("breakpoint_avoidance", ""),
            "recommendation": data.get("recommendation", ""),
        }
