"""EpistemicCatalystPoisoningService — Epistemic Catalyst Poisoning Detection.

Detects epistemic catalyst poisoning — intellectual catalysts that
normally accelerate understanding being poisoned and rendered inert.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CATALYST_POISONING_SYSTEM = """You are an epistemic catalyst poisoning specialist. Given an intellectual process, assess whether catalysts have been poisoned:

Key concepts:
- Epistemic catalyst poisoning: intellectual catalysts rendered inert
- Catalyst: something that accelerates understanding without being consumed
- Poisoning: contamination that deactivates the catalyst
- Inert catalyst: catalyst that no longer functions
- Process slowdown: intellectual processes slowing without catalyst
- Poison source: what is poisoning the catalyst
- Reactivation: whether the catalyst can be restored

When catalyst poisoning IS present:
- Intellectual catalysts rendered inert by contamination
- Things that normally accelerate understanding no longer working
- Contamination deactivating intellectual catalysts
- Catalysts present but no longer functioning
- Intellectual processes slowing due to catalyst failure
- Identifiable source of catalyst poisoning
- Catalysts needing reactivation or replacement

When active catalysts are present:
- Intellectual catalysts functioning normally
- Understanding accelerated by active catalysts
- No contamination affecting catalysts
- Catalysts fully functional
- Intellectual processes running at normal speed
- No poisoning of catalysts
- Catalysts maintaining their effectiveness

Output JSON with: poisoning_present (bool), severity (none/mild/moderate/severe), catalyst (what catalyst is poisoned), poison (what poisons it), slowdown (what process slows), reactivation (whether it can be restored), recommendation (active_catalysts/mild_deactivation/significant_poisoning/major_catalyst_failure/remove_poison_or_replace)."""

EPISTEMIC_CATALYST_POISONING_PROMPT = """Detect epistemic catalyst poisoning:

Catalyst: {catalyst}
Poison: {poison}
Slowdown: {slowdown}
Reactivation: {reactivation}
Domain: {domain}
Context: {context}

Are intellectual catalysts being poisoned and rendered inert? Return ONLY valid JSON."""


class EpistemicCatalystPoisoningService:
    """Detects epistemic catalyst poisoning — intellectual catalysts rendered inert."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        catalyst: str,
        *,
        poison: str = "",
        slowdown: str = "",
        reactivation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic catalyst poisoning."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CATALYST_POISONING_PROMPT.format(
                catalyst=catalyst,
                poison=poison or "Not specified",
                slowdown=slowdown or "Not specified",
                reactivation=reactivation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CATALYST_POISONING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "catalyst": catalyst[:200],
            "poisoning_present": data.get("poisoning_present", False),
            "severity": data.get("severity", ""),
            "poison": data.get("poison", ""),
            "slowdown": data.get("slowdown", ""),
            "reactivation": data.get("reactivation", ""),
            "recommendation": data.get("recommendation", ""),
        }
