"""EpistemicLanguageEuphemismService — Epistemic Language Euphemism Detection.

Detects epistemic language euphemism — euphemisms hiding epistemic
reality and softening what should be confronted directly.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LANGUAGE_EUPHEMISM_SYSTEM = """You are an epistemic language euphemism specialist. Given euphemisms hiding epistemic reality, assess language euphemism:

Key concepts:
- Epistemic language euphemism: euphemisms hiding epistemic reality
- Reality softening: softening harsh realities with gentle language
- Truth packaging: packaging truth in acceptable wrapping
- Severity minimization: minimizing severity through word choice
- Consequence hiding: hiding consequences behind euphemisms
- Accountability diffusion: diffusing accountability through vague language
- Impact masking: masking impact with neutral terminology

When epistemic language euphemism IS present:
- Euphemisms hiding reality
- Reality softened
- Truth packaged
- Severity minimized
- Consequences hidden
- Accountability diffused
- Impact masked

When no language euphemism:
- Reality stated directly
- No softening needed
- Truth stated plainly
- Severity acknowledged
- Consequences named
- Accountability clear
- Impact stated

Output JSON with: language_euphemism_detected (bool), severity (none/mild/moderate/severe), reality_softening (what reality softened), severity_minimization (what severity minimized), consequence_hiding (what consequences hidden), accountability_diffusion (what accountability diffused), recommendation (no_language_euphemism/mild_directness_practice/significant_plain_speaking/major_intensive_truth_naming/emergency_complete_language_euphemism)."""

EPISTEMIC_LANGUAGE_EUPHEMISM_PROMPT = """Detect epistemic language euphemism:

Reality softening: {reality_softening}
Severity minimization: {severity_minimization}
Consequence hiding: {consequence_hiding}
Accountability diffusion: {accountability_diffusion}
Domain: {domain}
Context: {context}

Are euphemisms hiding epistemic reality? Return ONLY valid JSON."""


class EpistemicLanguageEuphemismService:
    """Detects epistemic language euphemism — euphemisms hiding reality."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reality_softening: str,
        *,
        severity_minimization: str = "",
        consequence_hiding: str = "",
        accountability_diffusion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic language euphemism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LANGUAGE_EUPHEMISM_PROMPT.format(
                reality_softening=reality_softening,
                severity_minimization=severity_minimization or "Not specified",
                consequence_hiding=consequence_hiding or "Not specified",
                accountability_diffusion=accountability_diffusion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LANGUAGE_EUPHEMISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "reality_softening": reality_softening[:200],
            "language_euphemism_detected": data.get("language_euphemism_detected", False),
            "severity": data.get("severity", ""),
            "severity_minimization": data.get("severity_minimization", ""),
            "consequence_hiding": data.get("consequence_hiding", ""),
            "accountability_diffusion": data.get("accountability_diffusion", ""),
            "recommendation": data.get("recommendation", ""),
        }
