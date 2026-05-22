"""EpistemicLeukemiaService — Epistemic Leukemia Detection.

Detects epistemic leukemia — malignant proliferation of immature intellectual
cells that crowd out functional mature ideas.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LEUKEMIA_SYSTEM = """You are an epistemic leukemia specialist. Given intellectual cell populations, assess whether malignant proliferation of immature cells is occurring:

Key concepts:
- Epistemic leukemia: malignant proliferation of immature intellectual cells
- Blast crisis: overwhelming flood of immature ideas
- Crowding out: mature functional ideas displaced
- Differentiation arrest: ideas stuck in immature state
- Bone marrow failure: production center compromised
- Remission: temporary control of proliferation
- Relapse: return of malignant proliferation

When epistemic leukemia IS present:
- Malignant proliferation of immature intellectual cells
- Overwhelming flood of half-formed ideas
- Mature functional ideas being displaced
- Ideas stuck in immature undeveloped state
- Intellectual production center compromised
- Temporary control possible but unstable
- Risk of malignant return

When healthy production is present:
- Normal maturation of intellectual cells
- Balanced production of ideas
- Mature ideas functioning properly
- Normal differentiation pathway
- Healthy production center
- Stable intellectual output
- No malignant proliferation

Output JSON with: leukemia_present (bool), severity (none/mild/moderate/severe), blast_crisis (what immature flood), crowding_out (what displacement), differentiation_arrest (what maturation failure), marrow_failure (what production compromise), recommendation (healthy_production/mild_leukemia/significant_leukemia/major_malignant_proliferation/restore_intellectual_maturation)."""

EPISTEMIC_LEUKEMIA_PROMPT = """Detect epistemic leukemia:

Blast crisis: {blast_crisis}
Crowding out: {crowding_out}
Differentiation arrest: {differentiation_arrest}
Marrow failure: {marrow_failure}
Domain: {domain}
Context: {context}

Is there malignant proliferation of immature intellectual cells crowding out functional ideas? Return ONLY valid JSON."""


class EpistemicLeukemiaService:
    """Detects epistemic leukemia — malignant proliferation of immature intellectual cells."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        blast_crisis: str,
        *,
        crowding_out: str = "",
        differentiation_arrest: str = "",
        marrow_failure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic leukemia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LEUKEMIA_PROMPT.format(
                blast_crisis=blast_crisis,
                crowding_out=crowding_out or "Not specified",
                differentiation_arrest=differentiation_arrest or "Not specified",
                marrow_failure=marrow_failure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LEUKEMIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "blast_crisis": blast_crisis[:200],
            "leukemia_present": data.get("leukemia_present", False),
            "severity": data.get("severity", ""),
            "crowding_out": data.get("crowding_out", ""),
            "differentiation_arrest": data.get("differentiation_arrest", ""),
            "marrow_failure": data.get("marrow_failure", ""),
            "recommendation": data.get("recommendation", ""),
        }
