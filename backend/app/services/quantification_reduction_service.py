"""QuantificationReductionService — Quantification Reduction Detection.

Detects quantification reduction — treating only what can be
measured as real or important, reducing rich qualitative phenomena
to numbers and losing essential meaning in the process.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

QUANTIFICATION_REDUCTION_SYSTEM = """You are a quantification reduction specialist. Given an assessment or evaluation, determine whether quantification is inappropriately reducing understanding:

Key concepts:
- Quantification reduction: only measured things count
- Metric tyranny: numbers replacing understanding
- Qualitative erasure: non-quantifiable aspects ignored
- Measurement as reality: what's measured is what's real
- Number fetishism: preference for numbers over insight
- Dashboard epistemology: knowing only through metrics
- Precision theater: false precision masking ignorance

When quantification reduction IS present:
- Only quantifiable aspects considered
- Rich phenomena reduced to single numbers
- Qualitative understanding dismissed
- Metrics substitute for genuine understanding
- Important non-measurable aspects ignored
- False precision masks genuine uncertainty
- Numbers treated as more real than experience

When quantification is appropriate:
- Measurement serves understanding
- Quantitative and qualitative integrated
- Metrics complement rather than replace insight
- Limitations of measurement acknowledged
- Non-quantifiable aspects valued
- Precision proportional to knowledge
- Numbers inform rather than replace judgment

Output JSON with: reduction_present (bool), severity (none/mild/moderate/severe), assessment (what is assessed), quantified (what is quantified), lost (what is lost in quantification), false_precision (what false precision exists), recommendation (appropriate_quantification/mild_metric_preference/significant_quantification_reduction/major_qualitative_erasure/integrate_qualitative_and_quantitative)."""

QUANTIFICATION_REDUCTION_PROMPT = """Detect quantification reduction:

Assessment: {assessment}
What's measured: {measured}
What's not measured: {unmeasured}
Qualitative aspects: {qualitative}
Domain: {domain}
Context: {context}

Is quantification inappropriately reducing understanding by ignoring non-measurable aspects? Return ONLY valid JSON."""


class QuantificationReductionService:
    """Detects quantification reduction — only measured things counting as real."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        assessment: str,
        *,
        measured: str = "",
        unmeasured: str = "",
        qualitative: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect quantification reduction."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=QUANTIFICATION_REDUCTION_PROMPT.format(
                assessment=assessment,
                measured=measured or "Not specified",
                unmeasured=unmeasured or "Not specified",
                qualitative=qualitative or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=QUANTIFICATION_REDUCTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "assessment": assessment[:200],
            "reduction_present": data.get("reduction_present", False),
            "severity": data.get("severity", ""),
            "quantified": data.get("quantified", ""),
            "lost": data.get("lost", ""),
            "false_precision": data.get("false_precision", ""),
            "recommendation": data.get("recommendation", ""),
        }
