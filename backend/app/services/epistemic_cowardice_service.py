"""EpistemicCowardiceService — Epistemic Cowardice Detection.

Detects epistemic cowardice — avoiding stating one's actual beliefs
or conclusions to avoid social consequences. Withholding honest
assessment, hedging excessively, or giving deliberately vague
answers when clarity is needed. The opposite of intellectual
courage — prioritizing social comfort over truth-telling.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COWARDICE_SYSTEM = """You are an epistemic cowardice specialist. Given a communication, assess whether honest beliefs are being withheld or obscured to avoid social consequences:

Key concepts:
- Epistemic cowardice: avoiding stating actual beliefs
- Excessive hedging: qualifying beyond what uncertainty warrants
- Strategic ambiguity: being vague to avoid commitment
- Social desirability: saying what's expected rather than what's true
- Preference falsification: publicly stating different beliefs than held
- Weasel words: language that appears to say something while saying nothing
- Diplomatic evasion: avoiding the question rather than answering honestly

When epistemic cowardice IS present:
- Knowing the answer but giving a non-answer to avoid conflict
- Hedging far beyond actual uncertainty
- "It depends" when it doesn't really depend
- Refusing to state a conclusion when evidence clearly points one way
- Giving both sides equal weight when one is clearly stronger
- Avoiding specificity to maintain plausible deniability
- "That's an interesting question" without ever answering it

When caution IS appropriate:
- Genuine uncertainty warrants genuine hedging
- The person truly doesn't have enough information
- Diplomatic framing serves a legitimate purpose
- The stakes of being wrong are very high
- Multiple perspectives genuinely have merit
- The audience needs to reach their own conclusion

Output JSON with: epistemic_cowardice_present (bool), severity (none/mild/moderate/severe), communication (what is being communicated), actual_belief (what does the person likely believe), stated_position (what are they actually saying), avoidance_mechanism (how are they avoiding clarity), social_pressure (what social consequence are they avoiding), cost_of_honesty (what would honest statement cost), recommendation (caution_appropriate/mild_hedging/significant_epistemic_cowardice/major_truth_avoidance/state_beliefs_clearly)."""

EPISTEMIC_COWARDICE_PROMPT = """Detect epistemic cowardice:

Communication: {communication}
Question asked: {question}
Response given: {response}
Stakes: {stakes}
Domain: {domain}
Context: {context}

Are honest beliefs being withheld or obscured to avoid social consequences? Return ONLY valid JSON."""


class EpistemicCowardiceService:
    """Detects epistemic cowardice — avoiding stating actual beliefs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        communication: str,
        *,
        question: str = "",
        response: str = "",
        stakes: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic cowardice."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COWARDICE_PROMPT.format(
                communication=communication,
                question=question or "Not specified",
                response=response or "Not specified",
                stakes=stakes or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COWARDICE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "communication": communication[:200],
            "epistemic_cowardice_present": data.get("epistemic_cowardice_present", False),
            "severity": data.get("severity", ""),
            "actual_belief": data.get("actual_belief", ""),
            "stated_position": data.get("stated_position", ""),
            "avoidance_mechanism": data.get("avoidance_mechanism", ""),
            "social_pressure": data.get("social_pressure", ""),
            "cost_of_honesty": data.get("cost_of_honesty", ""),
            "recommendation": data.get("recommendation", ""),
        }
