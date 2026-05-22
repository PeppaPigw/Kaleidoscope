"""IncentiveAnalyzerService — Incentive Structure Analysis.

Maps the incentive structures around a claim or research area.
Identifies who benefits from the claim being true/false, what
incentives shape the research, and where incentive misalignment
might distort findings.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

INCENTIVE_SYSTEM = """You are an incentive structure analyst. Given a research claim or area, map the incentives:
- Who benefits if this claim is true? Who benefits if it's false?
- What incentives do the researchers have? (funding, career, ideology)
- Are there institutional pressures that shape findings?
- Is there a "publish or perish" effect distorting the research?
- Who funds this research and what do they want to find?
- Are there regulatory or legal incentives that shape conclusions?

Output JSON with: beneficiaries_if_true (list of: actor, benefit, magnitude), beneficiaries_if_false (list of: actor, benefit, magnitude), researcher_incentives (list of: incentive, direction_of_bias, strength (weak/moderate/strong)), funding_influence (who funds and what they want), institutional_pressures (list), career_incentives (how career incentives shape research), overall_incentive_alignment (0-1, 0=incentives strongly bias toward one conclusion, 1=neutral), bias_direction (which conclusion incentives push toward), trust_discount (0-1, how much to discount the claim given incentive misalignment), what_would_change_incentives (how to realign incentives)."""

INCENTIVE_PROMPT = """Analyze incentive structures:

Claim/Area: {claim}
Key actors: {actors}
Funding sources: {funding}
Domain: {domain}

Who benefits and how do incentives shape this? Return ONLY valid JSON."""


class IncentiveAnalyzerService:
    """Analyzes incentive structures around research claims."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze(
        self,
        claim: str,
        *,
        actors: str = "",
        funding: str = "",
        domain: str = "",
    ) -> dict:
        """Analyze incentive structures."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=INCENTIVE_PROMPT.format(
                claim=claim,
                actors=actors or "Not specified",
                funding=funding or "Not specified",
                domain=domain or "general",
            ),
            system=INCENTIVE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "beneficiaries_if_true": data.get("beneficiaries_if_true", []),
            "beneficiaries_if_false": data.get("beneficiaries_if_false", []),
            "researcher_incentives": data.get("researcher_incentives", []),
            "funding_influence": data.get("funding_influence", ""),
            "institutional_pressures": data.get("institutional_pressures", []),
            "overall_incentive_alignment": data.get("overall_incentive_alignment", 0),
            "bias_direction": data.get("bias_direction", ""),
            "trust_discount": data.get("trust_discount", 0),
            "what_would_change": data.get("what_would_change_incentives", ""),
        }
