"""SurvivorshipExplanationService — Survivorship Explanation Detection.

Detects survivorship explanation — explaining success by studying
only survivors, missing that the same traits exist in failures,
creating false causal narratives from biased samples.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SURVIVORSHIP_EXPLANATION_SYSTEM = """You are a survivorship explanation specialist. Given a causal explanation, assess whether it's based on studying only survivors:

Key concepts:
- Survivorship explanation: causal claims from survivor-only data
- Selection on dependent variable: studying only successes
- Invisible failures: failures with same traits not examined
- Success narrative: post-hoc explanation of why survivors succeeded
- Base rate of traits: traits common in both successes and failures
- Wald's bullet holes: looking at what survived, not what didn't
- Reverse survivorship: traits of failures also present in successes

When survivorship explanation IS present:
- Success explained by traits also present in failures
- Only survivors studied, failures invisible
- Causal claims from biased sample
- Traits of success identified without checking failures
- Post-hoc narrative constructed from survivor characteristics
- Base rate of traits in failures unknown or ignored
- Selection on dependent variable

When success analysis is appropriate:
- Both successes and failures examined
- Base rates of traits compared across outcomes
- Selection bias acknowledged
- Causal claims appropriately hedged
- Failures with same traits noted
- Survivorship bias explicitly addressed
- Comparison group included

Output JSON with: survivorship_present (bool), severity (none/mild/moderate/severe), explanation (what is explained), survivors_studied (who/what was studied), failures_ignored (what failures are invisible), shared_traits (traits common to both), recommendation (appropriate_success_analysis/mild_selection_bias/significant_survivorship_explanation/major_survivor_only_causation/include_failures)."""

SURVIVORSHIP_EXPLANATION_PROMPT = """Detect survivorship explanation:

Explanation: {explanation}
Sample: {sample}
Failures: {failures}
Traits claimed: {traits}
Domain: {domain}
Context: {context}

Is success being explained by studying only survivors while ignoring failures with the same traits? Return ONLY valid JSON."""


class SurvivorshipExplanationService:
    """Detects survivorship explanation — causal claims from survivor-only data."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        explanation: str,
        *,
        sample: str = "",
        failures: str = "",
        traits: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect survivorship explanation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SURVIVORSHIP_EXPLANATION_PROMPT.format(
                explanation=explanation,
                sample=sample or "Not specified",
                failures=failures or "Not specified",
                traits=traits or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SURVIVORSHIP_EXPLANATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "explanation": explanation[:200],
            "survivorship_present": data.get("survivorship_present", False),
            "severity": data.get("severity", ""),
            "survivors_studied": data.get("survivors_studied", ""),
            "failures_ignored": data.get("failures_ignored", ""),
            "shared_traits": data.get("shared_traits", ""),
            "recommendation": data.get("recommendation", ""),
        }
