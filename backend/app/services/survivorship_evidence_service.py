"""SurvivorshipEvidenceService — Survivorship Evidence Detection.

Detects survivorship evidence bias — when conclusions are drawn
only from survivors or successes, systematically missing the
evidence from failures, dropouts, or non-survivors that would
change the conclusion.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SURVIVORSHIP_EVIDENCE_SYSTEM = """You are a survivorship evidence specialist. Given a conclusion, assess whether it's based only on survivor data:

Key concepts:
- Survivorship bias in evidence: only seeing what survived
- Missing failures: conclusions drawn without failure data
- Selection on outcome: studying only successes
- Dropout bias: ignoring those who left the sample
- Publication bias: only successful studies published
- Visibility bias: failures are invisible, successes are visible
- Base rate from survivors: can't estimate success rate from winners only

When survivorship evidence IS present:
- Conclusions drawn only from successful cases
- Failures, dropouts, or non-survivors not in the data
- "All successful X did Y" without checking if unsuccessful X also did Y
- Advice derived only from winners
- Sample consists only of those who made it through
- No data on the base rate of failure
- Invisible graveyard of failures not accounted for

When survivorship evidence is NOT present:
- Both successes and failures included in analysis
- Base rates calculated from full population
- Dropouts and non-survivors tracked
- Conclusions account for selection effects
- Failure data actively sought
- "What about those who tried and failed?" addressed
- Full population, not just survivors, informs conclusions

Output JSON with: survivorship_present (bool), severity (none/mild/moderate/severe), conclusion (what is being claimed), survivor_sample (who is in the data), missing_failures (what failures are invisible), base_rate_impact (how failures would change the conclusion), recommendation (full_sample/mild_survivorship/significant_survivor_bias/major_invisible_graveyard/include_failure_data)."""

SURVIVORSHIP_EVIDENCE_PROMPT = """Detect survivorship evidence:

Conclusion: {conclusion}
Sample: {sample}
Selection process: {selection}
Known failures: {failures}
Domain: {domain}
Context: {context}

Is this conclusion based only on survivor/success data? Return ONLY valid JSON."""


class SurvivorshipEvidenceService:
    """Detects survivorship evidence — conclusions from survivors only."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        conclusion: str,
        *,
        sample: str = "",
        selection: str = "",
        failures: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect survivorship evidence."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SURVIVORSHIP_EVIDENCE_PROMPT.format(
                conclusion=conclusion,
                sample=sample or "Not specified",
                selection=selection or "Not specified",
                failures=failures or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SURVIVORSHIP_EVIDENCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "conclusion": conclusion[:200],
            "survivorship_present": data.get("survivorship_present", False),
            "severity": data.get("severity", ""),
            "missing_failures": data.get("missing_failures", ""),
            "base_rate_impact": data.get("base_rate_impact", ""),
            "survivor_sample": data.get("survivor_sample", ""),
            "recommendation": data.get("recommendation", ""),
        }
