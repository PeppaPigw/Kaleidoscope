"""EpistemicImmunodeficiencyService — Epistemic Immunodeficiency Detection.

Detects epistemic immunodeficiency — failure to reject harmful
or false ideas that should be filtered out.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_IMMUNODEFICIENCY_SYSTEM = """You are an epistemic immunodeficiency specialist. Given a knowledge system, assess whether it fails to reject harmful or false ideas:

Key concepts:
- Epistemic immunodeficiency: failure to reject harmful ideas
- Critical thinking failure: critical thinking not functioning
- Filter failure: filters not catching false ideas
- Gullibility: accepting ideas without scrutiny
- Defense absence: absence of intellectual defenses
- Vulnerability: vulnerable to misinformation
- Quality control failure: quality control not functioning

When epistemic immunodeficiency IS present:
- Failure to reject harmful or false ideas
- Critical thinking not functioning
- Filters not catching false or harmful ideas
- Accepting ideas without appropriate scrutiny
- Absence of intellectual defenses
- Vulnerable to misinformation and bad ideas
- Quality control not functioning

When healthy openness is present:
- Openness combined with appropriate scrutiny
- Critical thinking functioning well
- Filters catching genuinely harmful ideas
- Ideas evaluated before acceptance
- Intellectual defenses proportionate
- Protected against misinformation
- Quality control functioning

Output JSON with: immunodeficiency_present (bool), severity (none/mild/moderate/severe), system (what system is deficient), failure (what filtering fails), vulnerability (what vulnerability exists), harmful_ideas (what harmful ideas get through), recommendation (healthy_openness/mild_laxity/significant_immunodeficiency/major_defense_failure/strengthen_critical_filters)."""

EPISTEMIC_IMMUNODEFICIENCY_PROMPT = """Detect epistemic immunodeficiency:

System: {system}
Failure: {failure}
Vulnerability: {vulnerability}
Harmful ideas: {harmful_ideas}
Domain: {domain}
Context: {context}

Does the system fail to reject harmful or false ideas? Return ONLY valid JSON."""


class EpistemicImmunodeficiencyService:
    """Detects epistemic immunodeficiency — failure to reject harmful ideas."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        system: str,
        *,
        failure: str = "",
        vulnerability: str = "",
        harmful_ideas: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic immunodeficiency."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_IMMUNODEFICIENCY_PROMPT.format(
                system=system,
                failure=failure or "Not specified",
                vulnerability=vulnerability or "Not specified",
                harmful_ideas=harmful_ideas or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_IMMUNODEFICIENCY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "system": system[:200],
            "immunodeficiency_present": data.get("immunodeficiency_present", False),
            "severity": data.get("severity", ""),
            "failure": data.get("failure", ""),
            "vulnerability": data.get("vulnerability", ""),
            "harmful_ideas": data.get("harmful_ideas", ""),
            "recommendation": data.get("recommendation", ""),
        }
