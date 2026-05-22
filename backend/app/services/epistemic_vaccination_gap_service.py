"""EpistemicVaccinationGapService — Epistemic Vaccination Gap Detection.

Detects epistemic vaccination gaps — intellectual systems lacking protective
immunization against known threats.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_VACCINATION_GAP_SYSTEM = """You are an epistemic vaccination gap specialist. Given intellectual systems lacking protection, assess vaccination gaps:

Key concepts:
- Epistemic vaccination gap: lacking protection against known threats
- Herd immunity: community-level protection threshold
- Booster: reinforcement of waning protection
- Catch-up schedule: accelerated protection for behind systems
- Contraindication: reason not to vaccinate
- Adverse reaction: negative response to vaccination
- Seroconversion: developing actual protection after vaccination

When epistemic vaccination gaps ARE present:
- Lacking protection against known threats
- Below community protection threshold
- Waning protection needing reinforcement
- Behind schedule needing catch-up
- No valid contraindication present
- Acceptable reaction risk
- Failed to develop protection

When no vaccination gaps:
- Protected against known threats
- Above community threshold
- Protection current and strong
- On schedule
- Valid contraindications respected
- No adverse reactions
- Confirmed protection present

Output JSON with: vaccination_gap (bool), severity (none/mild/moderate/severe), missing_protections (what lacking), herd_immunity_status (what community level), booster_need (what reinforcement), catch_up_plan (what acceleration), recommendation (no_gap/mild_single_booster/significant_catch_up/major_full_series/emergency_post_exposure_prophylaxis)."""

EPISTEMIC_VACCINATION_GAP_PROMPT = """Detect epistemic vaccination gap:

Missing protections: {missing_protections}
Herd immunity status: {herd_immunity_status}
Booster need: {booster_need}
Catch-up plan: {catch_up_plan}
Domain: {domain}
Context: {context}

Is the intellectual system lacking protective immunization against known threats? Return ONLY valid JSON."""


class EpistemicVaccinationGapService:
    """Detects epistemic vaccination gaps — lacking protection against known threats."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        missing_protections: str,
        *,
        herd_immunity_status: str = "",
        booster_need: str = "",
        catch_up_plan: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic vaccination gap."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_VACCINATION_GAP_PROMPT.format(
                missing_protections=missing_protections,
                herd_immunity_status=herd_immunity_status or "Not specified",
                booster_need=booster_need or "Not specified",
                catch_up_plan=catch_up_plan or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_VACCINATION_GAP_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "missing_protections": missing_protections[:200],
            "vaccination_gap": data.get("vaccination_gap", False),
            "severity": data.get("severity", ""),
            "herd_immunity_status": data.get("herd_immunity_status", ""),
            "booster_need": data.get("booster_need", ""),
            "catch_up_plan": data.get("catch_up_plan", ""),
            "recommendation": data.get("recommendation", ""),
        }
