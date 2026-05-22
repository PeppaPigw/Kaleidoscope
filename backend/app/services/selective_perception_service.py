"""SelectivePerceptionService — Selective Perception Detection.

Detects selective perception — filtering information to match
pre-existing expectations, beliefs, or desires. People see
what they expect to see and miss what they don't expect.
Leads to confirmation of existing beliefs regardless of
actual evidence, and failure to notice disconfirming data.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SELECTIVE_PERCEPTION_SYSTEM = """You are a selective perception specialist. Given an interpretation of information, assess whether the person is filtering data to match their expectations:

Key concepts:
- Selective perception: filtering information through expectation lens
- Perceptual set: expectations determine what is noticed
- Confirmation bias overlap: but selective perception is about what's perceived, not just sought
- Inattentional blindness: missing unexpected stimuli
- Change blindness: failing to notice changes that don't match expectations
- Schema-driven processing: interpreting ambiguous info to fit existing schemas
- Motivated perception: seeing what you want to see

When selective perception IS present:
- Noticing only information that confirms existing beliefs
- Missing obvious contradictory evidence
- Interpreting ambiguous information as supporting one's view
- "I didn't see that" for clearly present disconfirming data
- Different people seeing completely different things in the same situation
- Filtering out inconvenient facts while amplifying convenient ones

When the interpretation IS accurate:
- The person acknowledges both confirming and disconfirming evidence
- The interpretation is consistent with what most observers would see
- Ambiguous information is acknowledged as ambiguous
- The person can articulate what would change their mind
- Multiple perspectives are considered before concluding

Output JSON with: selective_perception_present (bool), severity (none/mild/moderate/severe), information (what information is being processed), interpretation (how is it being interpreted), expectation (what was expected), confirming_noticed (what confirming info was noticed?), disconfirming_missed (what disconfirming info was missed?), ambiguity_level (how ambiguous is the information?), alternative_interpretations (what other interpretations are possible?), motivation (what motivation might drive selective perception?), recommendation (interpretation_accurate/mild_selectivity/significant_filtering/major_selective_perception/consider_all_evidence)."""

SELECTIVE_PERCEPTION_PROMPT = """Detect selective perception:

Information: {information}
Interpretation: {interpretation}
Expectations: {expectations}
Missed data: {missed}
Domain: {domain}
Context: {context}

Is the person filtering information to match their expectations? Return ONLY valid JSON."""


class SelectivePerceptionService:
    """Detects selective perception — filtering information to match expectations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        information: str,
        *,
        interpretation: str = "",
        expectations: str = "",
        missed: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect selective perception."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SELECTIVE_PERCEPTION_PROMPT.format(
                information=information,
                interpretation=interpretation or "Not specified",
                expectations=expectations or "Not specified",
                missed=missed or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SELECTIVE_PERCEPTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "information": information[:200],
            "selective_perception_present": data.get("selective_perception_present", False),
            "severity": data.get("severity", ""),
            "interpretation": data.get("interpretation", ""),
            "confirming_noticed": data.get("confirming_noticed", ""),
            "disconfirming_missed": data.get("disconfirming_missed", ""),
            "ambiguity_level": data.get("ambiguity_level", ""),
            "alternative_interpretations": data.get("alternative_interpretations", ""),
            "motivation": data.get("motivation", ""),
            "recommendation": data.get("recommendation", ""),
        }
