"""FalseConsensusService — False Consensus Effect Detection.

Detects the false consensus effect — the tendency to overestimate
the extent to which others share one's beliefs, attitudes, and
behaviors. Ross, Greene & House (1977). Leads to surprise when
others disagree, poor prediction of group behavior, and
overconfidence in the popularity of one's views.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FALSE_CONSENSUS_SYSTEM = """You are a false consensus effect specialist. Given a belief about what others think, assess whether the false consensus effect is distorting the estimate:

Key concepts (Ross, Greene & House, 1977):
- False consensus: overestimating how many people share your view
- Projection bias: assuming others think/feel as you do
- Availability bias component: your own view is most "available" to you
- Social circle bias: your friends agree with you, so "everyone" must
- Naive realism: "I see reality clearly, so reasonable people must agree"
- False uniqueness (inverse): underestimating how common your abilities are

When false consensus IS present:
- Claiming "everyone knows" or "most people think" without data
- Surprise or outrage when others disagree
- Using personal experience as evidence of population-level beliefs
- Assuming silence means agreement
- Treating one's social circle as representative

When the consensus estimate MAY be accurate:
- Based on actual survey/polling data
- The belief is genuinely near-universal (basic facts, shared values)
- Multiple independent sources confirm the estimate
- The person has diverse social exposure

Output JSON with: false_consensus_present (bool), severity (none/mild/moderate/severe), claimed_consensus (what level of agreement is being claimed), actual_consensus_likely (what the real level probably is), evidence_for_claim (what supports the consensus estimate), projection_bias (bool — assuming others think as they do?), social_circle_bias (bool — generalizing from one's bubble?), naive_realism (bool — "reasonable people must agree with me"?), silence_as_agreement (bool — treating non-objection as support?), survey_data_available (bool — is there actual data on this?), population_sampled (who was actually consulted), population_relevant (who should be consulted), overestimate_magnitude (how far off the consensus estimate likely is), consequences_of_error (what happens if the consensus is wrong), recommendation (consensus_accurate/mild_overestimate/significant_false_consensus/major_projection_error/verify_with_data)."""

FALSE_CONSENSUS_PROMPT = """Detect false consensus effect:

Belief/Claim about others: {belief}
Evidence cited: {evidence}
Population referenced: {population}
Speaker's position: {position}
Domain: {domain}
Context: {context}

Is the false consensus effect inflating this estimate? Return ONLY valid JSON."""


class FalseConsensusService:
    """Detects false consensus effect — overestimating agreement with one's views."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        belief: str,
        *,
        evidence: str = "",
        population: str = "",
        position: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect false consensus effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FALSE_CONSENSUS_PROMPT.format(
                belief=belief,
                evidence=evidence or "Not specified",
                population=population or "Not specified",
                position=position or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=FALSE_CONSENSUS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "belief": belief[:200],
            "false_consensus_present": data.get("false_consensus_present", False),
            "severity": data.get("severity", ""),
            "claimed_consensus": data.get("claimed_consensus", ""),
            "actual_consensus_likely": data.get("actual_consensus_likely", ""),
            "evidence_for_claim": data.get("evidence_for_claim", ""),
            "projection_bias": data.get("projection_bias", False),
            "social_circle_bias": data.get("social_circle_bias", False),
            "naive_realism": data.get("naive_realism", False),
            "silence_as_agreement": data.get("silence_as_agreement", False),
            "survey_data_available": data.get("survey_data_available", False),
            "population_sampled": data.get("population_sampled", ""),
            "population_relevant": data.get("population_relevant", ""),
            "overestimate_magnitude": data.get("overestimate_magnitude", ""),
            "consequences_of_error": data.get("consequences_of_error", ""),
            "recommendation": data.get("recommendation", ""),
        }
