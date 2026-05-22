"""TechDeterminismService — Technological Determinism Detection.

Detects technological determinism — treating technology as an
autonomous force that determines social outcomes, ignoring human
agency, design choices, and political decisions embedded in technology.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TECH_DETERMINISM_SYSTEM = """You are a technological determinism specialist. Given a claim about technology, assess whether it inappropriately treats technology as autonomous:

Key concepts:
- Technological determinism: technology as autonomous force
- Tech inevitability: treating outcomes as predetermined
- Design invisibility: ignoring choices embedded in technology
- Agency erasure: removing human responsibility for tech outcomes
- Progress narrative: technology as inevitable improvement
- Tool neutrality myth: treating tools as value-free
- Automation as destiny: treating automation as inevitable

When technological determinism IS present:
- Technology treated as autonomous force
- Outcomes presented as inevitable
- Design choices made invisible
- Human agency in tech development denied
- Progress assumed without evaluation
- Tools treated as value-neutral
- Political decisions hidden in technical ones

When technology analysis is appropriate:
- Technology understood as human creation
- Outcomes seen as result of choices
- Design decisions made visible
- Human agency acknowledged
- Progress evaluated not assumed
- Values embedded in tools recognized
- Technical and political distinguished

Output JSON with: determinism_present (bool), severity (none/mild/moderate/severe), claim (what claim is made), technology (what technology is discussed), agency_erased (what human agency is erased), choices_hidden (what design choices are hidden), recommendation (appropriate_tech_analysis/mild_deterministic_framing/significant_tech_determinism/major_agency_erasure/restore_human_agency)."""

TECH_DETERMINISM_PROMPT = """Detect technological determinism:

Claim: {claim}
Technology discussed: {technology}
Agency acknowledged: {agency}
Design choices visible: {choices}
Domain: {domain}
Context: {context}

Is technology being treated as an autonomous force that determines outcomes? Return ONLY valid JSON."""


class TechDeterminismService:
    """Detects technological determinism — treating technology as autonomous force."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        technology: str = "",
        agency: str = "",
        choices: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect technological determinism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TECH_DETERMINISM_PROMPT.format(
                claim=claim,
                technology=technology or "Not specified",
                agency=agency or "Not specified",
                choices=choices or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=TECH_DETERMINISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "determinism_present": data.get("determinism_present", False),
            "severity": data.get("severity", ""),
            "technology": data.get("technology", ""),
            "agency_erased": data.get("agency_erased", ""),
            "choices_hidden": data.get("choices_hidden", ""),
            "recommendation": data.get("recommendation", ""),
        }
