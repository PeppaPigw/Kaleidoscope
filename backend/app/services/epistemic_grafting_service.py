"""EpistemicGraftingService — Epistemic Grafting Detection.

Detects epistemic grafting — foreign ideas grafted onto incompatible
root systems, creating unstable hybrid knowledge.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GRAFTING_SYSTEM = """You are an epistemic grafting specialist. Given a knowledge combination, assess whether foreign ideas are grafted onto incompatible foundations:

Key concepts:
- Epistemic grafting: foreign ideas attached to incompatible foundations
- Incompatible rootstock: foundation that cannot support the grafted idea
- Rejection risk: risk of the graft being rejected
- Hybrid instability: unstable combination of incompatible elements
- Surface attachment: ideas attached superficially without deep integration
- Nutrient mismatch: foundation unable to nourish the grafted idea
- Graft failure: eventual failure of the incompatible combination

When epistemic grafting IS present:
- Foreign ideas attached to incompatible foundations
- Foundation unable to support the grafted concept
- Risk of rejection as incompatibility becomes apparent
- Unstable combination of incompatible intellectual elements
- Ideas attached superficially without deep integration
- Foundation unable to nourish or develop the grafted idea
- Eventual failure likely as incompatibility manifests

When compatible integration is present:
- Ideas integrated with compatible foundations
- Foundation able to support new concepts
- No rejection risk from incompatibility
- Stable combination of compatible elements
- Ideas deeply integrated with foundation
- Foundation able to nourish and develop new ideas
- Sustainable combination likely to thrive

Output JSON with: grafting_present (bool), severity (none/mild/moderate/severe), idea (what idea is grafted), rootstock (what incompatible foundation), incompatibility (what incompatibility exists), rejection_risk (what rejection risk), recommendation (compatible_integration/mild_mismatch/significant_grafting/major_incompatibility/find_compatible_foundation)."""

EPISTEMIC_GRAFTING_PROMPT = """Detect epistemic grafting:

Idea: {idea}
Rootstock: {rootstock}
Incompatibility: {incompatibility}
Rejection risk: {rejection_risk}
Domain: {domain}
Context: {context}

Are foreign ideas grafted onto incompatible intellectual foundations? Return ONLY valid JSON."""


class EpistemicGraftingService:
    """Detects epistemic grafting — ideas on incompatible foundations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        idea: str,
        *,
        rootstock: str = "",
        incompatibility: str = "",
        rejection_risk: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic grafting."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GRAFTING_PROMPT.format(
                idea=idea,
                rootstock=rootstock or "Not specified",
                incompatibility=incompatibility or "Not specified",
                rejection_risk=rejection_risk or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GRAFTING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "idea": idea[:200],
            "grafting_present": data.get("grafting_present", False),
            "severity": data.get("severity", ""),
            "rootstock": data.get("rootstock", ""),
            "incompatibility": data.get("incompatibility", ""),
            "rejection_risk": data.get("rejection_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }
