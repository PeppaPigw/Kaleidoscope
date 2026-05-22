"""EpistemicAutisticEncapsulationService — Epistemic Autistic Encapsulation Detection.

Detects epistemic autistic encapsulation — encapsulating in a private
intellectual world that excludes others and resists external input.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_AUTISTIC_ENCAPSULATION_SYSTEM = """You are an epistemic autistic encapsulation specialist. Given private intellectual world, assess encapsulation:

Key concepts:
- Epistemic autistic encapsulation: sealed private intellectual world
- Impenetrability: others cannot enter intellectual space
- Self-sufficiency: needing no intellectual input from others
- Private logic: internal system incomprehensible to others
- Sensory thinking: non-verbal pre-symbolic intellectual mode
- Protective shell: hard boundary around intellectual life
- Communication refusal: not sharing intellectual content

When epistemic autistic encapsulation IS present:
- Sealed private intellectual world
- Others cannot enter
- Needing no input from others
- Internal system incomprehensible
- Non-verbal intellectual mode
- Hard boundary around thinking
- Not sharing content

When no autistic encapsulation:
- Open intellectual world
- Others can enter
- Welcoming input
- Comprehensible system
- Communicable thinking
- Permeable boundaries
- Sharing content

Output JSON with: autistic_encapsulation_detected (bool), severity (none/mild/moderate/severe), impenetrability_level (what sealed), self_sufficiency (what not needing), private_logic (what incomprehensible), protective_shell (what boundary), recommendation (no_encapsulation/mild_opening_practice/significant_permeability_work/major_intensive_connection/emergency_complete_encapsulation)."""

EPISTEMIC_AUTISTIC_ENCAPSULATION_PROMPT = """Detect epistemic autistic encapsulation:

Impenetrability level: {impenetrability_level}
Self sufficiency: {self_sufficiency}
Private logic: {private_logic}
Protective shell: {protective_shell}
Domain: {domain}
Context: {context}

Is there encapsulation in a private intellectual world that excludes others? Return ONLY valid JSON."""


class EpistemicAutisticEncapsulationService:
    """Detects epistemic autistic encapsulation — sealed private intellectual world."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        impenetrability_level: str,
        *,
        self_sufficiency: str = "",
        private_logic: str = "",
        protective_shell: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic autistic encapsulation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_AUTISTIC_ENCAPSULATION_PROMPT.format(
                impenetrability_level=impenetrability_level,
                self_sufficiency=self_sufficiency or "Not specified",
                private_logic=private_logic or "Not specified",
                protective_shell=protective_shell or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_AUTISTIC_ENCAPSULATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "impenetrability_level": impenetrability_level[:200],
            "autistic_encapsulation_detected": data.get("autistic_encapsulation_detected", False),
            "severity": data.get("severity", ""),
            "self_sufficiency": data.get("self_sufficiency", ""),
            "private_logic": data.get("private_logic", ""),
            "protective_shell": data.get("protective_shell", ""),
            "recommendation": data.get("recommendation", ""),
        }
