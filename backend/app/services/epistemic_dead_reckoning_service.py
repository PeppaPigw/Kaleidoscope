"""EpistemicDeadReckoningService — Epistemic Dead Reckoning Detection.

Detects epistemic dead reckoning — navigating by assumption without
checking actual position, accumulating errors over time.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DEAD_RECKONING_SYSTEM = """You are an epistemic dead reckoning specialist. Given a reasoning navigation pattern, assess whether position is assumed without verification:

Key concepts:
- Epistemic dead reckoning: navigating by assumption without position checks
- Accumulated error: errors accumulating without correction
- Position assumption: assuming position without verification
- Drift undetected: drifting from true position without knowing
- No landmarks: no reference points to check against
- Course correction absent: no mechanism to correct course
- Compounding deviation: small errors compounding over time

When dead reckoning IS present:
- Navigating by assumption without checking actual position
- Errors accumulating without correction
- Position assumed without verification
- Drifting from true position without detection
- No reference points being checked against
- No mechanism to correct course
- Small errors compounding over time

When verified navigation is present:
- Position regularly checked against reality
- Errors detected and corrected promptly
- Position verified through multiple means
- Drift detected and corrected
- Reference points regularly checked
- Course correction mechanisms active
- Errors caught before compounding

Output JSON with: dead_reckoning (bool), severity (none/mild/moderate/severe), navigation (what navigation uses dead reckoning), assumptions (what assumptions are made), accumulated_error (what errors accumulate), verification_absent (what verification is missing), recommendation (verified_navigation/mild_assumption/significant_dead_reckoning/major_accumulated_error/check_position)."""

EPISTEMIC_DEAD_RECKONING_PROMPT = """Detect epistemic dead reckoning:

Navigation: {navigation}
Assumptions: {assumptions}
Accumulated error: {accumulated_error}
Verification absent: {verification_absent}
Domain: {domain}
Context: {context}

Is reasoning navigating by assumption without checking actual position? Return ONLY valid JSON."""


class EpistemicDeadReckoningService:
    """Detects epistemic dead reckoning — navigating without position checks."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        navigation: str,
        *,
        assumptions: str = "",
        accumulated_error: str = "",
        verification_absent: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic dead reckoning."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DEAD_RECKONING_PROMPT.format(
                navigation=navigation,
                assumptions=assumptions or "Not specified",
                accumulated_error=accumulated_error or "Not specified",
                verification_absent=verification_absent or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DEAD_RECKONING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "navigation": navigation[:200],
            "dead_reckoning": data.get("dead_reckoning", False),
            "severity": data.get("severity", ""),
            "assumptions": data.get("assumptions", ""),
            "accumulated_error": data.get("accumulated_error", ""),
            "verification_absent": data.get("verification_absent", ""),
            "recommendation": data.get("recommendation", ""),
        }
