"""EpistemicArthroscopyService — Epistemic Arthroscopy Detection.

Detects need for epistemic arthroscopy — examining joint connections
between intellectual structures for damage or degeneration.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ARTHROSCOPY_SYSTEM = """You are an epistemic arthroscopy specialist. Given intellectual joint connections, assess whether damage exists at connection points:

Key concepts:
- Epistemic arthroscopy: examining intellectual joint connections
- Meniscal tear: cushioning between ideas torn
- Ligament damage: stabilizing connections weakened
- Synovitis: inflammation of joint lining
- Loose body: detached fragment floating in joint space
- Cartilage defect: smooth surface worn away
- Joint effusion: excess fluid from inflammation

When epistemic arthroscopy findings ARE present:
- Damage at intellectual connection points
- Cushioning between ideas torn
- Stabilizing connections weakened
- Inflammation of connection lining
- Detached fragments in joint space
- Smooth connection surface worn away
- Excess fluid from intellectual inflammation

When healthy joints are present:
- Intact connection points
- Full cushioning between ideas
- Strong stabilizing connections
- No inflammation
- No loose fragments
- Smooth intact surfaces
- Normal fluid levels

Output JSON with: arthroscopy_findings_present (bool), severity (none/mild/moderate/severe), meniscal_tear (what cushion damage), ligament_damage (what connection weakness), synovitis (what inflammation), loose_body (what detached fragment), recommendation (healthy_joints/mild_findings/significant_joint_damage/major_connection_failure/repair_intellectual_joints)."""

EPISTEMIC_ARTHROSCOPY_PROMPT = """Detect epistemic arthroscopy findings:

Meniscal tear: {meniscal_tear}
Ligament damage: {ligament_damage}
Synovitis: {synovitis}
Loose body: {loose_body}
Domain: {domain}
Context: {context}

Is there damage at the joint connections between intellectual structures? Return ONLY valid JSON."""


class EpistemicArthroscopyService:
    """Detects epistemic arthroscopy findings — intellectual joint connection damage."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        meniscal_tear: str,
        *,
        ligament_damage: str = "",
        synovitis: str = "",
        loose_body: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic arthroscopy findings."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ARTHROSCOPY_PROMPT.format(
                meniscal_tear=meniscal_tear,
                ligament_damage=ligament_damage or "Not specified",
                synovitis=synovitis or "Not specified",
                loose_body=loose_body or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ARTHROSCOPY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "meniscal_tear": meniscal_tear[:200],
            "arthroscopy_findings_present": data.get("arthroscopy_findings_present", False),
            "severity": data.get("severity", ""),
            "ligament_damage": data.get("ligament_damage", ""),
            "synovitis": data.get("synovitis", ""),
            "loose_body": data.get("loose_body", ""),
            "recommendation": data.get("recommendation", ""),
        }
