"""MoralLicensingAsymmetryService — Moral Licensing Asymmetry Detection.

Detects moral licensing asymmetry — when past good behavior is
used to justify subsequent bad behavior, but past bad behavior
is not similarly used to motivate compensatory good behavior.
The licensing effect works asymmetrically.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MORAL_LICENSING_ASYMMETRY_SYSTEM = """You are a moral licensing asymmetry specialist. Given a justification, assess whether past behavior is being used asymmetrically:

Key concepts:
- Moral licensing: past good deeds license future bad ones
- Moral credentials: establishing a track record to draw on
- Licensing asymmetry: good deeds license bad, but bad don't motivate good
- Self-concept maintenance: "I'm a good person so this is fine"
- Moral bank account: treating ethics as a balance sheet
- Compensatory behavior: doing good to offset bad (the reverse)
- Moral self-regulation: how people maintain their moral self-image

When moral licensing asymmetry IS present:
- Past good behavior cited to justify current questionable behavior
- "I've earned the right to..." after prior good deeds
- Moral credentials used to deflect criticism
- Good track record used as permission for exceptions
- Asymmetry: past good licenses bad, but past bad doesn't motivate good
- Self-concept as "good person" used to excuse specific bad acts
- Moral bank account thinking — spending accumulated credit

When moral licensing asymmetry is NOT present:
- Past behavior not used to justify current decisions
- Each action evaluated on its own merits
- Good track record acknowledged but not used as license
- Moral consistency maintained regardless of past behavior
- Both good and bad past behavior inform future choices symmetrically
- Self-concept doesn't override specific ethical evaluation
- No "earned the right" reasoning

Output JSON with: licensing_present (bool), severity (none/mild/moderate/severe), credential (what past good behavior is cited), licensed_behavior (what it's being used to justify), asymmetry (how the licensing works one-way), moral_logic (the reasoning being used), recommendation (no_licensing/mild_credential_use/significant_licensing/major_moral_bank_account/evaluate_independently)."""

MORAL_LICENSING_ASYMMETRY_PROMPT = """Detect moral licensing asymmetry:

Justification: {justification}
Past behavior: {past_behavior}
Current action: {current_action}
Moral reasoning: {reasoning}
Domain: {domain}
Context: {context}

Is past good behavior being used to license current questionable behavior? Return ONLY valid JSON."""


class MoralLicensingAsymmetryService:
    """Detects moral licensing asymmetry — past good licensing future bad."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        justification: str,
        *,
        past_behavior: str = "",
        current_action: str = "",
        reasoning: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect moral licensing asymmetry."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MORAL_LICENSING_ASYMMETRY_PROMPT.format(
                justification=justification,
                past_behavior=past_behavior or "Not specified",
                current_action=current_action or "Not specified",
                reasoning=reasoning or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MORAL_LICENSING_ASYMMETRY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "justification": justification[:200],
            "licensing_present": data.get("licensing_present", False),
            "severity": data.get("severity", ""),
            "credential": data.get("credential", ""),
            "licensed_behavior": data.get("licensed_behavior", ""),
            "asymmetry": data.get("asymmetry", ""),
            "recommendation": data.get("recommendation", ""),
        }
