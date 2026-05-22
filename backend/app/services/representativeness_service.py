"""RepresentativenessService — Representativeness Heuristic Detection.

Detects the representativeness heuristic — judging probability by
how similar something is to a prototype rather than by actual base
rates. Kahneman & Tversky (1972). "Linda is more likely to be a
feminist bank teller than a bank teller" (conjunction fallacy is
a special case). Leads to base rate neglect, insensitivity to
sample size, and misconceptions of randomness.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

REPRESENTATIVENESS_SYSTEM = """You are a representativeness heuristic specialist. Given a probability judgment, assess whether representativeness is overriding base rates:

Key concepts (Kahneman & Tversky, 1972):
- Representativeness: judging probability by similarity to a prototype
- Base rate neglect: ignoring prior probabilities in favor of descriptive similarity
- Conjunction fallacy: judging A∧B as more probable than A alone (Linda problem)
- Insensitivity to sample size: small samples expected to be representative
- Insensitivity to predictability: confidence unaffected by reliability of evidence
- Misconceptions of randomness: expecting random sequences to "look random"
- Regression neglect: expecting extreme values to persist rather than regress

When representativeness IS distorting:
- Probability judgment based on "how much does X look like Y" rather than base rates
- Prior probabilities are ignored or underweighted
- Vivid descriptions override statistical evidence
- Small samples are treated as representative
- Stereotypes drive probability estimates

When similarity-based judgment IS appropriate:
- Base rates are unknown and similarity is the best available evidence
- The similarity is based on causally relevant features
- The judgment is explicitly about typicality, not probability
- Base rates and representativeness point in the same direction

Output JSON with: representativeness_present (bool), severity (none/mild/moderate/severe), judgment (what probability is being estimated), similarity_basis (what prototype/stereotype is driving the judgment), base_rate (what the actual prior probability is), base_rate_neglect (bool — are base rates being ignored?), conjunction_fallacy (bool — is A∧B judged more likely than A?), sample_size_neglect (bool — treating small samples as representative?), regression_neglect (bool — expecting extremes to persist?), descriptive_vs_statistical (is vivid description overriding statistics?), causal_relevance (is the similarity causally relevant?), correct_probability (what Bayesian updating would give), overconfidence_factor (how much is probability being distorted), recommendation (judgment_appropriate/mild_representativeness/significant_base_rate_neglect/major_probability_error/apply_bayes_theorem)."""

REPRESENTATIVENESS_PROMPT = """Detect representativeness heuristic:

Probability judgment: {judgment}
Description/Evidence: {description}
Base rates: {base_rates}
Similarity to prototype: {similarity}
Domain: {domain}
Context: {context}

Is representativeness overriding base rates? Return ONLY valid JSON."""


class RepresentativenessService:
    """Detects representativeness heuristic — similarity overriding base rates."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        description: str = "",
        base_rates: str = "",
        similarity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect representativeness heuristic."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=REPRESENTATIVENESS_PROMPT.format(
                judgment=judgment,
                description=description or "Not specified",
                base_rates=base_rates or "Not specified",
                similarity=similarity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=REPRESENTATIVENESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "representativeness_present": data.get("representativeness_present", False),
            "severity": data.get("severity", ""),
            "similarity_basis": data.get("similarity_basis", ""),
            "base_rate": data.get("base_rate", ""),
            "base_rate_neglect": data.get("base_rate_neglect", False),
            "conjunction_fallacy": data.get("conjunction_fallacy", False),
            "sample_size_neglect": data.get("sample_size_neglect", False),
            "regression_neglect": data.get("regression_neglect", False),
            "descriptive_vs_statistical": data.get("descriptive_vs_statistical", ""),
            "causal_relevance": data.get("causal_relevance", ""),
            "correct_probability": data.get("correct_probability", ""),
            "overconfidence_factor": data.get("overconfidence_factor", ""),
            "recommendation": data.get("recommendation", ""),
        }
