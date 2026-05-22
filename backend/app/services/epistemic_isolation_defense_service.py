"""EpistemicIsolationDefenseService — Epistemic Isolation Defense Detection.

Detects epistemic isolation defense — separating threatening intellectual
content from its emotional significance to render it harmless.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ISOLATION_DEFENSE_SYSTEM = """You are an epistemic isolation defense specialist. Given separation of content from emotion, assess isolation:

Key concepts:
- Epistemic isolation defense: separating content from emotional significance
- Affect stripping: removing feeling from threatening knowledge
- Factual shell: retaining information without its impact
- Emotional disconnection: knowing but not feeling implications
- Clinical detachment: treating own crisis as case study
- Meaning evacuation: emptying knowledge of significance
- Sterile knowing: understanding without being moved

When epistemic isolation defense IS present:
- Separating content from emotion
- Removing feeling from knowledge
- Retaining info without impact
- Knowing but not feeling
- Treating own crisis clinically
- Emptying significance
- Understanding without being moved

When no isolation defense:
- Content and emotion integrated
- Feeling present with knowledge
- Information has full impact
- Knowing and feeling together
- Personally engaged
- Full significance
- Moved by understanding

Output JSON with: isolation_defense_detected (bool), severity (none/mild/moderate/severe), affect_stripping (what removing feeling), factual_shell (what without impact), clinical_detachment (what treating clinically), meaning_evacuation (what emptying), recommendation (no_isolation_defense/mild_reconnection_practice/significant_affect_therapy/major_intensive_integration/emergency_complete_disconnection)."""

EPISTEMIC_ISOLATION_DEFENSE_PROMPT = """Detect epistemic isolation defense:

Affect stripping: {affect_stripping}
Factual shell: {factual_shell}
Clinical detachment: {clinical_detachment}
Meaning evacuation: {meaning_evacuation}
Domain: {domain}
Context: {context}

Is there separation of threatening intellectual content from its emotional significance? Return ONLY valid JSON."""


class EpistemicIsolationDefenseService:
    """Detects epistemic isolation defense — separating content from emotion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        affect_stripping: str,
        *,
        factual_shell: str = "",
        clinical_detachment: str = "",
        meaning_evacuation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic isolation defense."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ISOLATION_DEFENSE_PROMPT.format(
                affect_stripping=affect_stripping,
                factual_shell=factual_shell or "Not specified",
                clinical_detachment=clinical_detachment or "Not specified",
                meaning_evacuation=meaning_evacuation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ISOLATION_DEFENSE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "affect_stripping": affect_stripping[:200],
            "isolation_defense_detected": data.get("isolation_defense_detected", False),
            "severity": data.get("severity", ""),
            "factual_shell": data.get("factual_shell", ""),
            "clinical_detachment": data.get("clinical_detachment", ""),
            "meaning_evacuation": data.get("meaning_evacuation", ""),
            "recommendation": data.get("recommendation", ""),
        }
