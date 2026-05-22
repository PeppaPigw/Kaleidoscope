"""EpistemicLocalAnesthesiaService — Epistemic Local Anesthesia Detection.

Detects epistemic local anesthesia — numbing a specific intellectual area
to allow painful procedures without general suppression.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LOCAL_ANESTHESIA_SYSTEM = """You are an epistemic local anesthesia specialist. Given need for localized intellectual numbing, assess local anesthesia:

Key concepts:
- Epistemic local anesthesia: numbing specific intellectual area
- Nerve block: blocking signal transmission in specific pathway
- Infiltration: flooding area with numbing agent
- Topical: surface-level numbing only
- Duration: how long numbness lasts
- Toxicity: risk of too much numbing agent
- Breakthrough pain: numbness wearing off during procedure

When epistemic local anesthesia IS needed:
- Painful intellectual procedure required
- Specific area needs numbing
- Signal blocking in pathway needed
- Area flooding with numbing appropriate
- Surface numbing sufficient
- Duration adequate for procedure
- Toxicity risk acceptable

When no local anesthesia needed:
- No painful procedure planned
- No specific area needs numbing
- No signal blocking needed
- No flooding required
- No surface numbing needed
- No procedure duration concern
- No numbing necessary

Output JSON with: local_anesthesia_needed (bool), severity (none/mild/moderate/severe), block_type (what numbing approach), target_area (what specific region), duration_need (what time required), toxicity_risk (what overdose danger), recommendation (no_anesthesia_needed/mild_topical/significant_infiltration/major_nerve_block/regional_block_required)."""

EPISTEMIC_LOCAL_ANESTHESIA_PROMPT = """Detect epistemic local anesthesia need:

Block type: {block_type}
Target area: {target_area}
Duration need: {duration_need}
Toxicity risk: {toxicity_risk}
Domain: {domain}
Context: {context}

Does a specific intellectual area need numbing for a painful procedure? Return ONLY valid JSON."""


class EpistemicLocalAnesthesiaService:
    """Detects epistemic local anesthesia need — numbing specific intellectual area."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        block_type: str,
        *,
        target_area: str = "",
        duration_need: str = "",
        toxicity_risk: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic local anesthesia need."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LOCAL_ANESTHESIA_PROMPT.format(
                block_type=block_type,
                target_area=target_area or "Not specified",
                duration_need=duration_need or "Not specified",
                toxicity_risk=toxicity_risk or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LOCAL_ANESTHESIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "block_type": block_type[:200],
            "local_anesthesia_needed": data.get("local_anesthesia_needed", False),
            "severity": data.get("severity", ""),
            "target_area": data.get("target_area", ""),
            "duration_need": data.get("duration_need", ""),
            "toxicity_risk": data.get("toxicity_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }
