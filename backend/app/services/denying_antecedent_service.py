"""DenyingAntecedentService — Denying the Antecedent Detection.

Detects denying the antecedent — the invalid inference from P→Q
and ¬P to ¬Q. Just because one sufficient condition is absent
doesn't mean the consequent is false, since other conditions
might produce the same result.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DENYING_ANTECEDENT_SYSTEM = """You are a denying the antecedent specialist. Given a reasoning pattern, assess whether it commits the fallacy of denying the antecedent:

Key concepts:
- Denying the antecedent: P→Q, ¬P, therefore ¬Q (INVALID)
- Sufficient vs necessary: P being sufficient for Q ≠ P being necessary for Q
- Multiple sufficient conditions: many paths can lead to Q
- Conditional logic: understanding what conditionals do and don't imply
- Inverse error: confusing a conditional with its inverse
- Alternative paths: other conditions that could produce Q
- Logical form: distinguishing valid from invalid argument forms

When denying the antecedent IS present:
- "If you study, you'll pass. You didn't study. Therefore you won't pass."
- Treating a sufficient condition as if it were necessary
- "If it rains, the ground is wet. It didn't rain. Therefore ground isn't wet."
- Ignoring other paths to the same outcome
- "Only if P then Q" when actually "if P then Q" (not biconditional)
- Concluding something can't happen because one cause is absent
- Failing to consider alternative sufficient conditions

When the inference IS valid:
- The conditional is actually biconditional (P is necessary AND sufficient)
- P is genuinely the only way to achieve Q
- The relationship is definitional, not merely causal
- No alternative paths to Q exist
- The conditional has been established as "only if"
- The inference is about necessary conditions, not just sufficient ones
- Context makes clear that P is the only relevant cause

Output JSON with: denying_antecedent_present (bool), severity (none/mild/moderate/severe), conditional (what P→Q relationship), denial (what ¬P is asserted), conclusion (what ¬Q is concluded), alternative_paths (what other paths to Q exist), necessity (is P actually necessary for Q), recommendation (inference_valid/mild_logical_error/significant_denying_antecedent/major_necessity_confusion/consider_alternative_paths)."""

DENYING_ANTECEDENT_PROMPT = """Detect denying the antecedent:

Reasoning: {reasoning}
Conditional: {conditional}
Denial: {denial}
Conclusion: {conclusion}
Domain: {domain}
Context: {context}

Does this reasoning commit the fallacy of denying the antecedent — concluding ¬Q from P→Q and ¬P? Return ONLY valid JSON."""


class DenyingAntecedentService:
    """Detects denying the antecedent — invalid inference from P→Q and ¬P to ¬Q."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reasoning: str,
        *,
        conditional: str = "",
        denial: str = "",
        conclusion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect denying the antecedent."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DENYING_ANTECEDENT_PROMPT.format(
                reasoning=reasoning,
                conditional=conditional or "Not specified",
                denial=denial or "Not specified",
                conclusion=conclusion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DENYING_ANTECEDENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "reasoning": reasoning[:200],
            "denying_antecedent_present": data.get("denying_antecedent_present", False),
            "severity": data.get("severity", ""),
            "conditional": data.get("conditional", ""),
            "alternative_paths": data.get("alternative_paths", ""),
            "necessity": data.get("necessity", ""),
            "recommendation": data.get("recommendation", ""),
        }
