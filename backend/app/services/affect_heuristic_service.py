"""AffectHeuristicService — Affect Heuristic Detection.

Detects the affect heuristic — letting current emotions drive
judgments of probability, risk, and benefit. If something feels
good, its risks seem low and benefits high. If something feels
scary, its risks seem high and benefits low. Slovic et al. (2002).
Emotions become information, substituting for careful analysis.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

AFFECT_SYSTEM = """You are an affect heuristic specialist. Given a risk/benefit judgment, assess whether emotions are substituting for analysis:

Key concepts (Slovic et al., 2002; Finucane et al., 2000):
- Affect heuristic: using emotional reactions as information about risk/benefit
- Risk-benefit inversion: if it feels good → low risk, high benefit (and vice versa)
- Dread risk: feared outcomes seem more probable than they are
- Emotional substitution: "how do I feel about it?" replaces "what do I think about it?"
- Affect pool: the collection of positive/negative feelings tagged to a concept
- Somatic markers: body-based emotional signals that guide decisions (Damasio)

When the affect heuristic IS distorting:
- Risk assessment correlates with emotional reaction, not actual data
- Benefits and risks are inversely correlated in judgment (they're often independent in reality)
- Feared activities are judged riskier than data supports
- Liked activities are judged safer than data supports
- Emotional framing changes probability estimates
- Vivid/scary scenarios dominate over statistical evidence

When emotional input IS appropriate:
- Values and preferences legitimately inform decisions
- Emotional reactions reflect genuine experience/expertise
- The decision is fundamentally about preferences, not probabilities
- Gut feelings are calibrated by extensive domain experience

Output JSON with: affect_heuristic_present (bool), severity (none/mild/moderate/severe), judgment (what risk/benefit assessment is being made), emotional_valence (positive/negative/mixed — what emotion is driving it), risk_estimate (what risk level is being assigned), benefit_estimate (what benefit level is being assigned), actual_risk_data (what objective data shows about risk), actual_benefit_data (what objective data shows about benefit), risk_benefit_inversion (bool — are risk and benefit inversely correlated in the judgment?), dread_factor (bool — is fear inflating risk estimates?), vividness_bias (bool — are vivid scenarios dominating statistics?), emotional_framing (how the emotional frame is shaping the judgment), substitution (what question is emotion answering instead of analysis?), calibration_check (how well does the emotional judgment match data?), recommendation (judgment_appropriate/mild_affect_bias/significant_emotional_substitution/major_affect_distortion/analyze_data_separately)."""

AFFECT_PROMPT = """Detect affect heuristic:

Judgment/Assessment: {judgment}
Emotional reaction: {emotion}
Risk data available: {risk_data}
Benefit data available: {benefit_data}
Domain: {domain}
Context: {context}

Is the affect heuristic substituting emotion for analysis? Return ONLY valid JSON."""


class AffectHeuristicService:
    """Detects affect heuristic — emotions substituting for probability/risk analysis."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        emotion: str = "",
        risk_data: str = "",
        benefit_data: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect affect heuristic."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=AFFECT_PROMPT.format(
                judgment=judgment,
                emotion=emotion or "Not specified",
                risk_data=risk_data or "Not specified",
                benefit_data=benefit_data or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=AFFECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "affect_heuristic_present": data.get("affect_heuristic_present", False),
            "severity": data.get("severity", ""),
            "emotional_valence": data.get("emotional_valence", ""),
            "risk_estimate": data.get("risk_estimate", ""),
            "benefit_estimate": data.get("benefit_estimate", ""),
            "actual_risk_data": data.get("actual_risk_data", ""),
            "actual_benefit_data": data.get("actual_benefit_data", ""),
            "risk_benefit_inversion": data.get("risk_benefit_inversion", False),
            "dread_factor": data.get("dread_factor", False),
            "vividness_bias": data.get("vividness_bias", False),
            "emotional_framing": data.get("emotional_framing", ""),
            "substitution": data.get("substitution", ""),
            "calibration_check": data.get("calibration_check", ""),
            "recommendation": data.get("recommendation", ""),
        }
