"""ScopeInsensitivityService — Scope Insensitivity Detection.

Detects scope insensitivity (scope neglect) — the failure to
properly scale emotional, policy, or resource responses to the
magnitude of a problem. Saving 2,000 birds feels almost the same
as saving 200,000 birds. A million deaths is a statistic.
Kahneman's "psychophysical numbing."
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SCOPE_SYSTEM = """You are a scope insensitivity specialist. Given a problem and response, assess whether scope insensitivity is distorting judgment:

Key concepts:
- Psychophysical numbing: emotional response doesn't scale with magnitude
- "One death is a tragedy, a million is a statistic" (attributed to Stalin)
- Willingness-to-pay doesn't scale: people pay similar amounts to save 2K vs 200K birds
- Identifiable victim effect: one named victim gets more response than thousands of anonymous ones
- Proportion dominance: saving 80% of 100 feels better than saving 20% of 1000 (even though 200 > 80)
- Unit bias: treating one unit as the natural quantity regardless of actual scale

Assess:
- Is the response proportional to the scale of the problem?
- Would the response be the same if the numbers were 10x larger or smaller?
- Is an identifiable victim getting more attention than a larger anonymous group?
- Are resources being allocated based on emotional salience rather than magnitude?

Output JSON with: scope_insensitivity_present (bool), severity (none/mild/moderate/severe/extreme), problem_magnitude (actual scale of the problem), response_magnitude (scale of the response), proportionality_gap (how mismatched response is to problem scale), would_response_change_at_10x (bool — would doubling/10x the problem change the response?), identifiable_victim_effect (bool — is a named case getting disproportionate attention?), psychophysical_numbing (bool — has emotional response plateaued?), unit_bias (bool — is one unit being treated as the natural quantity?), what_proportional_response_looks_like (what a scope-sensitive response would be), resource_misallocation (how resources are being misdirected), emotional_vs_rational (how emotional response compares to rational assessment), comparison_anchor (what reference point would restore scope sensitivity), who_benefits_from_insensitivity (who gains from people not grasping the scale), communication_fix (how to present the problem to overcome scope neglect), recommendation (response_proportional/mild_neglect/significant_neglect/severe_neglect/complete_scope_failure)."""

SCOPE_PROMPT = """Detect scope insensitivity:

Problem: {problem}
Scale: {scale}
Current response: {response}
Comparison: {comparison}
Domain: {domain}
Context: {context}

Is scope insensitivity distorting the response? Return ONLY valid JSON."""


class ScopeInsensitivityService:
    """Detects scope insensitivity — failure to scale response to magnitude."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        problem: str,
        *,
        scale: str = "",
        response: str = "",
        comparison: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect scope insensitivity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SCOPE_PROMPT.format(
                problem=problem,
                scale=scale or "Not specified",
                response=response or "Not specified",
                comparison=comparison or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SCOPE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "problem": problem[:200],
            "scope_insensitivity_present": data.get("scope_insensitivity_present", False),
            "severity": data.get("severity", ""),
            "problem_magnitude": data.get("problem_magnitude", ""),
            "response_magnitude": data.get("response_magnitude", ""),
            "proportionality_gap": data.get("proportionality_gap", ""),
            "would_response_change_at_10x": data.get("would_response_change_at_10x", False),
            "identifiable_victim_effect": data.get("identifiable_victim_effect", False),
            "psychophysical_numbing": data.get("psychophysical_numbing", False),
            "unit_bias": data.get("unit_bias", False),
            "what_proportional_response_looks_like": data.get("what_proportional_response_looks_like", ""),
            "resource_misallocation": data.get("resource_misallocation", ""),
            "emotional_vs_rational": data.get("emotional_vs_rational", ""),
            "comparison_anchor": data.get("comparison_anchor", ""),
            "who_benefits_from_insensitivity": data.get("who_benefits_from_insensitivity", ""),
            "communication_fix": data.get("communication_fix", ""),
            "recommendation": data.get("recommendation", ""),
        }
