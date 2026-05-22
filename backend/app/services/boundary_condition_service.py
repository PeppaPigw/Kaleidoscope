"""BoundaryConditionService — Validity Envelope & Edge Case Finder.

Identifies the conditions under which a claim, finding, or theory
breaks down. Maps the boundary of its validity — where it works,
where it stops working, and what changes at the boundary.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

BOUNDARY_SYSTEM = """You are a boundary condition specialist. Given a claim or finding, map where it stops being true:
- Under what conditions does it hold?
- Under what conditions does it break down?
- What changes at the boundary (gradual degradation or sudden failure)?
- Are there phase transitions (works perfectly until X, then fails completely)?
- What are the implicit scope conditions that are rarely stated?

Output JSON with: validity_conditions (list of conditions where the claim holds), boundary_conditions (list of: condition, what_happens_at_boundary, failure_mode (gradual/sudden/catastrophic)), implicit_scope (unstated assumptions about when this applies), phase_transitions (list of: threshold, before, after), edge_cases (list of: case, why_it_breaks, severity), robustness_score (0-1, how wide the validity envelope is), narrowest_constraint (the condition most likely to be violated), real_world_violations (scenarios where boundary conditions are commonly violated without people realizing), safe_operating_range (where you can confidently apply this), danger_zone (where it might still work but you're near the edge)."""

BOUNDARY_PROMPT = """Find boundary conditions:

Claim/Finding: {claim}
Stated scope: {stated_scope}
Domain: {domain}
Context: {context}

Where does this stop being true? Return ONLY valid JSON."""


class BoundaryConditionService:
    """Finds boundary conditions and validity envelopes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find(
        self,
        claim: str,
        *,
        stated_scope: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Find boundary conditions."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BOUNDARY_PROMPT.format(
                claim=claim,
                stated_scope=stated_scope or "Not explicitly stated",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=BOUNDARY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "validity_conditions": data.get("validity_conditions", []),
            "boundary_conditions": data.get("boundary_conditions", []),
            "implicit_scope": data.get("implicit_scope", []),
            "phase_transitions": data.get("phase_transitions", []),
            "edge_cases": data.get("edge_cases", []),
            "robustness_score": data.get("robustness_score", 0),
            "narrowest_constraint": data.get("narrowest_constraint", ""),
            "real_world_violations": data.get("real_world_violations", []),
            "safe_operating_range": data.get("safe_operating_range", ""),
            "danger_zone": data.get("danger_zone", ""),
        }
