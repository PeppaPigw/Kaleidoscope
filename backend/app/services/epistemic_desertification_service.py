"""EpistemicDesertificationService — Epistemic Desertification Detection.

Detects epistemic desertification — the degradation of knowledge
ecosystems through defunding, neglect, or active destruction,
creating knowledge deserts where inquiry cannot flourish.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DESERTIFICATION_SYSTEM = """You are an epistemic desertification specialist. Given a knowledge ecosystem, assess whether it is being degraded:

Key concepts:
- Epistemic desertification: degradation of knowledge ecosystems
- Knowledge desert: areas where inquiry cannot flourish
- Institutional decay: degradation of knowledge-producing institutions
- Defunding knowledge: removing resources for inquiry
- Brain drain: loss of knowledge workers from an ecosystem
- Infrastructure collapse: loss of knowledge infrastructure
- Epistemic neglect: allowing knowledge systems to decay

When epistemic desertification IS present:
- Knowledge-producing institutions being degraded
- Resources for inquiry being removed
- Knowledge workers leaving or being driven out
- Infrastructure for knowledge production collapsing
- Neglect allowing knowledge systems to decay
- Active destruction of knowledge institutions
- Knowledge deserts forming where inquiry once flourished

When resource reallocation is appropriate:
- Resources shifted to more productive areas
- Institutions reformed rather than destroyed
- Knowledge workers supported in transition
- Infrastructure maintained or upgraded
- Changes serve knowledge production
- Reallocation based on epistemic merit
- New institutions replace old ones

Output JSON with: desertification_present (bool), severity (none/mild/moderate/severe), ecosystem (what ecosystem is affected), degradation (what degradation occurs), cause (what causes degradation), consequence (what knowledge is lost), recommendation (appropriate_resource_reallocation/mild_institutional_stress/significant_epistemic_desertification/major_knowledge_desert/restore_knowledge_ecosystem)."""

EPISTEMIC_DESERTIFICATION_PROMPT = """Detect epistemic desertification:

Ecosystem: {ecosystem}
Degradation observed: {degradation}
Cause: {cause}
Resources: {resources}
Domain: {domain}
Context: {context}

Is the knowledge ecosystem being degraded, creating knowledge deserts? Return ONLY valid JSON."""


class EpistemicDesertificationService:
    """Detects epistemic desertification — degradation of knowledge ecosystems."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        ecosystem: str,
        *,
        degradation: str = "",
        cause: str = "",
        resources: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic desertification."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DESERTIFICATION_PROMPT.format(
                ecosystem=ecosystem,
                degradation=degradation or "Not specified",
                cause=cause or "Not specified",
                resources=resources or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DESERTIFICATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "ecosystem": ecosystem[:200],
            "desertification_present": data.get("desertification_present", False),
            "severity": data.get("severity", ""),
            "degradation": data.get("degradation", ""),
            "cause": data.get("cause", ""),
            "consequence": data.get("consequence", ""),
            "recommendation": data.get("recommendation", ""),
        }
