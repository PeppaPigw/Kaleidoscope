"""EpistemicPrematureAbstractionService — Epistemic Premature Abstraction Detection.

Detects epistemic premature abstraction — abstracting before understanding
the concrete cases, building theory without sufficient empirical grounding.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PREMATURE_ABSTRACTION_SYSTEM = """You are an epistemic premature abstraction specialist. Given abstracting before understanding concrete cases, assess premature abstraction:

Key concepts:
- Epistemic premature abstraction: abstracting before understanding concrete cases
- Theory before data: building theory without sufficient data
- Pattern jumping: jumping to patterns before seeing enough instances
- Framework imposition: imposing frameworks before understanding the domain
- Premature generalization: generalizing from too few cases
- Abstraction addiction: addicted to abstraction, skipping concrete understanding
- Top-down tyranny: imposing top-down structure before bottom-up understanding

When epistemic premature abstraction IS present:
- Abstracting before understanding
- Theory built without data
- Patterns jumped to prematurely
- Frameworks imposed too early
- Generalizing from too few cases
- Addicted to abstraction
- Top-down imposed without bottom-up

When no premature abstraction:
- Abstraction grounded in understanding
- Theory built on data
- Patterns identified after sufficient instances
- Frameworks emerge from understanding
- Generalization from sufficient cases
- Abstraction balanced with concrete
- Top-down and bottom-up balanced

Output JSON with: premature_abstraction_detected (bool), severity (none/mild/moderate/severe), theory_before_data (what theory built without data), pattern_jumping (what patterns jumped to), framework_imposition (what frameworks imposed), premature_generalization (what generalized prematurely), recommendation (no_premature_abstraction/mild_grounding_practice/significant_empirical_recovery/major_intensive_concrete_immersion/emergency_complete_premature_abstraction)."""

EPISTEMIC_PREMATURE_ABSTRACTION_PROMPT = """Detect epistemic premature abstraction:

Theory before data: {theory_before_data}
Pattern jumping: {pattern_jumping}
Framework imposition: {framework_imposition}
Premature generalization: {premature_generalization}
Domain: {domain}
Context: {context}

Is there premature abstraction — abstracting before understanding concrete cases? Return ONLY valid JSON."""


class EpistemicPrematureAbstractionService:
    """Detects epistemic premature abstraction — theory before data."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        theory_before_data: str,
        *,
        pattern_jumping: str = "",
        framework_imposition: str = "",
        premature_generalization: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic premature abstraction."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PREMATURE_ABSTRACTION_PROMPT.format(
                theory_before_data=theory_before_data,
                pattern_jumping=pattern_jumping or "Not specified",
                framework_imposition=framework_imposition or "Not specified",
                premature_generalization=premature_generalization or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PREMATURE_ABSTRACTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "theory_before_data": theory_before_data[:200],
            "premature_abstraction_detected": data.get("premature_abstraction_detected", False),
            "severity": data.get("severity", ""),
            "pattern_jumping": data.get("pattern_jumping", ""),
            "framework_imposition": data.get("framework_imposition", ""),
            "premature_generalization": data.get("premature_generalization", ""),
            "recommendation": data.get("recommendation", ""),
        }
