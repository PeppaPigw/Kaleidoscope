"""ManufacturedConsentService — Manufactured Consent Detection.

Detects manufactured consent — engineering public opinion through
systematic media/institutional control so that people believe they
freely chose positions that were actually shaped for them.
Chomsky & Herman (1988). The consent appears genuine but was
manufactured through information control.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MANUFACTURED_CONSENT_SYSTEM = """You are a manufactured consent specialist. Given an opinion formation process, assess whether consent is being engineered rather than genuinely formed:

Key concepts (Chomsky & Herman, 1988):
- Manufactured consent: engineering opinion through information control
- Propaganda model: systematic filters on information
- Overton window management: controlling what's considered acceptable
- Agenda setting: controlling what people think about, not what they think
- Framing control: determining how issues are presented
- False consensus: making manufactured opinion appear organic
- Information asymmetry: controlling what people know to control what they conclude

When manufactured consent IS present:
- Opinion appears organic but was systematically shaped
- Information is filtered to support predetermined conclusions
- Alternative viewpoints are systematically excluded
- The range of acceptable debate is artificially narrowed
- People believe they freely chose positions that were shaped for them
- Institutional power shapes opinion while appearing neutral
- Dissent is marginalized rather than engaged

When opinion formation IS organic:
- Multiple perspectives are genuinely available
- People have access to contradicting information
- The opinion formation process is transparent
- Dissent is possible and visible
- No systematic filtering of information
- People can articulate reasons beyond what they've been told
- The opinion survives exposure to counter-arguments

Output JSON with: manufactured_consent_present (bool), severity (none/mild/moderate/severe), opinion (what opinion is being formed), formation_process (how is it being formed), information_control (what information is filtered), alternative_suppression (what alternatives are excluded), organic_indicators (signs of genuine opinion formation), recommendation (opinion_organic/mild_influence/significant_manufacturing/major_consent_engineering/expose_information_filters)."""

MANUFACTURED_CONSENT_PROMPT = """Detect manufactured consent:

Opinion: {opinion}
Formation: {formation}
Information control: {control}
Alternatives: {alternatives}
Domain: {domain}
Context: {context}

Is consent being engineered through systematic information control rather than genuinely formed? Return ONLY valid JSON."""


class ManufacturedConsentService:
    """Detects manufactured consent — engineered opinion formation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        opinion: str,
        *,
        formation: str = "",
        control: str = "",
        alternatives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect manufactured consent."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MANUFACTURED_CONSENT_PROMPT.format(
                opinion=opinion,
                formation=formation or "Not specified",
                control=control or "Not specified",
                alternatives=alternatives or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MANUFACTURED_CONSENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "opinion": opinion[:200],
            "manufactured_consent_present": data.get("manufactured_consent_present", False),
            "severity": data.get("severity", ""),
            "information_control": data.get("information_control", ""),
            "alternative_suppression": data.get("alternative_suppression", ""),
            "organic_indicators": data.get("organic_indicators", ""),
            "recommendation": data.get("recommendation", ""),
        }
