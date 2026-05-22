"""ExpertiseMapperService — Required Expertise Identification.

Identifies what expertise is needed to properly evaluate a research claim,
what disciplines should weigh in, and maps the expertise landscape for
a given research question.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EXPERTISE_SYSTEM = """You are an expertise mapping specialist. Given a research claim or question, identify exactly what expertise is needed to properly evaluate it. Consider: domain knowledge, methodological expertise, statistical skills, and interdisciplinary perspectives.

Output JSON with: expertise_map.claim, expertise_map.required_expertise (list of expertise_area/why_needed/criticality essential|important|helpful/typical_holder), expertise_map.disciplines_needed (list of discipline/contribution/weight 0-1), expertise_map.methodological_skills (list of skill/for_what), expertise_map.blind_spot_risk (what expertise is commonly missing from evaluation panels), expertise_map.ideal_panel (list of role/expertise/what_they_check), expertise_map.minimum_viable_review (smallest set of expertise that covers critical evaluation)."""

EXPERTISE_PROMPT = """Map required expertise:

Claim/Question: {claim}
Domain: {domain}
Methodology used: {methodology}

What expertise is needed to properly evaluate this? Return ONLY valid JSON."""


class ExpertiseMapperService:
    """Maps required expertise for research evaluation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def map_expertise(
        self,
        claim: str,
        *,
        domain: str = "",
        methodology: str = "",
    ) -> dict:
        """Identify what expertise is needed to evaluate a claim."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EXPERTISE_PROMPT.format(
                claim=claim,
                domain=domain or "research",
                methodology=methodology or "Not specified",
            ),
            system=EXPERTISE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        emap = data.get("expertise_map", data)

        return {
            "claim": claim,
            "required_expertise": emap.get("required_expertise", []),
            "disciplines_needed": emap.get("disciplines_needed", []),
            "methodological_skills": emap.get("methodological_skills", []),
            "blind_spot_risk": emap.get("blind_spot_risk", ""),
            "ideal_panel": emap.get("ideal_panel", []),
            "minimum_viable_review": emap.get("minimum_viable_review", []),
        }
