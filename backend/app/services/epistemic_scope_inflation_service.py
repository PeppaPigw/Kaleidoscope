"""EpistemicScopeInflationService — Epistemic Scope Inflation Detection.

Detects epistemic scope inflation — inflating the scope of discussion
to dilute specific criticisms or avoid addressing pointed questions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SCOPE_INFLATION_SYSTEM = """You are an epistemic scope inflation specialist. Given scope inflation to dilute criticism, assess scope inflation:

Key concepts:
- Epistemic scope inflation: inflating scope to dilute specific criticisms
- Whataboutism: deflecting to broader issues to avoid specific point
- Dilution strategy: diluting criticism by expanding context
- Moving to meta: moving to meta-level to avoid object-level criticism
- Complexity shield: using complexity of broader picture as shield
- Proportionality distortion: making specific issue seem small in inflated scope
- Accountability diffusion: diffusing accountability across inflated scope

When epistemic scope inflation IS present:
- Scope inflated to dilute
- Whataboutism deployed
- Criticism diluted
- Meta-level escape
- Complexity used as shield
- Proportionality distorted
- Accountability diffused

When no scope inflation:
- Scope appropriate
- Specific points addressed
- Criticism engaged directly
- Level appropriate
- Complexity honest
- Proportionality accurate
- Accountability focused

Output JSON with: scope_inflation_detected (bool), severity (none/mild/moderate/severe), whataboutism (what deflected to), dilution_strategy (what diluted), complexity_shield (what complexity shields), accountability_diffusion (what accountability diffused), recommendation (no_scope_inflation/mild_focus_practice/significant_specificity_recovery/major_intensive_scope_correction/emergency_complete_scope_inflation)."""

EPISTEMIC_SCOPE_INFLATION_PROMPT = """Detect epistemic scope inflation:

Whataboutism: {whataboutism}
Dilution strategy: {dilution_strategy}
Complexity shield: {complexity_shield}
Accountability diffusion: {accountability_diffusion}
Domain: {domain}
Context: {context}

Is scope being inflated to dilute specific criticisms? Return ONLY valid JSON."""


class EpistemicScopeInflationService:
    """Detects epistemic scope inflation — diluting through expansion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        whataboutism: str,
        *,
        dilution_strategy: str = "",
        complexity_shield: str = "",
        accountability_diffusion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic scope inflation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SCOPE_INFLATION_PROMPT.format(
                whataboutism=whataboutism,
                dilution_strategy=dilution_strategy or "Not specified",
                complexity_shield=complexity_shield or "Not specified",
                accountability_diffusion=accountability_diffusion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SCOPE_INFLATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "whataboutism": whataboutism[:200],
            "scope_inflation_detected": data.get("scope_inflation_detected", False),
            "severity": data.get("severity", ""),
            "dilution_strategy": data.get("dilution_strategy", ""),
            "complexity_shield": data.get("complexity_shield", ""),
            "accountability_diffusion": data.get("accountability_diffusion", ""),
            "recommendation": data.get("recommendation", ""),
        }
