"""MotteBaileyDriftService — Motte-and-Bailey Drift Detection.

Detects motte-and-bailey drift — the gradual, often unconscious shift
from a defensible position (motte) to an indefensible one (bailey)
over time, where the drift happens incrementally rather than as a
deliberate rhetorical strategy.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MOTTE_BAILEY_DRIFT_SYSTEM = """You are a motte-and-bailey drift specialist. Given a position that has evolved over time, assess whether it has drifted from defensible to indefensible:

Key concepts:
- Motte-and-bailey drift: gradual shift from defensible to indefensible
- Scope creep in claims: claims expanding beyond their evidence
- Incremental overreach: each step seems small but total drift is large
- Defensible core: the original, well-supported claim
- Indefensible extension: where the claim has drifted to
- Unconscious drift: not deliberate strategy but gradual expansion
- Retreat pattern: when challenged, retreating to the original defensible claim

When motte-and-bailey drift IS present:
- A position has expanded well beyond its original evidence base
- The current claim is much stronger than what was originally supported
- When challenged, the person retreats to a weaker, defensible version
- The drift happened gradually through small extensions
- The person may not realize how far they've drifted
- The original claim was reasonable but the current one isn't
- Each incremental step seemed justified but the total is not

When position evolution IS legitimate:
- New evidence supports the stronger claim
- The expansion is acknowledged and justified
- The person doesn't retreat when challenged
- The stronger claim is independently supported
- The evolution is transparent and documented
- Each step is supported by its own evidence
- The person can defend the current position, not just the original

Output JSON with: motte_bailey_drift_present (bool), severity (none/mild/moderate/severe), original_position (defensible starting point), current_position (where it has drifted to), drift_mechanism (how the drift occurred), retreat_pattern (does person retreat when challenged), evidence_gap (gap between evidence and current claim), recommendation (position_supported/mild_drift/significant_motte_bailey_drift/major_overreach/return_to_evidence_base)."""

MOTTE_BAILEY_DRIFT_PROMPT = """Detect motte-and-bailey drift:

Position: {position}
Original claim: {original}
Current claim: {current}
Evidence: {evidence}
Domain: {domain}
Context: {context}

Has this position drifted from a defensible claim to an indefensible one? Return ONLY valid JSON."""


class MotteBaileyDriftService:
    """Detects motte-and-bailey drift — gradual expansion beyond evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        position: str,
        *,
        original: str = "",
        current: str = "",
        evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect motte-and-bailey drift."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MOTTE_BAILEY_DRIFT_PROMPT.format(
                position=position,
                original=original or "Not specified",
                current=current or "Not specified",
                evidence=evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MOTTE_BAILEY_DRIFT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "position": position[:200],
            "motte_bailey_drift_present": data.get("motte_bailey_drift_present", False),
            "severity": data.get("severity", ""),
            "original_position": data.get("original_position", ""),
            "current_position": data.get("current_position", ""),
            "drift_mechanism": data.get("drift_mechanism", ""),
            "retreat_pattern": data.get("retreat_pattern", ""),
            "recommendation": data.get("recommendation", ""),
        }
