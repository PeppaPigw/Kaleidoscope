"""EpistemicNociceptionService — Epistemic Nociception Detection.

Detects epistemic nociception — the intellectual pain signal that
warns when knowledge is being damaged or threatened.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NOCICEPTION_SYSTEM = """You are an epistemic nociception specialist. Given an intellectual pain pattern, assess whether pain signals warn of knowledge damage:

Key concepts:
- Epistemic nociception: pain signals warning of knowledge damage
- Nociceptor: detector of intellectual harm
- Pain threshold: how much damage before signal fires
- Referred pain: pain felt in wrong location
- Hyperalgesia: excessive pain sensitivity
- Analgesia: inability to feel intellectual pain
- Chronic pain: persistent pain without ongoing damage

When epistemic nociception IS present:
- Pain signals warning that knowledge is being damaged
- Detectors firing when intellectual harm occurs
- Threshold of damage before warning signals activate
- Pain felt in wrong intellectual area
- Excessive sensitivity to intellectual threats
- Inability to feel when knowledge is being harmed
- Persistent pain without ongoing intellectual damage

When painless awareness is present:
- Awareness of damage without pain signals
- No alarm system for intellectual harm
- No threshold needed for awareness
- Awareness located accurately
- Proportionate response to threats
- Full awareness of all harm
- No persistent false alarms

Output JSON with: nociception_present (bool), severity (none/mild/moderate/severe), nociceptor (what detects harm), threshold (what triggers the signal), referred (where pain is mislocated), hyperalgesia (what excessive sensitivity), recommendation (painless_awareness/mild_sensitivity/significant_nociception/major_pain_signaling/calibrate_pain_response)."""

EPISTEMIC_NOCICEPTION_PROMPT = """Detect epistemic nociception:

Nociceptor: {nociceptor}
Threshold: {threshold}
Referred: {referred}
Hyperalgesia: {hyperalgesia}
Domain: {domain}
Context: {context}

Are intellectual pain signals warning when knowledge is being damaged or threatened? Return ONLY valid JSON."""


class EpistemicNociceptionService:
    """Detects epistemic nociception — pain signals warning of knowledge damage."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        nociceptor: str,
        *,
        threshold: str = "",
        referred: str = "",
        hyperalgesia: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic nociception."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NOCICEPTION_PROMPT.format(
                nociceptor=nociceptor,
                threshold=threshold or "Not specified",
                referred=referred or "Not specified",
                hyperalgesia=hyperalgesia or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NOCICEPTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "nociceptor": nociceptor[:200],
            "nociception_present": data.get("nociception_present", False),
            "severity": data.get("severity", ""),
            "threshold": data.get("threshold", ""),
            "referred": data.get("referred", ""),
            "hyperalgesia": data.get("hyperalgesia", ""),
            "recommendation": data.get("recommendation", ""),
        }
