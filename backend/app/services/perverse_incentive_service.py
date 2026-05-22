"""PerverseIncentiveService — Perverse Incentive Detection.

Detects perverse incentives — incentive structures that produce the
opposite of their intended outcomes because rational actors respond
to the incentive in ways the designer didn't anticipate.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PERVERSE_INCENTIVE_SYSTEM = """You are a perverse incentive specialist. Given an incentive structure, assess whether it produces outcomes opposite to its intent:

Key concepts:
- Perverse incentive: reward structure that produces unintended harmful outcomes
- Cobra effect: bounty on cobras leads to cobra farming
- Gaming the metric: optimizing the measure rather than the goal
- Rational response: actors respond rationally to incentives, not intentions
- Misaligned incentives: what's rewarded differs from what's desired
- Unintended optimization: system optimizes for the wrong thing
- Campbell's Law: measures used as targets become corrupted

When perverse incentive IS present:
- The incentive rewards behavior opposite to the stated goal
- Rational actors would game the system rather than achieve the goal
- The metric being rewarded diverges from the actual objective
- Historical examples show similar incentives producing perverse outcomes
- The incentive creates a market for the problem it's trying to solve
- Short-term incentives conflict with long-term goals
- The incentive punishes the desired behavior or rewards the undesired

When incentive IS well-designed:
- The incentive aligns individual and collective interests
- Gaming is difficult or unprofitable
- The metric closely tracks the actual objective
- Feedback loops correct for unintended responses
- The incentive has been tested and refined
- Multiple metrics prevent single-metric gaming
- The incentive accounts for rational actor responses

Output JSON with: perverse_incentive_present (bool), severity (none/mild/moderate/severe), incentive (what incentive structure), intended_outcome (what was intended), actual_outcome (what actually happens), mechanism (how rational actors game it), alignment (how well incentive aligns with goal), recommendation (incentive_aligned/mild_misalignment/significant_perverse_incentive/major_cobra_effect/redesign_incentive_structure)."""

PERVERSE_INCENTIVE_PROMPT = """Detect perverse incentive:

Incentive structure: {incentive}
Intended outcome: {intended}
Actual behavior: {actual}
Gaming potential: {gaming}
Domain: {domain}
Context: {context}

Does this incentive structure produce outcomes opposite to its intent? Return ONLY valid JSON."""


class PerverseIncentiveService:
    """Detects perverse incentives — incentive structures producing opposite outcomes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        incentive: str,
        *,
        intended: str = "",
        actual: str = "",
        gaming: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect perverse incentive."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PERVERSE_INCENTIVE_PROMPT.format(
                incentive=incentive,
                intended=intended or "Not specified",
                actual=actual or "Not specified",
                gaming=gaming or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PERVERSE_INCENTIVE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "incentive": incentive[:200],
            "perverse_incentive_present": data.get("perverse_incentive_present", False),
            "severity": data.get("severity", ""),
            "intended_outcome": data.get("intended_outcome", ""),
            "actual_outcome": data.get("actual_outcome", ""),
            "mechanism": data.get("mechanism", ""),
            "recommendation": data.get("recommendation", ""),
        }
