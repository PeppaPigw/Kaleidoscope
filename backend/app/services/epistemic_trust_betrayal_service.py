"""EpistemicTrustBetrayalService — Epistemic Trust Betrayal Detection.

Detects epistemic trust betrayal — betrayal of intellectual trust
where ideas shared in confidence are misused or weaponized.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TRUST_BETRAYAL_SYSTEM = """You are an epistemic trust betrayal specialist. Given betrayal of intellectual trust, assess trust betrayal:

Key concepts:
- Epistemic trust betrayal: ideas shared in confidence misused
- Confidence violation: sharing private intellectual work without permission
- Idea theft: taking credit for shared ideas
- Vulnerability exploitation: using shared doubts against someone
- Intellectual backstabbing: using private knowledge to undermine
- Trust weaponization: turning shared vulnerability into weapon
- Betrayal aftermath: lasting damage from intellectual betrayal

When epistemic trust betrayal IS present:
- Ideas shared in confidence misused
- Private work shared without permission
- Taking credit for shared ideas
- Using doubts against someone
- Using private knowledge to undermine
- Turning vulnerability into weapon
- Lasting damage from betrayal

When no trust betrayal:
- Confidence respected
- Private work protected
- Credit given appropriately
- Doubts held safely
- Private knowledge protected
- Vulnerability honored
- Trust maintained

Output JSON with: trust_betrayal_detected (bool), severity (none/mild/moderate/severe), confidence_violation (what shared without permission), idea_theft (what taking credit for), vulnerability_exploitation (what using against), betrayal_aftermath (what lasting damage), recommendation (no_trust_betrayal/mild_boundary_setting/significant_trust_rebuilding/major_intensive_betrayal_processing/emergency_severe_trust_destruction)."""

EPISTEMIC_TRUST_BETRAYAL_PROMPT = """Detect epistemic trust betrayal:

Confidence violation: {confidence_violation}
Idea theft: {idea_theft}
Vulnerability exploitation: {vulnerability_exploitation}
Betrayal aftermath: {betrayal_aftermath}
Domain: {domain}
Context: {context}

Is there betrayal of intellectual trust? Return ONLY valid JSON."""


class EpistemicTrustBetrayalService:
    """Detects epistemic trust betrayal — ideas shared in confidence misused."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        confidence_violation: str,
        *,
        idea_theft: str = "",
        vulnerability_exploitation: str = "",
        betrayal_aftermath: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic trust betrayal."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TRUST_BETRAYAL_PROMPT.format(
                confidence_violation=confidence_violation,
                idea_theft=idea_theft or "Not specified",
                vulnerability_exploitation=vulnerability_exploitation or "Not specified",
                betrayal_aftermath=betrayal_aftermath or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TRUST_BETRAYAL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "confidence_violation": confidence_violation[:200],
            "trust_betrayal_detected": data.get("trust_betrayal_detected", False),
            "severity": data.get("severity", ""),
            "idea_theft": data.get("idea_theft", ""),
            "vulnerability_exploitation": data.get("vulnerability_exploitation", ""),
            "betrayal_aftermath": data.get("betrayal_aftermath", ""),
            "recommendation": data.get("recommendation", ""),
        }
