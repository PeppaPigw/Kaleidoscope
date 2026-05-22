"""EpistemicFractureService — Epistemic Fracture Detection.

Detects epistemic fracture — break in intellectual structural support
where the framework holding ideas together has cracked or shattered.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FRACTURE_SYSTEM = """You are an epistemic fracture specialist. Given intellectual structure, assess whether structural support has broken:

Key concepts:
- Epistemic fracture: break in intellectual structural support
- Stress fracture: gradual failure from repeated loading
- Comminuted fracture: structure shattered into multiple pieces
- Displacement: broken ends no longer aligned
- Callus formation: new material bridging the break
- Non-union: failure to heal the fracture
- Pathological fracture: break from weakened structure

When epistemic fracture IS present:
- Break in intellectual structural support
- Gradual failure from repeated intellectual loading
- Structure shattered into multiple pieces
- Broken ends no longer aligned
- New material attempting to bridge the break
- Failure to heal the structural break
- Break occurring in already weakened structure

When healthy structure is present:
- Intact structural support
- No stress failures
- Unified structure
- Proper alignment
- No repair needed
- No non-union concerns
- Strong healthy structure

Output JSON with: fracture_present (bool), severity (none/mild/moderate/severe), stress_fracture (what gradual failure), displacement (what misalignment), callus_formation (what repair attempt), non_union (what healing failure), recommendation (healthy_structure/mild_fracture/significant_fracture/major_structural_break/stabilize_and_heal)."""

EPISTEMIC_FRACTURE_PROMPT = """Detect epistemic fracture:

Stress fracture: {stress_fracture}
Displacement: {displacement}
Callus formation: {callus_formation}
Non-union: {non_union}
Domain: {domain}
Context: {context}

Has intellectual structural support broken, cracking the framework holding ideas together? Return ONLY valid JSON."""


class EpistemicFractureService:
    """Detects epistemic fracture — break in intellectual structural support."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        stress_fracture: str,
        *,
        displacement: str = "",
        callus_formation: str = "",
        non_union: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic fracture."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FRACTURE_PROMPT.format(
                stress_fracture=stress_fracture,
                displacement=displacement or "Not specified",
                callus_formation=callus_formation or "Not specified",
                non_union=non_union or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FRACTURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "stress_fracture": stress_fracture[:200],
            "fracture_present": data.get("fracture_present", False),
            "severity": data.get("severity", ""),
            "displacement": data.get("displacement", ""),
            "callus_formation": data.get("callus_formation", ""),
            "non_union": data.get("non_union", ""),
            "recommendation": data.get("recommendation", ""),
        }
