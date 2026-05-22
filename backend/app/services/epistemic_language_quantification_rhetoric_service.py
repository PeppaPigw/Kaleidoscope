"""EpistemicLanguageQuantificationRhetoricService - Epistemic Language Quantification Rhetoric Detection.

Detects epistemic language quantification rhetoric - numbers used to
create false precision, authority, or scale distortion.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LANGUAGE_QUANTIFICATION_RHETORIC_SYSTEM = """You are an epistemic language quantification rhetoric specialist. Given numbers used to create false precision, assess quantification rhetoric:

Key concepts:
- Epistemic language quantification rhetoric: using numbers to create unwarranted authority
- Numerical authority: numbers making claims seem more objective than warranted
- Statistic cherry-picking: selecting favorable statistics while omitting others
- Denominator neglect: ignoring the base or comparison population
- Percentage versus absolute: choosing percentage or absolute framing strategically
- False precision: giving more exactness than evidence supports
- Scale distortion: numbers changing perceived magnitude misleadingly

When quantification rhetoric IS present:
- Numerical authority overused
- Statistics cherry-picked
- Denominators neglected
- Percentage or absolute framing manipulative
- False precision created
- Scale distorted
- Quantification outruns evidence

When no quantification rhetoric:
- Numbers support warranted claims
- Statistics contextualized
- Denominators clear
- Percentage and absolute values balanced
- Precision calibrated
- Scale represented accurately
- Quantification matches evidence

Output JSON with: quantification_rhetoric_detected (bool), severity (none/mild/moderate/severe), numerical_authority (what authority created), statistic_cherry_picking (what statistic selected), denominator_neglect (what denominator ignored), percentage_vs_absolute (what framing distorted), recommendation (no_quantification_rhetoric/mild_context_addition/significant_statistical_reframing/major_intensive_number_audit/emergency_complete_quantification_rhetoric)."""

EPISTEMIC_LANGUAGE_QUANTIFICATION_RHETORIC_PROMPT = """Detect epistemic language quantification rhetoric:

Numerical authority: {numerical_authority}
Statistic cherry-picking: {statistic_cherry_picking}
Denominator neglect: {denominator_neglect}
Percentage vs absolute: {percentage_vs_absolute}
Domain: {domain}
Context: {context}

Are numbers creating false precision or authority? Return ONLY valid JSON."""


class EpistemicLanguageQuantificationRhetoricService:
    """Detects epistemic language quantification rhetoric - false numerical authority."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        numerical_authority: str,
        *,
        statistic_cherry_picking: str = "",
        denominator_neglect: str = "",
        percentage_vs_absolute: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic language quantification rhetoric."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LANGUAGE_QUANTIFICATION_RHETORIC_PROMPT.format(
                numerical_authority=numerical_authority,
                statistic_cherry_picking=statistic_cherry_picking or "Not specified",
                denominator_neglect=denominator_neglect or "Not specified",
                percentage_vs_absolute=percentage_vs_absolute or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LANGUAGE_QUANTIFICATION_RHETORIC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "numerical_authority": numerical_authority[:200],
            "quantification_rhetoric_detected": data.get("quantification_rhetoric_detected", False),
            "severity": data.get("severity", ""),
            "statistic_cherry_picking": data.get("statistic_cherry_picking", ""),
            "denominator_neglect": data.get("denominator_neglect", ""),
            "percentage_vs_absolute": data.get("percentage_vs_absolute", ""),
            "recommendation": data.get("recommendation", ""),
        }
