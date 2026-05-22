"""EpistemicPowerKnowledgeMonopolyService - Epistemic Power Knowledge Monopoly Detection.

Detects knowledge monopoly where access to information is controlled.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_POWER_KNOWLEDGE_MONOPOLY_SYSTEM = """You are an epistemic power and knowledge monopoly specialist. Given information control, assess whether access to knowledge is monopolized:

Key concepts:
- Knowledge monopoly: concentrated control over information access
- Information control: restricting who can know, verify, or challenge claims
- Classification abuse: secrecy used beyond legitimate protection
- Need-to-know expansion: unnecessary restriction through access doctrine
- Transparency resistance: blocking accountability or independent review

When a knowledge monopoly IS present:
- Information access is controlled to preserve power
- Secrecy exceeds legitimate safety or privacy needs
- Need-to-know rules expand beyond necessity
- Independent verification is prevented
- Transparency is resisted without adequate justification

When no knowledge monopoly:
- Restrictions are narrow, justified, and reviewable
- Independent oversight can verify claims
- Access rules match real safety or privacy constraints
- Transparency is default where possible
- Information control is contestable and time-limited

Output JSON with: monopoly_detected (bool), severity (none/mild/moderate/severe), information_control (what information is controlled), classification_abuse (what secrecy abuse appears), need_to_know_expansion (how access limits expand), transparency_resistance (what accountability is resisted), recommendation (no_monopoly/mild_access_review/significant_transparency_reform/major_information_opening/emergency_monopoly_breakup)."""

EPISTEMIC_POWER_KNOWLEDGE_MONOPOLY_PROMPT = """Detect epistemic power and knowledge monopoly:

Information control: {information_control}
Classification abuse: {classification_abuse}
Need-to-know expansion: {need_to_know_expansion}
Transparency resistance: {transparency_resistance}
Domain: {domain}
Context: {context}

Is access to information being controlled as a knowledge monopoly? Return ONLY valid JSON."""


class EpistemicPowerKnowledgeMonopolyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        information_control: str,
        *,
        classification_abuse: str = "",
        need_to_know_expansion: str = "",
        transparency_resistance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_POWER_KNOWLEDGE_MONOPOLY_PROMPT.format(
                information_control=information_control,
                classification_abuse=classification_abuse or "Not specified",
                need_to_know_expansion=need_to_know_expansion or "Not specified",
                transparency_resistance=transparency_resistance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_POWER_KNOWLEDGE_MONOPOLY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "information_control": information_control[:200],
            "monopoly_detected": data.get("monopoly_detected", False),
            "severity": data.get("severity", ""),
            "classification_abuse": data.get("classification_abuse", ""),
            "need_to_know_expansion": data.get("need_to_know_expansion", ""),
            "transparency_resistance": data.get("transparency_resistance", ""),
            "recommendation": data.get("recommendation", ""),
        }
