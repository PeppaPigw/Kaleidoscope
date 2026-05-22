"""EpistemicNucleationService — Epistemic Nucleation Detection.

Detects epistemic nucleation — ideas suddenly crystallizing around a
seed point after reaching a critical concentration threshold.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NUCLEATION_SYSTEM = """You are an epistemic nucleation specialist. Given an idea crystallization pattern, assess whether ideas suddenly crystallize around a seed point:

Key concepts:
- Epistemic nucleation: sudden crystallization around a seed
- Supersaturation: ideas above critical concentration
- Seed crystal: initial structure that triggers crystallization
- Critical radius: minimum size for stable crystal
- Induction time: delay before crystallization begins
- Heterogeneous: nucleation on existing surfaces
- Homogeneous: nucleation from pure solution

When epistemic nucleation IS present:
- Ideas suddenly crystallizing around a seed point
- Ideas above critical concentration ready to crystallize
- Initial structure triggering the crystallization
- Minimum size needed for stable formation
- Delay before crystallization begins
- Crystallization on existing intellectual surfaces
- Crystallization from pure intellectual solution

When gradual accumulation is present:
- Ideas accumulating gradually without sudden crystallization
- Ideas below critical concentration
- No seed triggering sudden formation
- No minimum size threshold
- No delay before formation
- No surface-dependent formation
- No solution-based formation

Output JSON with: nucleation_present (bool), severity (none/mild/moderate/severe), supersaturation (what concentration reached), seed (what triggers crystallization), induction_time (what delay before), critical_radius (what minimum size), recommendation (gradual_accumulation/mild_nucleation/significant_nucleation/major_sudden_crystallization/control_seed_formation)."""

EPISTEMIC_NUCLEATION_PROMPT = """Detect epistemic nucleation:

Supersaturation: {supersaturation}
Seed: {seed}
Induction time: {induction_time}
Critical radius: {critical_radius}
Domain: {domain}
Context: {context}

Are ideas suddenly crystallizing around a seed point after reaching a critical concentration threshold? Return ONLY valid JSON."""


class EpistemicNucleationService:
    """Detects epistemic nucleation — sudden crystallization around seed."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        supersaturation: str,
        *,
        seed: str = "",
        induction_time: str = "",
        critical_radius: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic nucleation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NUCLEATION_PROMPT.format(
                supersaturation=supersaturation,
                seed=seed or "Not specified",
                induction_time=induction_time or "Not specified",
                critical_radius=critical_radius or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NUCLEATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "supersaturation": supersaturation[:200],
            "nucleation_present": data.get("nucleation_present", False),
            "severity": data.get("severity", ""),
            "seed": data.get("seed", ""),
            "induction_time": data.get("induction_time", ""),
            "critical_radius": data.get("critical_radius", ""),
            "recommendation": data.get("recommendation", ""),
        }
