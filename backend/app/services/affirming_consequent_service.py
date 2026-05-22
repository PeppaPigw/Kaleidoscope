"""AffirmingConsequentService — Affirming the Consequent Detection.

Detects affirming the consequent — the invalid inference from
P→Q and Q to P. Just because a theory predicts an observation
doesn't mean the observation proves the theory, since other
theories might predict the same observation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

AFFIRMING_CONSEQUENT_SYSTEM = """You are an affirming the consequent specialist. Given a reasoning pattern, assess whether it commits the fallacy of affirming the consequent:

Key concepts:
- Affirming the consequent: P→Q, Q, therefore P (INVALID)
- Multiple realizability: many causes can produce the same effect
- Underdetermination: evidence consistent with multiple theories
- Confirmation vs proof: evidence supports but doesn't prove
- Alternative explanations: other theories predict the same observation
- Necessary vs sufficient: Q being necessary for P ≠ Q being sufficient for P
- Bayesian update: observation increases probability but doesn't prove

When affirming the consequent IS present:
- "If my theory is right, we'd see X. We see X. Therefore my theory is right."
- Treating confirmation as proof
- Ignoring alternative explanations for the same observation
- "The prediction came true, so the theory must be correct"
- Failing to consider other theories that predict the same thing
- Treating a necessary condition as sufficient
- "If guilty, fingerprints would be there. Fingerprints are there. Therefore guilty."

When the inference IS valid:
- The conditional is biconditional (P↔Q, not just P→Q)
- Alternative explanations have been ruled out
- The observation is uniquely predicted by this theory
- Bayesian reasoning properly weights the evidence
- The inference is presented as probabilistic, not certain
- Multiple independent predictions all confirmed
- The theory is the only known explanation

Output JSON with: affirming_consequent_present (bool), severity (none/mild/moderate/severe), conditional (what P→Q relationship), observation (what Q is observed), conclusion (what P is concluded), alternatives (what other explanations exist), validity (is the inference valid), recommendation (inference_valid/mild_overconfidence/significant_affirming_consequent/major_proof_confusion/consider_alternative_explanations)."""

AFFIRMING_CONSEQUENT_PROMPT = """Detect affirming the consequent:

Reasoning: {reasoning}
Conditional: {conditional}
Observation: {observation}
Conclusion: {conclusion}
Domain: {domain}
Context: {context}

Does this reasoning commit the fallacy of affirming the consequent — concluding P from P→Q and Q? Return ONLY valid JSON."""


class AffirmingConsequentService:
    """Detects affirming the consequent — invalid inference from P→Q and Q to P."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reasoning: str,
        *,
        conditional: str = "",
        observation: str = "",
        conclusion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect affirming the consequent."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=AFFIRMING_CONSEQUENT_PROMPT.format(
                reasoning=reasoning,
                conditional=conditional or "Not specified",
                observation=observation or "Not specified",
                conclusion=conclusion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=AFFIRMING_CONSEQUENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "reasoning": reasoning[:200],
            "affirming_consequent_present": data.get("affirming_consequent_present", False),
            "severity": data.get("severity", ""),
            "conditional": data.get("conditional", ""),
            "alternatives": data.get("alternatives", ""),
            "validity": data.get("validity", ""),
            "recommendation": data.get("recommendation", ""),
        }
