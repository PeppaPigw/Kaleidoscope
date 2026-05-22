"""EpistemicTechnologyAlgorithmOpacityService — Epistemic Technology Algorithm Opacity Detection.

Detects epistemic technology algorithm opacity — black-box systems
preventing epistemic accountability.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TECHNOLOGY_ALGORITHM_OPACITY_SYSTEM = """You are an epistemic technology algorithm opacity specialist. Given decision opacity, assess black-box accountability failure:

Key concepts:
- Algorithm opacity: black-box systems preventing epistemic accountability
- Decision opacity: inability to know why a system produced an outcome
- Explainability gap: missing intelligible reasons for automated judgments
- Audit impossibility: inability to inspect, test, or challenge the process
- Accountability void: no responsible agent can justify the decision

When algorithm opacity IS present:
- Decisions cannot be explained
- Explanations are too vague or post hoc
- Audits cannot reconstruct the reasoning
- Accountability is displaced onto the system
- Affected parties cannot challenge outcomes

When no algorithm opacity:
- Decision logic can be explained
- Explanations support meaningful challenge
- Audits can inspect relevant inputs and processes
- Accountability remains assigned
- System limits are transparent

Output JSON with: algorithm_opacity_detected (bool), severity (none/mild/moderate/severe), explainability_gap (what explanation is missing), audit_impossibility (what cannot be audited), accountability_void (what accountability is displaced), recommendation (no_algorithm_opacity/mild_explainability_improvement/significant_audit_access/major_accountability_repair/emergency_black_box_suspension)."""

EPISTEMIC_TECHNOLOGY_ALGORITHM_OPACITY_PROMPT = """Detect epistemic technology algorithm opacity:

Decision opacity: {decision_opacity}
Explainability gap: {explainability_gap}
Audit impossibility: {audit_impossibility}
Accountability void: {accountability_void}
Domain: {domain}
Context: {context}

Are black-box systems preventing epistemic accountability? Return ONLY valid JSON."""


class EpistemicTechnologyAlgorithmOpacityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision_opacity: str,
        *,
        explainability_gap: str = "",
        audit_impossibility: str = "",
        accountability_void: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TECHNOLOGY_ALGORITHM_OPACITY_PROMPT.format(
                decision_opacity=decision_opacity,
                explainability_gap=explainability_gap or "Not specified",
                audit_impossibility=audit_impossibility or "Not specified",
                accountability_void=accountability_void or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TECHNOLOGY_ALGORITHM_OPACITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision_opacity": decision_opacity[:200],
            "algorithm_opacity_detected": data.get("algorithm_opacity_detected", False),
            "severity": data.get("severity", ""),
            "explainability_gap": data.get("explainability_gap", ""),
            "audit_impossibility": data.get("audit_impossibility", ""),
            "accountability_void": data.get("accountability_void", ""),
            "recommendation": data.get("recommendation", ""),
        }
