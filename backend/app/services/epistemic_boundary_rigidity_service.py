"""EpistemicBoundaryRigidityService — Epistemic Boundary Rigidity Detection.

Detects epistemic boundary rigidity — overly rigid intellectual boundaries
that prevent learning from others.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BOUNDARY_RIGIDITY_SYSTEM = """You are an epistemic boundary rigidity specialist. Given overly rigid intellectual boundaries, assess boundary rigidity:

Key concepts:
- Epistemic boundary rigidity: overly rigid boundaries preventing learning
- Intellectual fortress: walls so high nothing gets in
- Input rejection: automatically rejecting all external ideas
- Learning blockade: boundaries preventing any new information
- Defensive isolation: rigidity as protection from influence
- Impermeability: no ideas can penetrate the boundary
- Growth prevention: rigidity stopping intellectual development

When epistemic boundary rigidity IS present:
- Overly rigid boundaries preventing learning
- Walls so high nothing gets in
- Automatically rejecting external ideas
- Boundaries preventing new information
- Rigidity as protection
- No ideas penetrating
- Rigidity stopping growth

When no boundary rigidity:
- Flexible boundaries
- Open to input
- Evaluating external ideas
- Permeable to information
- Appropriate protection
- Ideas can enter
- Boundaries support growth

Output JSON with: boundary_rigidity_detected (bool), severity (none/mild/moderate/severe), intellectual_fortress (what walling off), input_rejection (what automatically rejecting), learning_blockade (what preventing learning about), defensive_isolation (what protecting from), recommendation (no_boundary_rigidity/mild_flexibility_practice/significant_permeability_building/major_intensive_opening_work/emergency_complete_intellectual_fortress)."""

EPISTEMIC_BOUNDARY_RIGIDITY_PROMPT = """Detect epistemic boundary rigidity:

Intellectual fortress: {intellectual_fortress}
Input rejection: {input_rejection}
Learning blockade: {learning_blockade}
Defensive isolation: {defensive_isolation}
Domain: {domain}
Context: {context}

Is there overly rigid intellectual boundaries preventing learning from others? Return ONLY valid JSON."""


class EpistemicBoundaryRigidityService:
    """Detects epistemic boundary rigidity — overly rigid intellectual boundaries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        intellectual_fortress: str,
        *,
        input_rejection: str = "",
        learning_blockade: str = "",
        defensive_isolation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic boundary rigidity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BOUNDARY_RIGIDITY_PROMPT.format(
                intellectual_fortress=intellectual_fortress,
                input_rejection=input_rejection or "Not specified",
                learning_blockade=learning_blockade or "Not specified",
                defensive_isolation=defensive_isolation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BOUNDARY_RIGIDITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "intellectual_fortress": intellectual_fortress[:200],
            "boundary_rigidity_detected": data.get("boundary_rigidity_detected", False),
            "severity": data.get("severity", ""),
            "input_rejection": data.get("input_rejection", ""),
            "learning_blockade": data.get("learning_blockade", ""),
            "defensive_isolation": data.get("defensive_isolation", ""),
            "recommendation": data.get("recommendation", ""),
        }
