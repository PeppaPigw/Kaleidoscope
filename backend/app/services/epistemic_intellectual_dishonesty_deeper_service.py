"""EpistemicIntellectualDishonestyDeeperService — Epistemic Intellectual Dishonesty Deeper Detection.

Detects deeper epistemic intellectual dishonesty — where one knows
they're being intellectually dishonest but continues anyway.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INTELLECTUAL_DISHONESTY_DEEPER_SYSTEM = """You are an epistemic intellectual dishonesty specialist. Given knowing dishonesty continues, assess deeper dishonesty:

Key concepts:
- Epistemic intellectual dishonesty deeper: knowing one is dishonest but continuing
- Conscious misrepresentation: knowingly misrepresenting one's views
- Strategic deception: deliberately deceiving about intellectual positions
- Bad faith argumentation: arguing positions one doesn't hold
- Intellectual fraud: presenting false intellectual credentials
- Knowing hypocrisy: applying different standards knowingly
- Meta-dishonesty: being dishonest about being dishonest

When epistemic intellectual dishonesty deeper IS present:
- Knowing one is dishonest but continuing
- Knowingly misrepresenting views
- Deliberately deceiving about positions
- Arguing positions not held
- Presenting false credentials
- Applying different standards knowingly
- Being dishonest about dishonesty

When no deeper dishonesty:
- Honest about positions
- Representing views accurately
- Transparent about positions
- Arguing genuine positions
- Honest credentials
- Consistent standards
- Honest about honesty

Output JSON with: intellectual_dishonesty_deeper_detected (bool), severity (none/mild/moderate/severe), conscious_misrepresentation (what knowingly misrepresenting), strategic_deception (what deliberately deceiving about), bad_faith_argumentation (what arguing without holding), knowing_hypocrisy (what applying different standards to), recommendation (no_deeper_dishonesty/mild_honesty_recommitment/significant_integrity_rebuilding/major_intensive_truth_alignment/emergency_complete_intellectual_fraud)."""

EPISTEMIC_INTELLECTUAL_DISHONESTY_DEEPER_PROMPT = """Detect deeper epistemic intellectual dishonesty:

Conscious misrepresentation: {conscious_misrepresentation}
Strategic deception: {strategic_deception}
Bad faith argumentation: {bad_faith_argumentation}
Knowing hypocrisy: {knowing_hypocrisy}
Domain: {domain}
Context: {context}

Is there knowing intellectual dishonesty that continues despite awareness? Return ONLY valid JSON."""


class EpistemicIntellectualDishonestyDeeperService:
    """Detects deeper epistemic intellectual dishonesty — knowing dishonesty continues."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        conscious_misrepresentation: str,
        *,
        strategic_deception: str = "",
        bad_faith_argumentation: str = "",
        knowing_hypocrisy: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect deeper epistemic intellectual dishonesty."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INTELLECTUAL_DISHONESTY_DEEPER_PROMPT.format(
                conscious_misrepresentation=conscious_misrepresentation,
                strategic_deception=strategic_deception or "Not specified",
                bad_faith_argumentation=bad_faith_argumentation or "Not specified",
                knowing_hypocrisy=knowing_hypocrisy or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INTELLECTUAL_DISHONESTY_DEEPER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "conscious_misrepresentation": conscious_misrepresentation[:200],
            "intellectual_dishonesty_deeper_detected": data.get("intellectual_dishonesty_deeper_detected", False),
            "severity": data.get("severity", ""),
            "strategic_deception": data.get("strategic_deception", ""),
            "bad_faith_argumentation": data.get("bad_faith_argumentation", ""),
            "knowing_hypocrisy": data.get("knowing_hypocrisy", ""),
            "recommendation": data.get("recommendation", ""),
        }
