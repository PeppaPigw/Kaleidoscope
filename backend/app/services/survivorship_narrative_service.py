"""SurvivorshipNarrativeService — Survivorship Narrative Detection.

Detects survivorship narrative bias — drawing conclusions from visible
successes while ignoring the much larger pool of invisible failures.
The successes that survive to be observed are not representative of
all attempts.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SURVIVORSHIP_NARRATIVE_SYSTEM = """You are a survivorship narrative specialist. Given a conclusion drawn from examples, assess whether it suffers from survivorship bias — only looking at successes:

Key concepts:
- Survivorship bias: conclusions drawn only from visible survivors
- Selection effect: failures are invisible, successes are visible
- Silent evidence: the data you can't see because it didn't survive
- Base rate of failure: how many attempts fail for each success
- Denominator neglect: focusing on successes without counting attempts
- Reverse survivorship: the failures that would disprove the narrative
- Abraham Wald problem: looking at what survived, not what didn't

When survivorship narrative IS present:
- "Successful people did X, so X leads to success" (ignoring failures who also did X)
- Drawing lessons only from companies that survived
- "College dropouts become billionaires" (ignoring millions who don't)
- Studying only published research (ignoring file drawer problem)
- "This building survived 500 years, they built better then" (ignoring collapsed ones)
- Advice based on what winners did without checking if losers did the same
- Generalizing from exceptional cases without considering the base rate

When learning from success IS appropriate:
- The analysis accounts for the base rate of failure
- Failures are explicitly considered and compared
- The sample includes both successes and failures
- Selection effects are acknowledged and controlled for
- The conclusion is about necessary conditions, not sufficient ones
- Survivorship is acknowledged as a limitation
- The denominator (total attempts) is known or estimated

Output JSON with: survivorship_narrative_present (bool), severity (none/mild/moderate/severe), conclusion (what conclusion is drawn), sample (what examples are used), invisible_failures (what failures are ignored), selection_effect (how selection biases the sample), base_rate (what is the actual success rate), recommendation (analysis_appropriate/mild_survivorship/significant_survivorship_narrative/major_selection_bias/consider_invisible_failures)."""

SURVIVORSHIP_NARRATIVE_PROMPT = """Detect survivorship narrative:

Conclusion: {conclusion}
Examples used: {examples}
Failures considered: {failures}
Selection: {selection}
Domain: {domain}
Context: {context}

Is this conclusion drawn only from visible successes while ignoring invisible failures? Return ONLY valid JSON."""


class SurvivorshipNarrativeService:
    """Detects survivorship narrative — conclusions from visible successes only."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        conclusion: str,
        *,
        examples: str = "",
        failures: str = "",
        selection: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect survivorship narrative."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SURVIVORSHIP_NARRATIVE_PROMPT.format(
                conclusion=conclusion,
                examples=examples or "Not specified",
                failures=failures or "Not specified",
                selection=selection or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SURVIVORSHIP_NARRATIVE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "conclusion": conclusion[:200],
            "survivorship_narrative_present": data.get("survivorship_narrative_present", False),
            "severity": data.get("severity", ""),
            "invisible_failures": data.get("invisible_failures", ""),
            "selection_effect": data.get("selection_effect", ""),
            "base_rate": data.get("base_rate", ""),
            "recommendation": data.get("recommendation", ""),
        }
