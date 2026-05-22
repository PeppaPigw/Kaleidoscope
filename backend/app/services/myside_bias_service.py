"""MysideBiasService — Myside Bias Detection.

Detects myside bias — the tendency to evaluate evidence, generate
arguments, and test hypotheses in a manner biased toward one's
own prior opinions and beliefs. Stanovich et al. (2013). Unlike
confirmation bias (seeking confirming evidence), myside bias is
about evaluating ALL evidence through one's own lens — even
evidence one didn't seek out.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MYSIDE_BIAS_SYSTEM = """You are a myside bias specialist. Given an evaluation or argument, assess whether it is being processed through the lens of prior beliefs rather than objectively:

Key concepts (Stanovich et al., 2013):
- Myside bias: evaluating everything from one's own perspective
- Belief-consistent evaluation: favorable treatment of supporting evidence
- Belief-inconsistent scrutiny: harsh treatment of opposing evidence
- Argument generation: generating arguments only for own side
- Hypothesis testing: testing only hypotheses consistent with beliefs
- Intelligence independence: myside bias is NOT correlated with IQ
- Decontextualization failure: inability to evaluate arguments independently of beliefs

When myside bias IS present:
- Generating arguments only for one's preferred conclusion
- Evaluating identical evidence differently based on which side it supports
- Failing to consider how the argument looks from the other side
- "That's a good point" only for points supporting one's view
- Inability to steelman the opposing position
- Treating own perspective as the neutral/default position
- Evaluating argument quality based on conclusion rather than logic

When perspective-taking IS adequate:
- Arguments are evaluated on logical structure regardless of conclusion
- The person can articulate the strongest version of opposing views
- Evidence is weighted by quality, not by which side it supports
- Own biases are acknowledged and compensated for
- The evaluation would be the same regardless of which side one is on

Output JSON with: myside_bias_present (bool), severity (none/mild/moderate/severe), evaluation (what is being evaluated), own_position (what is the evaluator's prior belief), treatment_of_supporting (how is supporting evidence treated), treatment_of_opposing (how is opposing evidence treated), steelman_ability (can they articulate the best opposing argument), perspective_independence (would evaluation change if beliefs were different), recommendation (evaluation_balanced/mild_myside_lean/significant_myside_bias/major_perspective_lock/evaluate_independently_of_beliefs)."""

MYSIDE_BIAS_PROMPT = """Detect myside bias:

Evaluation: {evaluation}
Own position: {own_position}
Evidence handling: {evidence_handling}
Opposing view: {opposing_view}
Domain: {domain}
Context: {context}

Is the evaluation being processed through the lens of prior beliefs rather than objectively? Return ONLY valid JSON."""


class MysideBiasService:
    """Detects myside bias — evaluating everything from one's own perspective."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        evaluation: str,
        *,
        own_position: str = "",
        evidence_handling: str = "",
        opposing_view: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect myside bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MYSIDE_BIAS_PROMPT.format(
                evaluation=evaluation,
                own_position=own_position or "Not specified",
                evidence_handling=evidence_handling or "Not specified",
                opposing_view=opposing_view or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MYSIDE_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "evaluation": evaluation[:200],
            "myside_bias_present": data.get("myside_bias_present", False),
            "severity": data.get("severity", ""),
            "own_position": data.get("own_position", ""),
            "treatment_of_supporting": data.get("treatment_of_supporting", ""),
            "treatment_of_opposing": data.get("treatment_of_opposing", ""),
            "steelman_ability": data.get("steelman_ability", ""),
            "perspective_independence": data.get("perspective_independence", ""),
            "recommendation": data.get("recommendation", ""),
        }
