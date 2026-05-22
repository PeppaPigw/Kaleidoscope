"""StakeholderImpactService — Stakeholder Impact Analysis.

Maps who is affected by a research finding or decision, how they're
affected, what their likely response will be, and where conflicts
of interest may arise.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

STAKEHOLDER_SYSTEM = """You are a stakeholder impact analyst. Given a finding or decision, map:
- Who is affected (directly and indirectly)
- How they're affected (positively, negatively, mixed)
- What their likely response will be (support, resist, ignore, co-opt)
- Where conflicts of interest arise
- Who has power to block or accelerate adoption
- Whose voices are missing from the conversation

Output JSON with: stakeholders (list of: group, impact_type (positive/negative/mixed/neutral), impact_magnitude (low/moderate/high/transformative), likely_response (support/resist/ignore/co-opt/adapt), power_level (low/moderate/high), interests (what they care about), conflict_with (other stakeholder groups they conflict with)), missing_voices (groups not represented), power_dynamics (who can block/accelerate), adoption_path (how to navigate stakeholder landscape), overall_controversy (0-1), coalition_potential (which groups might ally)."""

STAKEHOLDER_PROMPT = """Analyze stakeholder impact:

Finding/Decision: {finding}
Domain: {domain}
Context: {context}
Scope: {scope}

Who is affected and how? Return ONLY valid JSON."""


class StakeholderImpactService:
    """Analyzes stakeholder impact of findings and decisions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze(
        self,
        finding: str,
        *,
        domain: str = "",
        context: str = "",
        scope: str = "",
    ) -> dict:
        """Analyze stakeholder impact of a finding or decision."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=STAKEHOLDER_PROMPT.format(
                finding=finding,
                domain=domain or "general",
                context=context or "No additional context",
                scope=scope or "Broad",
            ),
            system=STAKEHOLDER_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)

        stakeholders = data.get("stakeholders", [])
        return {
            "finding": finding[:200],
            "stakeholders_count": len(stakeholders),
            "stakeholders": stakeholders,
            "missing_voices": data.get("missing_voices", []),
            "power_dynamics": data.get("power_dynamics", ""),
            "adoption_path": data.get("adoption_path", ""),
            "overall_controversy": data.get("overall_controversy", 0),
            "coalition_potential": data.get("coalition_potential", []),
        }
