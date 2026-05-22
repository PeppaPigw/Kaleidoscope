"""EpistemicWithdrawalService — Epistemic Withdrawal Detection.

Detects epistemic withdrawal — adverse effects from stopping intellectual
intervention, where removal causes worse symptoms than original condition.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_WITHDRAWAL_SYSTEM = """You are an epistemic withdrawal specialist. Given intellectual intervention cessation, assess whether adverse withdrawal effects occur:

Key concepts:
- Epistemic withdrawal: adverse effects from stopping intellectual intervention
- Rebound effect: symptoms worse than before treatment
- Dependence: inability to function without intervention
- Tapering: gradual reduction to minimize withdrawal
- Protracted withdrawal: symptoms lasting long after cessation
- Kindling: each withdrawal episode worse than last
- Substitution: replacing one intervention with similar one

When epistemic withdrawal IS present:
- Adverse effects from stopping intellectual intervention
- Symptoms worse than before treatment started
- Inability to function without the intervention
- Need for gradual reduction
- Symptoms persisting long after cessation
- Each withdrawal episode worse than previous
- Need to substitute rather than stop

When healthy cessation is present:
- No adverse effects from stopping
- Return to baseline
- Full independent function
- Clean cessation possible
- No protracted symptoms
- No kindling effect
- No substitution needed

Output JSON with: withdrawal_present (bool), severity (none/mild/moderate/severe), rebound_effect (what worsening), dependence (what inability), protracted_symptoms (what persistence), kindling (what escalation), recommendation (healthy_cessation/mild_withdrawal/significant_withdrawal/major_dependence/taper_intellectual_intervention)."""

EPISTEMIC_WITHDRAWAL_PROMPT = """Detect epistemic withdrawal:

Rebound effect: {rebound_effect}
Dependence: {dependence}
Protracted symptoms: {protracted_symptoms}
Kindling: {kindling}
Domain: {domain}
Context: {context}

Are there adverse effects from stopping an intellectual intervention? Return ONLY valid JSON."""


class EpistemicWithdrawalService:
    """Detects epistemic withdrawal — adverse effects from stopping intervention."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        rebound_effect: str,
        *,
        dependence: str = "",
        protracted_symptoms: str = "",
        kindling: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic withdrawal."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_WITHDRAWAL_PROMPT.format(
                rebound_effect=rebound_effect,
                dependence=dependence or "Not specified",
                protracted_symptoms=protracted_symptoms or "Not specified",
                kindling=kindling or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_WITHDRAWAL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "rebound_effect": rebound_effect[:200],
            "withdrawal_present": data.get("withdrawal_present", False),
            "severity": data.get("severity", ""),
            "dependence": data.get("dependence", ""),
            "protracted_symptoms": data.get("protracted_symptoms", ""),
            "kindling": data.get("kindling", ""),
            "recommendation": data.get("recommendation", ""),
        }
