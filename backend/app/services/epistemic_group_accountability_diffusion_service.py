"""EpistemicGroupAccountabilityDiffusionService — Epistemic Group Accountability Diffusion Detection.

Detects epistemic group accountability diffusion — diffused accountability
reducing epistemic rigor as no individual feels responsible for accuracy.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GROUP_ACCOUNTABILITY_DIFFUSION_SYSTEM = """You are an epistemic group accountability diffusion specialist. Given accountability diffusion, assess rigor reduction:

Key concepts:
- Epistemic accountability diffusion: no individual responsible for accuracy
- Bystander effect epistemic: assuming someone else will verify
- Responsibility dilution: shared responsibility becoming no responsibility
- Free-rider epistemic: relying on others' epistemic labor
- Verification assumption: assuming others have verified
- Quality ownership gap: no one owning quality of group knowledge
- Collective negligence: group negligence from individual diffusion

When epistemic accountability diffusion IS present:
- No individual responsible for accuracy
- Bystander effect active
- Responsibility diluted
- Free-riding on others' verification
- Verification assumed not done
- Quality ownership absent
- Collective negligence emerging

When no accountability diffusion:
- Clear accountability for accuracy
- Individual responsibility maintained
- Verification explicitly assigned
- Free-riding prevented
- Quality ownership clear
- Collective responsibility structured
- Individual rigor maintained

Output JSON with: accountability_diffusion_detected (bool), severity (none/mild/moderate/severe), bystander_effect (what bystander effect), responsibility_dilution (what responsibility diluted), verification_assumption (what verification assumed), quality_ownership_gap (what quality ownership missing), recommendation (no_accountability_diffusion/mild_responsibility_assignment/significant_verification_structure/major_intensive_accountability_reform/emergency_complete_accountability_diffusion)."""

EPISTEMIC_GROUP_ACCOUNTABILITY_DIFFUSION_PROMPT = """Detect epistemic group accountability diffusion:

Bystander effect: {bystander_effect}
Responsibility dilution: {responsibility_dilution}
Verification assumption: {verification_assumption}
Quality ownership gap: {quality_ownership_gap}
Domain: {domain}
Context: {context}

Is diffused accountability reducing epistemic rigor? Return ONLY valid JSON."""


class EpistemicGroupAccountabilityDiffusionService:
    """Detects epistemic accountability diffusion — rigor reduction."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        bystander_effect: str,
        *,
        responsibility_dilution: str = "",
        verification_assumption: str = "",
        quality_ownership_gap: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic group accountability diffusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GROUP_ACCOUNTABILITY_DIFFUSION_PROMPT.format(
                bystander_effect=bystander_effect,
                responsibility_dilution=responsibility_dilution or "Not specified",
                verification_assumption=verification_assumption or "Not specified",
                quality_ownership_gap=quality_ownership_gap or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GROUP_ACCOUNTABILITY_DIFFUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "bystander_effect": bystander_effect[:200],
            "accountability_diffusion_detected": data.get("accountability_diffusion_detected", False),
            "severity": data.get("severity", ""),
            "responsibility_dilution": data.get("responsibility_dilution", ""),
            "verification_assumption": data.get("verification_assumption", ""),
            "quality_ownership_gap": data.get("quality_ownership_gap", ""),
            "recommendation": data.get("recommendation", ""),
        }
