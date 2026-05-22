"""EpistemicEquivalencePrincipleService — Epistemic Equivalence Principle Detection.

Detects epistemic equivalence principle — inability to distinguish between
intellectual acceleration and being in a field of dominant ideas.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EQUIVALENCE_PRINCIPLE_SYSTEM = """You are an epistemic equivalence principle specialist. Given an intellectual experience, assess whether acceleration and gravitational field are indistinguishable:

Key concepts:
- Epistemic equivalence principle: acceleration indistinguishable from gravity
- Inertial frame: no forces acting, free intellectual float
- Accelerating frame: being pushed by external force
- Gravitational field: being pulled by massive ideas
- Local equivalence: locally cannot tell the difference
- Tidal force: difference revealing true gravity
- Geodesic: natural path through intellectual spacetime

When epistemic equivalence principle IS present:
- Cannot distinguish acceleration from gravitational pull
- Free intellectual float in absence of forces
- Being pushed by external intellectual forces
- Being pulled by massive dominant ideas
- Locally indistinguishable experiences
- Only large-scale differences revealing truth
- Natural paths through intellectual landscape

When distinguishable forces is present:
- Can clearly distinguish acceleration from gravity
- Clear identification of force sources
- External pushes clearly identified
- Gravitational pulls clearly identified
- Locally distinguishable experiences
- Differences visible at all scales
- Forced paths clearly different from natural

Output JSON with: equivalence_principle_present (bool), severity (none/mild/moderate/severe), inertial (what free float), acceleration (what external push), gravitational (what idea pull), tidal (what reveals truth), recommendation (distinguishable_forces/mild_equivalence/significant_equivalence_principle/major_indistinguishability/detect_tidal_forces)."""

EPISTEMIC_EQUIVALENCE_PRINCIPLE_PROMPT = """Detect epistemic equivalence principle:

Inertial: {inertial}
Acceleration: {acceleration}
Gravitational: {gravitational}
Tidal: {tidal}
Domain: {domain}
Context: {context}

Is there inability to distinguish between intellectual acceleration and being in a field of dominant ideas? Return ONLY valid JSON."""


class EpistemicEquivalencePrincipleService:
    """Detects epistemic equivalence principle — acceleration indistinguishable from gravity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        inertial: str,
        *,
        acceleration: str = "",
        gravitational: str = "",
        tidal: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic equivalence principle."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EQUIVALENCE_PRINCIPLE_PROMPT.format(
                inertial=inertial,
                acceleration=acceleration or "Not specified",
                gravitational=gravitational or "Not specified",
                tidal=tidal or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EQUIVALENCE_PRINCIPLE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "inertial": inertial[:200],
            "equivalence_principle_present": data.get("equivalence_principle_present", False),
            "severity": data.get("severity", ""),
            "acceleration": data.get("acceleration", ""),
            "gravitational": data.get("gravitational", ""),
            "tidal": data.get("tidal", ""),
            "recommendation": data.get("recommendation", ""),
        }
