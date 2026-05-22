"""SensitivityAnalysisService — Conclusion Sensitivity to Assumptions.

Identifies which inputs/assumptions a conclusion is most sensitive to,
and how much the conclusion changes when you vary them. The intellectual
equivalent of "what if I'm wrong about X?"
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SENSITIVITY_SYSTEM = """You are a sensitivity analysis specialist. Given a conclusion and its supporting assumptions, identify:
- Which assumptions the conclusion is most sensitive to (small changes → big impact)
- Which assumptions are robust (can vary widely without changing the conclusion)
- The "tipping points" where changing an assumption flips the conclusion
- Whether the conclusion is fragile (depends on everything being right) or robust (survives most perturbations)

Output JSON with: parameters (list of: assumption, sensitivity (low/moderate/high/critical), current_value (what's assumed), tipping_point (at what value does the conclusion flip), if_wrong (what happens to the conclusion), confidence_in_assumption (0-1)), most_sensitive (the assumption that matters most), robustness_score (0-1, how robust is the conclusion to perturbation), fragility_profile (fragile/moderate/robust/antifragile), worst_case (what happens if the most sensitive assumptions are all wrong), recommendation (what to verify first)."""

SENSITIVITY_PROMPT = """Analyze sensitivity of this conclusion:

Conclusion: {conclusion}
Key assumptions: {assumptions}
Domain: {domain}
Context: {context}

Which assumptions matter most? Return ONLY valid JSON."""


class SensitivityAnalysisService:
    """Analyzes how sensitive conclusions are to their assumptions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze(
        self,
        conclusion: str,
        assumptions: list[str],
        *,
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Analyze sensitivity of a conclusion to its assumptions."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        assumptions_formatted = "\n".join(f"- {a}" for a in assumptions[:8])

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SENSITIVITY_PROMPT.format(
                conclusion=conclusion,
                assumptions=assumptions_formatted,
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SENSITIVITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        params = data.get("parameters", [])
        return {
            "conclusion": conclusion[:200],
            "parameters_analyzed": len(params),
            "parameters": params,
            "most_sensitive": data.get("most_sensitive", ""),
            "robustness_score": data.get("robustness_score", 0),
            "fragility_profile": data.get("fragility_profile", ""),
            "worst_case": data.get("worst_case", ""),
            "recommendation": data.get("recommendation", ""),
        }
