"""EpistemicDislocationService — Epistemic Dislocation Detection.

Detects epistemic dislocation — defects in intellectual crystal structure
that allow ideas to deform under stress rather than shatter.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DISLOCATION_SYSTEM = """You are an epistemic dislocation specialist. Given an intellectual structure pattern, assess whether defects allow deformation under stress:

Key concepts:
- Epistemic dislocation: defects allowing deformation not shattering
- Edge dislocation: extra half-plane of ideas inserted
- Screw dislocation: spiral arrangement around defect line
- Slip plane: plane along which deformation occurs
- Work hardening: deformation making further deformation harder
- Annealing: heat treatment removing dislocations
- Brittle fracture: what happens without dislocations

When epistemic dislocation IS present:
- Defects in intellectual structure allowing deformation
- Extra ideas inserted creating local distortion
- Spiral arrangements around defect lines
- Specific planes along which deformation occurs
- Deformation making further change harder
- Recovery processes removing accumulated defects
- Structure bending rather than breaking under stress

When perfect crystal is present:
- No defects in intellectual structure
- No extra ideas creating distortion
- No spiral arrangements
- No preferred deformation planes
- No work hardening from deformation
- No need for recovery processes
- Structure either holds perfectly or shatters

Output JSON with: dislocation_present (bool), severity (none/mild/moderate/severe), defect_type (what kind of dislocation), slip_plane (where deformation occurs), work_hardening (what makes change harder), annealing (what recovery process), recommendation (perfect_crystal/mild_defects/significant_dislocation/major_structural_defects/controlled_annealing)."""

EPISTEMIC_DISLOCATION_PROMPT = """Detect epistemic dislocation:

Defect type: {defect_type}
Slip plane: {slip_plane}
Work hardening: {work_hardening}
Annealing: {annealing}
Domain: {domain}
Context: {context}

Are defects in intellectual crystal structure allowing ideas to deform under stress rather than shatter? Return ONLY valid JSON."""


class EpistemicDislocationService:
    """Detects epistemic dislocation — defects allowing deformation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        defect_type: str,
        *,
        slip_plane: str = "",
        work_hardening: str = "",
        annealing: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic dislocation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DISLOCATION_PROMPT.format(
                defect_type=defect_type,
                slip_plane=slip_plane or "Not specified",
                work_hardening=work_hardening or "Not specified",
                annealing=annealing or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DISLOCATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "defect_type": defect_type[:200],
            "dislocation_present": data.get("dislocation_present", False),
            "severity": data.get("severity", ""),
            "slip_plane": data.get("slip_plane", ""),
            "work_hardening": data.get("work_hardening", ""),
            "annealing": data.get("annealing", ""),
            "recommendation": data.get("recommendation", ""),
        }
