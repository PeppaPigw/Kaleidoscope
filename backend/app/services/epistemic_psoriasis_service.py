"""EpistemicPsoriasisService — Epistemic Psoriasis Detection.

Detects epistemic psoriasis — autoimmune overproduction of intellectual
surface cells creating thick scaly patches of rigid thinking.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PSORIASIS_SYSTEM = """You are an epistemic psoriasis specialist. Given autoimmune intellectual overproduction, assess psoriasis:

Key concepts:
- Epistemic psoriasis: autoimmune overproduction of surface cells
- Plaque formation: thick scaly patches of rigid thinking
- Turnover rate: accelerated production of surface material
- Autoimmune trigger: immune system attacking own tissue
- Biologics: targeted immune modulation
- Phototherapy: light-based treatment
- Remission: periods of reduced activity

When epistemic psoriasis IS present:
- Autoimmune overproduction occurring
- Thick scaly patches forming
- Accelerated surface material production
- Immune system attacking own tissue
- No targeted modulation in place
- No light-based treatment
- No remission periods

When no psoriasis:
- Normal surface cell production
- No plaque formation
- Normal turnover rate
- Immune system functioning properly
- No modulation needed
- No treatment required
- Stable condition

Output JSON with: psoriasis_detected (bool), severity (none/mild/moderate/severe), plaque_pattern (what rigid patches), turnover_rate (what overproduction speed), autoimmune_trigger (what self-attack), treatment_response (what intervention effect), recommendation (no_psoriasis/mild_topical/significant_phototherapy/major_biologics/emergency_erythrodermic)."""

EPISTEMIC_PSORIASIS_PROMPT = """Detect epistemic psoriasis:

Plaque pattern: {plaque_pattern}
Turnover rate: {turnover_rate}
Autoimmune trigger: {autoimmune_trigger}
Treatment response: {treatment_response}
Domain: {domain}
Context: {context}

Is there autoimmune overproduction of intellectual surface cells creating rigid patches? Return ONLY valid JSON."""


class EpistemicPsoriasisService:
    """Detects epistemic psoriasis — autoimmune overproduction creating rigid patches."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        plaque_pattern: str,
        *,
        turnover_rate: str = "",
        autoimmune_trigger: str = "",
        treatment_response: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic psoriasis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PSORIASIS_PROMPT.format(
                plaque_pattern=plaque_pattern,
                turnover_rate=turnover_rate or "Not specified",
                autoimmune_trigger=autoimmune_trigger or "Not specified",
                treatment_response=treatment_response or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PSORIASIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "plaque_pattern": plaque_pattern[:200],
            "psoriasis_detected": data.get("psoriasis_detected", False),
            "severity": data.get("severity", ""),
            "turnover_rate": data.get("turnover_rate", ""),
            "autoimmune_trigger": data.get("autoimmune_trigger", ""),
            "treatment_response": data.get("treatment_response", ""),
            "recommendation": data.get("recommendation", ""),
        }
