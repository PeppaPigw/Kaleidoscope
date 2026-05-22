"""EpistemicSurvivorGuiltService — Epistemic Survivor Guilt Detection.

Detects epistemic survivor guilt — guilt over succeeding intellectually
where peers or colleagues failed.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SURVIVOR_GUILT_SYSTEM = """You are an epistemic survivor guilt specialist. Given guilt over succeeding where others failed, assess survivor guilt:

Key concepts:
- Epistemic survivor guilt: guilt over succeeding where peers failed
- Success shame: feeling bad about achievements when others struggle
- Peer comparison guilt: guilt when outperforming colleagues
- Advancement guilt: guilt about promotions or recognition
- Publication guilt: guilt about publishing when others can't
- Selection guilt: guilt about being chosen over others
- Thriving guilt: guilt about flourishing in difficult conditions

When epistemic survivor guilt IS present:
- Guilt over succeeding where peers failed
- Feeling bad about achievements
- Guilt when outperforming
- Guilt about advancement
- Guilt about publishing
- Guilt about being chosen
- Guilt about flourishing

When no survivor guilt:
- Celebrating success freely
- Comfortable with achievement
- Healthy competition
- Grateful for advancement
- Proud of publications
- Accepting selection
- Enjoying flourishing

Output JSON with: survivor_guilt_detected (bool), severity (none/mild/moderate/severe), success_shame (what feeling bad about), peer_comparison_guilt (what outperforming), advancement_guilt (what advancing past), selection_guilt (what being chosen over), recommendation (no_survivor_guilt/mild_celebration_practice/significant_guilt_processing/major_intensive_survivor_work/emergency_paralyzing_success_guilt)."""

EPISTEMIC_SURVIVOR_GUILT_PROMPT = """Detect epistemic survivor guilt:

Success shame: {success_shame}
Peer comparison guilt: {peer_comparison_guilt}
Advancement guilt: {advancement_guilt}
Selection guilt: {selection_guilt}
Domain: {domain}
Context: {context}

Is there guilt over succeeding where peers failed? Return ONLY valid JSON."""


class EpistemicSurvivorGuiltService:
    """Detects epistemic survivor guilt — guilt over succeeding where peers failed."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        success_shame: str,
        *,
        peer_comparison_guilt: str = "",
        advancement_guilt: str = "",
        selection_guilt: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic survivor guilt."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SURVIVOR_GUILT_PROMPT.format(
                success_shame=success_shame,
                peer_comparison_guilt=peer_comparison_guilt or "Not specified",
                advancement_guilt=advancement_guilt or "Not specified",
                selection_guilt=selection_guilt or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SURVIVOR_GUILT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "success_shame": success_shame[:200],
            "survivor_guilt_detected": data.get("survivor_guilt_detected", False),
            "severity": data.get("severity", ""),
            "peer_comparison_guilt": data.get("peer_comparison_guilt", ""),
            "advancement_guilt": data.get("advancement_guilt", ""),
            "selection_guilt": data.get("selection_guilt", ""),
            "recommendation": data.get("recommendation", ""),
        }
