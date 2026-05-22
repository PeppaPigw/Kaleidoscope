"""EpistemicErosionService — Epistemic Erosion Detection.

Detects epistemic erosion — gradual wearing away of foundational
knowledge through neglect or disuse.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EROSION_SYSTEM = """You are an epistemic erosion specialist. Given a knowledge domain, assess whether foundational knowledge is being gradually worn away:

Key concepts:
- Epistemic erosion: gradual wearing away of foundational knowledge
- Foundation neglect: foundational knowledge neglected
- Knowledge weathering: knowledge degrading through exposure
- Skill atrophy: skills degrading through disuse
- Institutional memory loss: organizations losing foundational knowledge
- Conceptual thinning: concepts becoming thinner over time
- Understanding degradation: understanding degrading gradually

When epistemic erosion IS present:
- Foundational knowledge gradually wearing away
- Foundational knowledge neglected and degrading
- Knowledge degrading through lack of maintenance
- Skills degrading through disuse
- Organizations losing foundational knowledge
- Concepts becoming thinner and less substantive
- Understanding degrading gradually without notice

When healthy maintenance is present:
- Foundational knowledge actively maintained
- Foundations regularly revisited and reinforced
- Knowledge maintained through active use
- Skills kept sharp through practice
- Institutional memory actively preserved
- Concepts maintained at full depth
- Understanding actively maintained

Output JSON with: erosion_present (bool), severity (none/mild/moderate/severe), domain (what domain is affected), foundation (what foundation is eroding), mechanism (how erosion operates), consequence (what consequences result), recommendation (healthy_maintenance/mild_neglect/significant_erosion/major_foundation_loss/actively_maintain_foundations)."""

EPISTEMIC_EROSION_PROMPT = """Detect epistemic erosion:

Domain: {target_domain}
Foundation: {foundation}
Mechanism: {mechanism}
Consequence: {consequence}
Field: {field}
Context: {context}

Is foundational knowledge being gradually worn away through neglect? Return ONLY valid JSON."""


class EpistemicErosionService:
    """Detects epistemic erosion — foundational knowledge wearing away."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        target_domain: str,
        *,
        foundation: str = "",
        mechanism: str = "",
        consequence: str = "",
        field: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic erosion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EROSION_PROMPT.format(
                target_domain=target_domain,
                foundation=foundation or "Not specified",
                mechanism=mechanism or "Not specified",
                consequence=consequence or "Not specified",
                field=field or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EROSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "target_domain": target_domain[:200],
            "erosion_present": data.get("erosion_present", False),
            "severity": data.get("severity", ""),
            "foundation": data.get("foundation", ""),
            "mechanism": data.get("mechanism", ""),
            "consequence": data.get("consequence", ""),
            "recommendation": data.get("recommendation", ""),
        }
