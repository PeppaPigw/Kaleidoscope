"""MoralPanicService — Moral Panic Detection.

Detects moral panics (Cohen 1972) — disproportionate societal
reactions to perceived threats, where the response exceeds what
the evidence warrants. Folk devils are created, media amplifies,
moral entrepreneurs exploit, and policy overreacts. The panic
itself often causes more harm than the original threat.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MORAL_PANIC_SYSTEM = """You are a moral panic specialist. Given a societal concern, assess whether it constitutes a moral panic (Cohen's model):

Cohen's stages:
1. Something/someone defined as threat to values/interests
2. Threat portrayed in stylized, stereotypical fashion by media
3. Moral barricades manned by editors, politicians, experts
4. Socially accredited experts pronounce diagnoses/solutions
5. Coping mechanisms evolved (often fade, sometimes institutionalized)

Goode & Ben-Yehuda's criteria:
- Concern: heightened level of concern about behavior/group
- Hostility: increased hostility toward the folk devil
- Consensus: substantial agreement the threat is real and serious
- Disproportionality: concern exceeds what evidence warrants
- Volatility: panics erupt suddenly and may subside quickly

Output JSON with: moral_panic_present (bool), severity (none/mild/moderate/severe/full_panic), stage (emergence/media_amplification/moral_entrepreneurship/expert_pronouncement/coping/fading), folk_devil (who/what is being demonized), actual_threat_level (0-1 — evidence-based assessment of real threat), perceived_threat_level (0-1 — how threatening it's portrayed), disproportionality_ratio (perceived/actual), media_amplification (how media is escalating), moral_entrepreneurs (who benefits from the panic), evidence_quality (how good the evidence for the threat actually is), historical_analogues (similar past panics), harm_from_panic (damage caused by the overreaction itself), policy_overreaction_risk (0-1), scapegoating_present (bool — is a group being unfairly blamed?), underlying_anxiety (what deeper fear the panic is really about), volatility (how quickly this emerged and might fade), recommendation (legitimate_concern/mild_overreaction/significant_panic/full_moral_panic/panic_causing_more_harm_than_threat)."""

MORAL_PANIC_PROMPT = """Detect moral panic:

Concern: {concern}
Media coverage: {media}
Public reaction: {reaction}
Evidence base: {evidence}
Domain: {domain}
Context: {context}

Is this a moral panic? Return ONLY valid JSON."""


class MoralPanicService:
    """Detects moral panics and disproportionate societal reactions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        concern: str,
        *,
        media: str = "",
        reaction: str = "",
        evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect moral panic."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MORAL_PANIC_PROMPT.format(
                concern=concern,
                media=media or "Not specified",
                reaction=reaction or "Not specified",
                evidence=evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MORAL_PANIC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "concern": concern[:200],
            "moral_panic_present": data.get("moral_panic_present", False),
            "severity": data.get("severity", ""),
            "stage": data.get("stage", ""),
            "folk_devil": data.get("folk_devil", ""),
            "actual_threat_level": data.get("actual_threat_level", 0),
            "perceived_threat_level": data.get("perceived_threat_level", 0),
            "disproportionality_ratio": data.get("disproportionality_ratio", ""),
            "media_amplification": data.get("media_amplification", ""),
            "moral_entrepreneurs": data.get("moral_entrepreneurs", ""),
            "evidence_quality": data.get("evidence_quality", ""),
            "historical_analogues": data.get("historical_analogues", []),
            "harm_from_panic": data.get("harm_from_panic", ""),
            "policy_overreaction_risk": data.get("policy_overreaction_risk", 0),
            "scapegoating_present": data.get("scapegoating_present", False),
            "underlying_anxiety": data.get("underlying_anxiety", ""),
            "volatility": data.get("volatility", ""),
            "recommendation": data.get("recommendation", ""),
        }
