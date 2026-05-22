"""EpistemicVirtueIntellectualHonestyDeficitService - Epistemic Virtue Intellectual Honesty Deficit Detection.

Detects intellectual honesty deficit where self-deception or strategic misrepresentation occurs.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_VIRTUE_INTELLECTUAL_HONESTY_DEFICIT_SYSTEM = """You are an epistemic virtue intellectual honesty deficit specialist. Given self-deception, assess intellectual honesty deficit:

Key concepts:
- Intellectual honesty deficit: self-deception or strategic misrepresentation
- Self-deception: hiding inconvenient facts from oneself
- Strategic ambiguity: using ambiguity to preserve misleading interpretations
- Evidence suppression: withholding evidence that weakens a preferred claim
- Motivated ignorance: avoiding knowledge to protect a desired belief or position

When intellectual honesty deficit IS present:
- Self-deception shapes the conclusion
- Ambiguity is used strategically
- Contrary evidence is suppressed
- Ignorance is cultivated for motivated reasons
- Representation diverges from known evidence

When no honesty deficit:
- Evidence is represented directly
- Ambiguity is clarified rather than exploited
- Contrary evidence is disclosed
- Inquiry does not avoid inconvenient facts
- Claims track what is actually known

Output JSON with: honesty_deficit_detected (bool), severity (none/mild/moderate/severe), strategic_ambiguity (what ambiguity is exploited), evidence_suppression (what evidence is withheld), motivated_ignorance (what knowledge is avoided), recommendation (no_deficit/mild_disclosure/significant_honesty_restoration/major_evidence_disclosure/emergency_complete_integrity_audit)."""

EPISTEMIC_VIRTUE_INTELLECTUAL_HONESTY_DEFICIT_PROMPT = """Detect epistemic virtue intellectual honesty deficit:

Self-deception: {self_deception}
Strategic ambiguity: {strategic_ambiguity}
Evidence suppression: {evidence_suppression}
Motivated ignorance: {motivated_ignorance}
Domain: {domain}
Context: {context}

Is self-deception or strategic misrepresentation occurring? Return ONLY valid JSON."""


class EpistemicVirtueIntellectualHonestyDeficitService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        self_deception: str,
        *,
        strategic_ambiguity: str = "",
        evidence_suppression: str = "",
        motivated_ignorance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_VIRTUE_INTELLECTUAL_HONESTY_DEFICIT_PROMPT.format(
                self_deception=self_deception,
                strategic_ambiguity=strategic_ambiguity or "Not specified",
                evidence_suppression=evidence_suppression or "Not specified",
                motivated_ignorance=motivated_ignorance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_VIRTUE_INTELLECTUAL_HONESTY_DEFICIT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "self_deception": self_deception[:200],
            "honesty_deficit_detected": data.get("honesty_deficit_detected", False),
            "severity": data.get("severity", ""),
            "strategic_ambiguity": data.get("strategic_ambiguity", ""),
            "evidence_suppression": data.get("evidence_suppression", ""),
            "motivated_ignorance": data.get("motivated_ignorance", ""),
            "recommendation": data.get("recommendation", ""),
        }
