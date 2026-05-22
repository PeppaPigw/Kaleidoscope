"""AttentionAsymmetryService — Attention Asymmetry Detection.

Detects attention asymmetry — asymmetric attention to confirming
versus disconfirming evidence, where more cognitive effort is spent
on evidence that supports existing beliefs.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ATTENTION_ASYMMETRY_SYSTEM = """You are an attention asymmetry specialist. Given an evidence evaluation, assess whether attention is asymmetrically distributed:

Key concepts:
- Attention asymmetry: unequal attention to confirming vs disconfirming
- Confirmation attention: more attention to supporting evidence
- Disconfirmation neglect: less attention to challenging evidence
- Scrutiny asymmetry: different scrutiny levels based on direction
- Effort asymmetry: more effort finding flaws in disconfirming
- Search asymmetry: searching harder for confirming evidence
- Processing asymmetry: deeper processing of preferred evidence

When attention asymmetry IS present:
- More attention given to confirming evidence
- Disconfirming evidence given less scrutiny
- Different standards applied based on direction
- More effort spent finding flaws in challenging evidence
- Search for evidence biased toward confirmation
- Confirming evidence processed more deeply
- Asymmetry in cognitive effort based on evidence direction

When differential attention is appropriate:
- Attention proportionate to evidence quality
- Scrutiny applied equally regardless of direction
- Standards consistent across confirming and disconfirming
- Effort allocated by relevance not preference
- Search balanced between confirming and disconfirming
- Processing depth based on quality not direction
- Asymmetry justified by evidence quality differences

Output JSON with: asymmetry_present (bool), severity (none/mild/moderate/severe), evaluation (what evaluation is made), confirming_attention (attention to confirming), disconfirming_attention (attention to disconfirming), ratio (how asymmetric), recommendation (balanced_attention/mild_confirmation_preference/significant_attention_asymmetry/major_disconfirmation_neglect/equalize_attention_across_directions)."""

ATTENTION_ASYMMETRY_PROMPT = """Detect attention asymmetry:

Evaluation: {evaluation}
Confirming evidence: {confirming}
Disconfirming evidence: {disconfirming}
Attention pattern: {pattern}
Domain: {domain}
Context: {context}

Is attention asymmetrically distributed between confirming and disconfirming evidence? Return ONLY valid JSON."""


class AttentionAsymmetryService:
    """Detects attention asymmetry — unequal attention to confirming vs disconfirming."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        evaluation: str,
        *,
        confirming: str = "",
        disconfirming: str = "",
        pattern: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect attention asymmetry."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ATTENTION_ASYMMETRY_PROMPT.format(
                evaluation=evaluation,
                confirming=confirming or "Not specified",
                disconfirming=disconfirming or "Not specified",
                pattern=pattern or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ATTENTION_ASYMMETRY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "evaluation": evaluation[:200],
            "asymmetry_present": data.get("asymmetry_present", False),
            "severity": data.get("severity", ""),
            "confirming_attention": data.get("confirming_attention", ""),
            "disconfirming_attention": data.get("disconfirming_attention", ""),
            "ratio": data.get("ratio", ""),
            "recommendation": data.get("recommendation", ""),
        }
