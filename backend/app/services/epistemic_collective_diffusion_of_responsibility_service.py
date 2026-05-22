"""EpistemicCollectiveDiffusionOfResponsibilityService — Epistemic Collective Diffusion Of Responsibility Detection.

Detects epistemic collective diffusion of responsibility — group settings
where responsibility for checking, knowing, or correcting is diluted.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COLLECTIVE_DIFFUSION_OF_RESPONSIBILITY_SYSTEM = """You are an epistemic collective diffusion of responsibility specialist. Given group knowledge practices, assess whether responsibility for knowing, checking, or correcting is being diluted:

Key concepts:
- Epistemic diffusion of responsibility: no one owns knowing or checking
- Responsibility dilution: responsibility spread so thin it disappears
- Bystander effect: members assume someone else will intervene
- Accountability gap: no clear owner for epistemic failures
- Free rider problem: members benefit from knowledge work without contributing
- Collective negligence: shared passivity around verification
- Ownership ambiguity: unclear who must investigate or correct

When epistemic diffusion of responsibility IS present:
- Responsibility for knowing is diluted
- Members wait for someone else to check
- Accountability gaps persist
- Free riding on others' epistemic labor occurs
- Verification work is deferred
- Ownership of correction is ambiguous
- Errors persist because no one acts

When no diffusion:
- Epistemic responsibility is assigned
- Members intervene when needed
- Accountability for failures is clear
- Knowledge labor is shared fairly
- Verification work is performed
- Correction ownership is explicit
- Errors are actively addressed

Output JSON with: diffusion_of_responsibility_detected (bool), severity (none/mild/moderate/severe), bystander_effect (what intervention is deferred), accountability_gap (what ownership is missing), free_rider_problem (what knowledge labor is avoided), recommendation (no_diffusion/mild_owner_clarification/significant_accountability_assignment/major_verification_redesign/emergency_restore_epistemic_ownership)."""

EPISTEMIC_COLLECTIVE_DIFFUSION_OF_RESPONSIBILITY_PROMPT = """Detect epistemic collective diffusion of responsibility:

Responsibility dilution: {responsibility_dilution}
Bystander effect: {bystander_effect}
Accountability gap: {accountability_gap}
Free rider problem: {free_rider_problem}
Domain: {domain}
Context: {context}

Is epistemic responsibility being diffused across the group? Return ONLY valid JSON."""


class EpistemicCollectiveDiffusionOfResponsibilityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        responsibility_dilution: str,
        *,
        bystander_effect: str = "",
        accountability_gap: str = "",
        free_rider_problem: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COLLECTIVE_DIFFUSION_OF_RESPONSIBILITY_PROMPT.format(
                responsibility_dilution=responsibility_dilution,
                bystander_effect=bystander_effect or "Not specified",
                accountability_gap=accountability_gap or "Not specified",
                free_rider_problem=free_rider_problem or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COLLECTIVE_DIFFUSION_OF_RESPONSIBILITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "responsibility_dilution": responsibility_dilution[:200],
            "diffusion_of_responsibility_detected": data.get(
                "diffusion_of_responsibility_detected", False
            ),
            "severity": data.get("severity", ""),
            "bystander_effect": data.get("bystander_effect", ""),
            "accountability_gap": data.get("accountability_gap", ""),
            "free_rider_problem": data.get("free_rider_problem", ""),
            "recommendation": data.get("recommendation", ""),
        }
