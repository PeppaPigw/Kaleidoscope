"""EpistemicDecisionArchitectureChoiceOverloadService — Choice Overload Detection.

Detects when too many options degrade decision quality.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DECISION_ARCHITECTURE_CHOICE_OVERLOAD_SYSTEM = """You are an epistemic decision architecture choice overload specialist. Given option proliferation, assess whether too many choices are degrading decision quality:

Key concepts:
- Choice overload: too many options reduce decision quality, confidence, or follow-through
- Option proliferation: expanding the option set beyond useful comparison capacity
- Decision fatigue: depleted attention and judgment from excessive choices
- Satisficing pressure: settling for acceptable options because full evaluation is too costly
- Comparison paralysis: inability to choose because dimensions and tradeoffs multiply

When choice overload IS present:
- The number of options exceeds useful evaluation capacity
- Decision fatigue reduces attention to important criteria
- Satisficing replaces reasoned comparison
- Comparison paralysis delays or prevents action

When no choice overload:
- Options are curated to decision-relevant alternatives
- Comparison dimensions are clear and limited
- Evaluation capacity matches option count
- Decision process preserves quality and follow-through

Output JSON with: choice_overload_detected (bool), severity (none/mild/moderate/severe), decision_fatigue (how fatigue degrades judgment), satisficing_pressure (how settling pressure appears), comparison_paralysis (how comparison stalls choice), recommendation (no_choice_overload/mild_option_curation/significant_choice_reduction/major_decision_scaffolding/emergency_option_set_reset)."""

EPISTEMIC_DECISION_ARCHITECTURE_CHOICE_OVERLOAD_PROMPT = """Detect decision architecture choice overload:

Option proliferation: {option_proliferation}
Decision fatigue: {decision_fatigue}
Satisficing pressure: {satisficing_pressure}
Comparison paralysis: {comparison_paralysis}
Domain: {domain}
Context: {context}

Are too many options degrading decision quality? Return ONLY valid JSON."""


class EpistemicDecisionArchitectureChoiceOverloadService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        option_proliferation: str,
        *,
        decision_fatigue: str = "",
        satisficing_pressure: str = "",
        comparison_paralysis: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DECISION_ARCHITECTURE_CHOICE_OVERLOAD_PROMPT.format(
                option_proliferation=option_proliferation,
                decision_fatigue=decision_fatigue or "Not specified",
                satisficing_pressure=satisficing_pressure or "Not specified",
                comparison_paralysis=comparison_paralysis or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DECISION_ARCHITECTURE_CHOICE_OVERLOAD_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "option_proliferation": option_proliferation[:200],
            "choice_overload_detected": data.get("choice_overload_detected", False),
            "severity": data.get("severity", ""),
            "decision_fatigue": data.get("decision_fatigue", ""),
            "satisficing_pressure": data.get("satisficing_pressure", ""),
            "comparison_paralysis": data.get("comparison_paralysis", ""),
            "recommendation": data.get("recommendation", ""),
        }
