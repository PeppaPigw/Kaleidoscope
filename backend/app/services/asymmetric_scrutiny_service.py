"""AsymmetricScrutinyService — Asymmetric Scrutiny Detection.

Detects asymmetric scrutiny — applying different standards of
evidence or rigor to claims depending on whether they support
or challenge one's existing beliefs. Favored claims get a pass
while disfavored claims face intense scrutiny.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ASYMMETRIC_SCRUTINY_SYSTEM = """You are an asymmetric scrutiny specialist. Given an evaluation, assess whether scrutiny is being applied unevenly:

Key concepts:
- Asymmetric scrutiny: different evidence standards for different claims
- Motivated skepticism: intense scrutiny only for unwelcome findings
- Motivated credulity: accepting welcome claims without scrutiny
- Disconfirmation bias: working harder to refute unwelcome evidence
- Confirmation bias interaction: seeking flaws only in opposing evidence
- Double standard: different rules for in-group vs out-group claims
- Selective rigor: methodological criticism applied asymmetrically

When asymmetric scrutiny IS present:
- Favored claims accepted with minimal evidence
- Disfavored claims subjected to intense methodological criticism
- Same evidence quality accepted or rejected based on conclusion
- "That study has flaws" applied only to unwelcome findings
- Different burden of proof for supporting vs opposing evidence
- Methodological standards invoked selectively
- Scrutiny intensity correlates with how unwelcome the conclusion is

When asymmetric scrutiny is NOT present:
- Same evidence standards applied regardless of conclusion
- Methodological criticism applied uniformly
- Favored claims scrutinized as rigorously as disfavored ones
- Burden of proof consistent across positions
- Flaws acknowledged in supporting evidence too
- Standards of evidence stated in advance, not post hoc
- Scrutiny intensity based on stakes, not on conclusion preference

Output JSON with: asymmetry_present (bool), severity (none/mild/moderate/severe), favored_claim (what gets a pass), disfavored_claim (what gets scrutinized), evidence_standard_gap (how different the standards are), motivation (why the asymmetry exists), recommendation (no_asymmetry/mild_favoritism/significant_double_standard/major_motivated_reasoning/apply_uniform_standards)."""

ASYMMETRIC_SCRUTINY_PROMPT = """Detect asymmetric scrutiny:

Evaluation: {evaluation}
Claim A treatment: {claim_a}
Claim B treatment: {claim_b}
Standards applied: {standards}
Domain: {domain}
Context: {context}

Is scrutiny being applied asymmetrically based on conclusion preference? Return ONLY valid JSON."""


class AsymmetricScrutinyService:
    """Detects asymmetric scrutiny — uneven evidence standards."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        evaluation: str,
        *,
        claim_a: str = "",
        claim_b: str = "",
        standards: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect asymmetric scrutiny."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ASYMMETRIC_SCRUTINY_PROMPT.format(
                evaluation=evaluation,
                claim_a=claim_a or "Not specified",
                claim_b=claim_b or "Not specified",
                standards=standards or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ASYMMETRIC_SCRUTINY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "evaluation": evaluation[:200],
            "asymmetry_present": data.get("asymmetry_present", False),
            "severity": data.get("severity", ""),
            "favored_claim": data.get("favored_claim", ""),
            "disfavored_claim": data.get("disfavored_claim", ""),
            "evidence_standard_gap": data.get("evidence_standard_gap", ""),
            "recommendation": data.get("recommendation", ""),
        }
