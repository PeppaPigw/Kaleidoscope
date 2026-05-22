"""EpistemicPanicService — Epistemic Panic Detection.

Detects epistemic panic — panic responses to epistemic threats that
worsen rather than resolve them, where the response to uncertainty
creates more problems than the original threat.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PANIC_SYSTEM = """You are an epistemic panic specialist. Given a response to an epistemic threat, assess whether panic is worsening the situation:

Key concepts:
- Epistemic panic: panic response to epistemic threats
- Uncertainty panic: inability to tolerate uncertainty causing harm
- Threat amplification: panic amplifying the original threat
- Reactive epistemology: reactive rather than considered response
- Certainty seeking panic: desperate grab for any certainty
- Epistemic flight: fleeing from uncertainty into false certainty
- Panic-driven decisions: decisions made from panic not reason

When epistemic panic IS present:
- Panic response to epistemic uncertainty
- Response worsening rather than resolving threat
- Desperate grab for certainty regardless of quality
- Reactive rather than considered response to challenge
- Panic amplifying the original epistemic threat
- Flight into false certainty to escape uncertainty
- Decisions driven by panic not evidence

When appropriate urgency is present:
- Urgency proportionate to actual threat
- Response considered despite time pressure
- Uncertainty tolerated while seeking resolution
- Response addressing rather than amplifying threat
- Certainty sought through appropriate means
- Urgency serving rather than replacing reason
- Decisions informed by evidence despite pressure

Output JSON with: panic_present (bool), severity (none/mild/moderate/severe), threat (what epistemic threat exists), response (how it is responded to), amplification (how panic worsens things), false_certainty (what false certainty is sought), recommendation (measured_response/mild_overreaction/significant_epistemic_panic/major_panic_amplification/tolerate_uncertainty_and_respond_deliberately)."""

EPISTEMIC_PANIC_PROMPT = """Detect epistemic panic:

Epistemic threat: {threat}
Response: {response}
Outcome: {outcome}
Certainty sought: {certainty}
Domain: {domain}
Context: {context}

Is panic response to epistemic threat worsening rather than resolving the situation? Return ONLY valid JSON."""


class EpistemicPanicService:
    """Detects epistemic panic — panic responses worsening epistemic threats."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        threat: str,
        *,
        response: str = "",
        outcome: str = "",
        certainty: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic panic."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PANIC_PROMPT.format(
                threat=threat,
                response=response or "Not specified",
                outcome=outcome or "Not specified",
                certainty=certainty or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PANIC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "threat": threat[:200],
            "panic_present": data.get("panic_present", False),
            "severity": data.get("severity", ""),
            "response": data.get("response", ""),
            "amplification": data.get("amplification", ""),
            "false_certainty": data.get("false_certainty", ""),
            "recommendation": data.get("recommendation", ""),
        }
