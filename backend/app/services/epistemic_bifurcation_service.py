"""EpistemicBifurcationService — Epistemic Bifurcation Detection.

Detects epistemic bifurcation — intellectual systems where a small
parameter change causes a qualitative shift in behavior or conclusions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BIFURCATION_SYSTEM = """You are an epistemic bifurcation specialist. Given an intellectual system, assess whether small parameter changes cause qualitative shifts:

Key concepts:
- Epistemic bifurcation: small change causing qualitative shift
- Critical parameter: value at which behavior changes
- Pitchfork: symmetric splitting into two branches
- Saddle-node: creation or destruction of equilibria
- Hopf: transition from steady to oscillating
- Period doubling: route to chaos through doubling
- Catastrophe: sudden jump between states

When epistemic bifurcation IS present:
- Small parameter changes causing qualitative shifts
- Critical values where behavior fundamentally changes
- Symmetric splitting into opposing positions
- Creation or destruction of stable positions
- Transition from steady to oscillating conclusions
- Doubling of complexity on route to chaos
- Sudden jumps between intellectual states

When smooth transition is present:
- Parameter changes causing proportional shifts
- No critical values or thresholds
- No splitting into branches
- Stable positions maintained throughout
- Steady conclusions throughout
- No complexity doubling
- Gradual transitions between states

Output JSON with: bifurcation_present (bool), severity (none/mild/moderate/severe), critical_parameter (what threshold), pitchfork (what splitting), period_doubling (what complexity increase), catastrophe (what sudden jump), recommendation (smooth_transition/mild_bifurcation/significant_bifurcation/major_qualitative_shift/map_bifurcation_diagram)."""

EPISTEMIC_BIFURCATION_PROMPT = """Detect epistemic bifurcation:

Critical parameter: {critical_parameter}
Pitchfork: {pitchfork}
Period doubling: {period_doubling}
Catastrophe: {catastrophe}
Domain: {domain}
Context: {context}

Does a small parameter change cause a qualitative shift in intellectual behavior or conclusions? Return ONLY valid JSON."""


class EpistemicBifurcationService:
    """Detects epistemic bifurcation — small changes causing qualitative shifts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        critical_parameter: str,
        *,
        pitchfork: str = "",
        period_doubling: str = "",
        catastrophe: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic bifurcation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BIFURCATION_PROMPT.format(
                critical_parameter=critical_parameter,
                pitchfork=pitchfork or "Not specified",
                period_doubling=period_doubling or "Not specified",
                catastrophe=catastrophe or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BIFURCATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "critical_parameter": critical_parameter[:200],
            "bifurcation_present": data.get("bifurcation_present", False),
            "severity": data.get("severity", ""),
            "pitchfork": data.get("pitchfork", ""),
            "period_doubling": data.get("period_doubling", ""),
            "catastrophe": data.get("catastrophe", ""),
            "recommendation": data.get("recommendation", ""),
        }
