"""EpistemicCodependencyService — Epistemic Codependency Detection.

Detects epistemic codependency — excessive reliance on another's intellectual
validation to the point of losing one's own epistemic autonomy.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CODEPENDENCY_SYSTEM = """You are an epistemic codependency specialist. Given excessive intellectual reliance, assess codependency:

Key concepts:
- Epistemic codependency: excessive reliance on other's validation
- Lost autonomy: cannot form beliefs independently
- Caretaking: managing other's intellectual needs at own expense
- Enabling: supporting other's epistemic dysfunction
- Boundary dissolution: where their thinking ends and mine begins
- Self-neglect: ignoring own intellectual needs
- Control through helping: maintaining relationship through indispensability

When epistemic codependency IS present:
- Excessive reliance on validation
- Cannot form beliefs independently
- Managing other's needs at own expense
- Supporting dysfunction
- Boundary dissolution
- Ignoring own needs
- Control through helping

When no codependency:
- Healthy interdependence
- Independent belief formation
- Balanced intellectual exchange
- Supporting growth
- Clear boundaries
- Own needs met
- Genuine collaboration

Output JSON with: codependency_detected (bool), severity (none/mild/moderate/severe), autonomy_loss (what independence lost), boundary_pattern (what dissolution), enabling_behavior (what supporting dysfunction), self_neglect (what ignoring), recommendation (no_codependency/mild_boundary_building/significant_autonomy_therapy/major_intensive_treatment/emergency_complete_fusion)."""

EPISTEMIC_CODEPENDENCY_PROMPT = """Detect epistemic codependency:

Autonomy loss: {autonomy_loss}
Boundary pattern: {boundary_pattern}
Enabling behavior: {enabling_behavior}
Self neglect: {self_neglect}
Domain: {domain}
Context: {context}

Is there excessive reliance on another's intellectual validation losing epistemic autonomy? Return ONLY valid JSON."""


class EpistemicCodependencyService:
    """Detects epistemic codependency — excessive intellectual reliance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        autonomy_loss: str,
        *,
        boundary_pattern: str = "",
        enabling_behavior: str = "",
        self_neglect: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic codependency."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CODEPENDENCY_PROMPT.format(
                autonomy_loss=autonomy_loss,
                boundary_pattern=boundary_pattern or "Not specified",
                enabling_behavior=enabling_behavior or "Not specified",
                self_neglect=self_neglect or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CODEPENDENCY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "autonomy_loss": autonomy_loss[:200],
            "codependency_detected": data.get("codependency_detected", False),
            "severity": data.get("severity", ""),
            "boundary_pattern": data.get("boundary_pattern", ""),
            "enabling_behavior": data.get("enabling_behavior", ""),
            "self_neglect": data.get("self_neglect", ""),
            "recommendation": data.get("recommendation", ""),
        }
