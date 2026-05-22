"""EpistemicInstitutionalFundingBiasService — Epistemic Funding Bias Detection.

Detects epistemic institutional funding bias — funding bias distorting research
directions and findings.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INSTITUTIONAL_FUNDING_BIAS_SYSTEM = """You are an epistemic institutional funding bias specialist. Given funder influence, assess research distortion:

Key concepts:
- Epistemic funding bias: funding sources biasing research
- Funder influence: funders shaping questions, methods, or conclusions
- Question selection bias: fundable questions prioritized over important questions
- Positive result pressure: pressure to produce funder-favorable or positive findings
- Commercial interest alignment: research agenda aligning with commercial incentives

When epistemic funding bias IS present:
- Funder influence distorts research
- Question selection biased by funding
- Positive results pressured
- Commercial interests shape findings
- Independent inquiry displaced

When no funding bias:
- Research questions selected on epistemic merit
- Results reported regardless of direction
- Commercial interests disclosed and bounded
- Methods and conclusions remain independent

Output JSON with: funding_bias_detected (bool), severity (none/mild/moderate/severe), question_selection_bias (what question selection bias), positive_result_pressure (what positive result pressure), commercial_interest_alignment (what commercial interest alignment), recommendation (no_funding_bias/mild_disclosure_check/significant_independence_verification/major_intensive_funding_audit/emergency_complete_funding_bias)."""

EPISTEMIC_INSTITUTIONAL_FUNDING_BIAS_PROMPT = """Detect epistemic institutional funding bias:

Funder influence: {funder_influence}
Question selection bias: {question_selection_bias}
Positive result pressure: {positive_result_pressure}
Commercial interest alignment: {commercial_interest_alignment}
Domain: {domain}
Context: {context}

Is funding bias distorting research directions and findings? Return ONLY valid JSON."""


class EpistemicInstitutionalFundingBiasService:
    """Detects epistemic funding bias — research distortion by funders."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        funder_influence: str,
        *,
        question_selection_bias: str = "",
        positive_result_pressure: str = "",
        commercial_interest_alignment: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic institutional funding bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INSTITUTIONAL_FUNDING_BIAS_PROMPT.format(
                funder_influence=funder_influence,
                question_selection_bias=question_selection_bias or "Not specified",
                positive_result_pressure=positive_result_pressure or "Not specified",
                commercial_interest_alignment=commercial_interest_alignment or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INSTITUTIONAL_FUNDING_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "funder_influence": funder_influence[:200],
            "funding_bias_detected": data.get("funding_bias_detected", False),
            "severity": data.get("severity", ""),
            "question_selection_bias": data.get("question_selection_bias", ""),
            "positive_result_pressure": data.get("positive_result_pressure", ""),
            "commercial_interest_alignment": data.get("commercial_interest_alignment", ""),
            "recommendation": data.get("recommendation", ""),
        }
