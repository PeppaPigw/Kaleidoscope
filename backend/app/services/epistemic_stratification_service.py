"""EpistemicStratificationService — Epistemic Stratification Detection.

Detects epistemic stratification — knowledge layered in ways that
privilege certain interpretations over others.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_STRATIFICATION_SYSTEM = """You are an epistemic stratification specialist. Given a knowledge organization pattern, assess whether layering privileges certain interpretations:

Key concepts:
- Epistemic stratification: knowledge layered to privilege interpretations
- Layer privilege: certain layers given priority over others
- Interpretation hierarchy: hierarchy of interpretations
- Depth privilege: deeper layers assumed more fundamental
- Surface dismissal: surface knowledge dismissed as superficial
- Canonical ordering: ordering that privileges certain readings
- Access stratification: different access to different layers

When epistemic stratification IS present:
- Knowledge layered to privilege certain interpretations
- Certain layers given unwarranted priority
- Hierarchy of interpretations imposed
- Deeper layers assumed more fundamental without justification
- Surface knowledge dismissed without evaluation
- Canonical ordering privileging certain readings
- Different access to different knowledge layers

When fair organization is present:
- Knowledge organized without privileging interpretations
- All layers given appropriate consideration
- Interpretations evaluated on merit
- Depth not assumed to equal importance
- All levels of knowledge valued appropriately
- Organization based on utility not privilege
- Equal access to all knowledge layers

Output JSON with: stratification_present (bool), severity (none/mild/moderate/severe), knowledge (what knowledge is stratified), privileged (what interpretation is privileged), mechanism (how stratification works), excluded (what is excluded), recommendation (fair_organization/mild_hierarchy/significant_stratification/major_interpretation_privilege/flatten_access)."""

EPISTEMIC_STRATIFICATION_PROMPT = """Detect epistemic stratification:

Knowledge: {knowledge}
Privileged: {privileged}
Mechanism: {mechanism}
Excluded: {excluded}
Domain: {domain}
Context: {context}

Is knowledge layered in ways that privilege certain interpretations? Return ONLY valid JSON."""


class EpistemicStratificationService:
    """Detects epistemic stratification — knowledge layered to privilege interpretations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge: str,
        *,
        privileged: str = "",
        mechanism: str = "",
        excluded: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic stratification."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_STRATIFICATION_PROMPT.format(
                knowledge=knowledge,
                privileged=privileged or "Not specified",
                mechanism=mechanism or "Not specified",
                excluded=excluded or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_STRATIFICATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge": knowledge[:200],
            "stratification_present": data.get("stratification_present", False),
            "severity": data.get("severity", ""),
            "privileged": data.get("privileged", ""),
            "mechanism": data.get("mechanism", ""),
            "excluded": data.get("excluded", ""),
            "recommendation": data.get("recommendation", ""),
        }
