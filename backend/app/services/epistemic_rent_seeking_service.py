"""EpistemicRentSeekingService — Epistemic Rent-Seeking Detection.

Detects epistemic rent-seeking — extracting value from controlling
access to knowledge rather than producing new knowledge, creating
artificial scarcity in information.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_RENT_SEEKING_SYSTEM = """You are an epistemic rent-seeking specialist. Given a knowledge economy situation, assess whether rent-seeking is occurring:

Key concepts:
- Epistemic rent-seeking: extracting value from access control
- Knowledge toll-booths: charging for passage not production
- Artificial scarcity: making knowledge scarce for profit
- Middleman capture: intermediaries extracting value
- Access gatekeeping for profit: restricting for revenue
- Knowledge hoarding: withholding for strategic advantage
- Information asymmetry maintenance: keeping others ignorant

When epistemic rent-seeking IS present:
- Value extracted from controlling access, not producing knowledge
- Artificial scarcity created in naturally abundant information
- Intermediaries capture value without adding knowledge
- Access restricted for revenue rather than quality
- Knowledge hoarded for strategic advantage
- Information asymmetry maintained for profit
- Barriers serve rent extraction not knowledge quality

When knowledge monetization is appropriate:
- Revenue supports knowledge production
- Access fees fund research and curation
- Intermediaries add genuine value
- Pricing reflects production costs
- Knowledge eventually becomes open
- Monetization incentivizes creation
- Barriers serve quality not just profit

Output JSON with: rent_seeking_present (bool), severity (none/mild/moderate/severe), situation (what situation exists), mechanism (how rent is extracted), artificial_scarcity (what scarcity is created), value_capture (who captures value), recommendation (appropriate_knowledge_monetization/mild_access_friction/significant_epistemic_rent_seeking/major_knowledge_toll_booth/open_knowledge_access)."""

EPISTEMIC_RENT_SEEKING_PROMPT = """Detect epistemic rent-seeking:

Situation: {situation}
Access model: {access}
Value flow: {value}
Production contribution: {production}
Domain: {domain}
Context: {context}

Is value being extracted from controlling knowledge access rather than producing knowledge? Return ONLY valid JSON."""


class EpistemicRentSeekingService:
    """Detects epistemic rent-seeking — extracting value from access control."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        access: str = "",
        value: str = "",
        production: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic rent-seeking."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_RENT_SEEKING_PROMPT.format(
                situation=situation,
                access=access or "Not specified",
                value=value or "Not specified",
                production=production or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_RENT_SEEKING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "rent_seeking_present": data.get("rent_seeking_present", False),
            "severity": data.get("severity", ""),
            "mechanism": data.get("mechanism", ""),
            "artificial_scarcity": data.get("artificial_scarcity", ""),
            "value_capture": data.get("value_capture", ""),
            "recommendation": data.get("recommendation", ""),
        }
