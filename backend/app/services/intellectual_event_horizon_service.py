"""IntellectualEventHorizonService — Intellectual Event Horizon Detection.

Detects intellectual event horizons — points of no return where
alternative views become invisible and unreachable.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

INTELLECTUAL_EVENT_HORIZON_SYSTEM = """You are an intellectual event horizon specialist. Given a belief commitment, assess whether a point of no return has been crossed where alternatives become invisible:

Key concepts:
- Intellectual event horizon: point where alternatives become invisible
- Point of no return: commitment beyond which return is impossible
- Alternative invisibility: alternatives no longer visible or conceivable
- Irreversible commitment: commitment that cannot be reversed
- Perspective lock-in: locked into one perspective permanently
- Conceptual blindness: blind to alternatives after crossing threshold
- Return impossibility: return to open consideration impossible

When intellectual event horizon IS present:
- Point of no return crossed for belief commitment
- Alternative views become invisible or inconceivable
- Commitment irreversible regardless of evidence
- Perspective locked in permanently
- Conceptual blindness to alternatives
- Return to open consideration impossible
- Threshold crossed beyond which revision fails

When strong commitment is present:
- Strong commitment with maintained openness
- Alternatives still visible even if not preferred
- Commitment revisable given sufficient evidence
- Perspective held strongly but not locked
- Alternatives conceivable even if unlikely
- Return to reconsideration possible
- Commitment proportionate to evidence

Output JSON with: event_horizon_present (bool), severity (none/mild/moderate/severe), commitment (what commitment exists), invisibility (what has become invisible), threshold (what threshold was crossed), reversibility (whether return is possible), recommendation (strong_commitment/mild_lock_in/significant_event_horizon/major_alternative_invisibility/maintain_reversibility)."""

INTELLECTUAL_EVENT_HORIZON_PROMPT = """Detect intellectual event horizon:

Commitment: {commitment}
Invisibility: {invisibility}
Threshold: {threshold}
Reversibility: {reversibility}
Domain: {domain}
Context: {context}

Has a point of no return been crossed where alternatives become invisible? Return ONLY valid JSON."""


class IntellectualEventHorizonService:
    """Detects intellectual event horizons — points where alternatives become invisible."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        commitment: str,
        *,
        invisibility: str = "",
        threshold: str = "",
        reversibility: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect intellectual event horizon."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=INTELLECTUAL_EVENT_HORIZON_PROMPT.format(
                commitment=commitment,
                invisibility=invisibility or "Not specified",
                threshold=threshold or "Not specified",
                reversibility=reversibility or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=INTELLECTUAL_EVENT_HORIZON_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "commitment": commitment[:200],
            "event_horizon_present": data.get("event_horizon_present", False),
            "severity": data.get("severity", ""),
            "invisibility": data.get("invisibility", ""),
            "threshold": data.get("threshold", ""),
            "reversibility": data.get("reversibility", ""),
            "recommendation": data.get("recommendation", ""),
        }
