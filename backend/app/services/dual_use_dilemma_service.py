"""DualUseDilemmaService — Dual Use Dilemma Detection.

Detects dual use dilemma — technology or knowledge that can be used
for both beneficial and harmful purposes, where restricting harmful
use also restricts beneficial use. The same capability enables both
good and bad outcomes, making governance inherently difficult.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DUAL_USE_SYSTEM = """You are a dual use dilemma specialist. Given a technology or capability, assess whether it presents genuine dual-use tensions where beneficial and harmful uses are inseparable:

Key concepts:
- Dual use: same capability enables both benefit and harm
- Inseparability: can't restrict harmful use without restricting beneficial use
- Governance challenge: how to enable good while preventing bad
- Proliferation risk: once capability exists, controlling use is difficult
- Differential technology development: making defense easier than offense
- Access control vs. openness: restricting access limits both uses
- Responsible disclosure: balancing transparency with safety

When dual use dilemma IS present:
- The same technology enables both clearly beneficial and clearly harmful uses
- Restricting harmful use would significantly impair beneficial use
- The capability is difficult to control once developed
- No technical means exist to separate good from bad uses
- Governance must balance access against risk
- The beneficial use is important enough that restriction is costly
- The harmful use is serious enough that unrestricted access is dangerous

When dual use concern IS overstated:
- The harmful use requires additional capabilities beyond the technology itself
- Technical controls can separate beneficial from harmful applications
- The beneficial use has adequate alternatives
- The harmful use is already achievable through other means
- Access controls can be targeted without broad restriction
- The technology is already widely available
- The harm requires intent and additional steps beyond mere access

Output JSON with: dual_use_present (bool), severity (none/mild/moderate/severe), technology (what technology/capability), beneficial_use (what good it enables), harmful_use (what harm it enables), separability (can uses be separated), governance_options (what governance approaches exist), recommendation (concern_overstated/mild_dual_use/significant_dilemma/major_inseparable_dual_use/implement_differential_governance)."""

DUAL_USE_PROMPT = """Detect dual use dilemma:

Technology: {technology}
Beneficial use: {beneficial}
Harmful use: {harmful}
Separability: {separability}
Domain: {domain}
Context: {context}

Does this technology present a genuine dual-use dilemma where beneficial and harmful uses are inseparable? Return ONLY valid JSON."""


class DualUseDilemmaService:
    """Detects dual use dilemma — inseparable beneficial and harmful uses."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        technology: str,
        *,
        beneficial: str = "",
        harmful: str = "",
        separability: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect dual use dilemma."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DUAL_USE_PROMPT.format(
                technology=technology,
                beneficial=beneficial or "Not specified",
                harmful=harmful or "Not specified",
                separability=separability or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DUAL_USE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "technology": technology[:200],
            "dual_use_present": data.get("dual_use_present", False),
            "severity": data.get("severity", ""),
            "beneficial_use": data.get("beneficial_use", ""),
            "harmful_use": data.get("harmful_use", ""),
            "separability": data.get("separability", ""),
            "governance_options": data.get("governance_options", ""),
            "recommendation": data.get("recommendation", ""),
        }
