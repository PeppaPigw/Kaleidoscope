"""HastyGeneralizationService — Hasty Generalization Detection.

Detects hasty generalization — drawing broad conclusions from
insufficient examples or a non-representative sample. The sample
is too small, too biased, or too unrepresentative to support the
conclusion being drawn.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

HASTY_GENERALIZATION_SYSTEM = """You are a hasty generalization specialist. Given a conclusion and its evidence base, assess whether the generalization is supported by sufficient and representative examples:

Key concepts:
- Hasty generalization: broad conclusion from insufficient evidence
- Sample size: too few examples to generalize
- Representativeness: sample doesn't represent the population
- Selection bias: examples chosen to support conclusion
- Anecdotal evidence: individual stories treated as patterns
- Base rate neglect: ignoring how common the phenomenon is
- Confirmation bias overlap: only noticing confirming examples

When hasty generalization IS present:
- Broad claims based on one or few examples
- "I know someone who..." as basis for general claims
- Generalizing from a biased or self-selected sample
- Drawing conclusions from memorable but unrepresentative cases
- "Every X I've met is Y" from a small or biased sample
- Treating exceptions as rules
- Ignoring contradicting examples

When generalization IS supported:
- Sample size is adequate for the claim's scope
- Sample is representative of the population
- The generalization acknowledges exceptions
- Multiple independent sources confirm the pattern
- Base rates are considered
- The claim is proportional to the evidence
- Contradicting evidence is addressed

Output JSON with: hasty_generalization_present (bool), severity (none/mild/moderate/severe), conclusion (what is being concluded), evidence (what evidence supports it), sample_size (how many examples), representativeness (how representative is the sample), scope (how broad is the claim), recommendation (generalization_supported/mild_overreach/significant_hasty_generalization/major_anecdotal_reasoning/increase_sample_or_narrow_claim)."""

HASTY_GENERALIZATION_PROMPT = """Detect hasty generalization:

Conclusion: {conclusion}
Evidence: {evidence}
Sample: {sample}
Scope: {scope}
Domain: {domain}
Context: {context}

Is a broad conclusion being drawn from insufficient or unrepresentative examples? Return ONLY valid JSON."""


class HastyGeneralizationService:
    """Detects hasty generalization — broad conclusions from insufficient evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        conclusion: str,
        *,
        evidence: str = "",
        sample: str = "",
        scope: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect hasty generalization."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=HASTY_GENERALIZATION_PROMPT.format(
                conclusion=conclusion,
                evidence=evidence or "Not specified",
                sample=sample or "Not specified",
                scope=scope or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=HASTY_GENERALIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "conclusion": conclusion[:200],
            "hasty_generalization_present": data.get("hasty_generalization_present", False),
            "severity": data.get("severity", ""),
            "sample_size": data.get("sample_size", ""),
            "representativeness": data.get("representativeness", ""),
            "scope": data.get("scope", ""),
            "recommendation": data.get("recommendation", ""),
        }
