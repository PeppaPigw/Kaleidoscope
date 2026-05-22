"""ProsecutorFallacyService — Prosecutor's Fallacy Detection.

Detects prosecutor's fallacy — confusing P(evidence|innocent) with
P(innocent|evidence). The probability of seeing the evidence if
innocent is not the same as the probability of being innocent given
the evidence. Requires Bayesian reasoning with base rates.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PROSECUTOR_FALLACY_SYSTEM = """You are a prosecutor's fallacy specialist. Given a probabilistic argument, assess whether it confuses conditional probabilities:

Key concepts:
- Prosecutor's fallacy: confusing P(E|H) with P(H|E)
- Transposed conditional: swapping the direction of conditional probability
- Base rate neglect: ignoring prior probability in Bayesian reasoning
- Bayes' theorem: P(H|E) = P(E|H) * P(H) / P(E)
- False positive paradox: rare events + imperfect tests = many false positives
- Likelihood vs posterior: evidence strength vs updated belief
- Reference class: the relevant population for computing base rates

When prosecutor's fallacy IS present:
- "The probability of this evidence if innocent is 1 in a million, so they're guilty"
- Confusing match probability with source probability
- Ignoring the size of the suspect pool
- "The DNA matches, probability of random match is tiny, therefore guilty"
- Treating P(evidence|hypothesis) as P(hypothesis|evidence)
- Ignoring base rates when interpreting test results
- "Only 1% false positive rate" without considering how many were tested

When probabilistic reasoning IS correct:
- Bayes' theorem is properly applied with base rates
- The prior probability is explicitly considered
- The reference class is appropriate and acknowledged
- Both P(E|H) and P(H) are used to compute P(H|E)
- The size of the tested population is accounted for
- Multiple independent pieces of evidence are properly combined
- The argument distinguishes likelihood from posterior probability

Output JSON with: prosecutor_fallacy_present (bool), severity (none/mild/moderate/severe), argument (what probabilistic argument), conditional_confused (what conditionals are swapped), base_rate (what base rate is ignored), correct_calculation (what Bayesian calculation would show), population_size (relevant population), recommendation (reasoning_correct/mild_conditional_confusion/significant_prosecutor_fallacy/major_base_rate_neglect/apply_bayes_theorem)."""

PROSECUTOR_FALLACY_PROMPT = """Detect prosecutor's fallacy:

Argument: {argument}
Probability cited: {probability}
Base rate: {base_rate}
Population: {population}
Domain: {domain}
Context: {context}

Does this argument confuse P(evidence|hypothesis) with P(hypothesis|evidence)? Return ONLY valid JSON."""


class ProsecutorFallacyService:
    """Detects prosecutor's fallacy — transposed conditional probability."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        probability: str = "",
        base_rate: str = "",
        population: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect prosecutor's fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PROSECUTOR_FALLACY_PROMPT.format(
                argument=argument,
                probability=probability or "Not specified",
                base_rate=base_rate or "Not specified",
                population=population or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PROSECUTOR_FALLACY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "prosecutor_fallacy_present": data.get("prosecutor_fallacy_present", False),
            "severity": data.get("severity", ""),
            "conditional_confused": data.get("conditional_confused", ""),
            "base_rate": data.get("base_rate", ""),
            "correct_calculation": data.get("correct_calculation", ""),
            "recommendation": data.get("recommendation", ""),
        }
