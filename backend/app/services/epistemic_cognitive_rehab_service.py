"""EpistemicCognitiveRehabService — Epistemic Cognitive Rehab Detection.

Detects need for epistemic cognitive rehabilitation — rebuilding intellectual
processing capacity after damage to thinking systems.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COGNITIVE_REHAB_SYSTEM = """You are an epistemic cognitive rehabilitation specialist. Given intellectual processing damage, assess whether rebuilding is needed:

Key concepts:
- Epistemic cognitive rehab: rebuilding intellectual processing after damage
- Attention training: restoring focus capacity
- Memory strategies: compensating for retention loss
- Executive function: restoring planning and organization
- Processing speed: rebuilding rapid thinking
- Metacognition: awareness of own thinking limitations
- Compensatory strategies: workarounds for permanent deficits

When epistemic cognitive rehab IS needed:
- Damaged intellectual processing requiring rebuilding
- Impaired focus capacity needing training
- Retention loss needing compensatory strategies
- Impaired planning and organization
- Slowed rapid thinking
- Poor awareness of own limitations
- Need for workarounds for permanent deficits

When no rehab needed:
- Full intellectual processing capacity
- Normal focus and attention
- Normal retention
- Full executive function
- Normal processing speed
- Good metacognitive awareness
- No compensatory strategies needed

Output JSON with: cognitive_rehab_needed (bool), severity (none/mild/moderate/severe), attention_deficit (what focus impairment), memory_loss (what retention problem), executive_dysfunction (what planning failure), processing_speed (what slowdown), recommendation (no_rehab_needed/mild_rehab/significant_cognitive_rehabilitation/major_processing_rebuild/comprehensive_intellectual_cognitive_program)."""

EPISTEMIC_COGNITIVE_REHAB_PROMPT = """Detect epistemic cognitive rehab need:

Attention deficit: {attention_deficit}
Memory loss: {memory_loss}
Executive dysfunction: {executive_dysfunction}
Processing speed: {processing_speed}
Domain: {domain}
Context: {context}

Is rebuilding of intellectual processing capacity needed after damage? Return ONLY valid JSON."""


class EpistemicCognitiveRehabService:
    """Detects epistemic cognitive rehab need — intellectual processing rebuild."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        attention_deficit: str,
        *,
        memory_loss: str = "",
        executive_dysfunction: str = "",
        processing_speed: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic cognitive rehab need."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COGNITIVE_REHAB_PROMPT.format(
                attention_deficit=attention_deficit,
                memory_loss=memory_loss or "Not specified",
                executive_dysfunction=executive_dysfunction or "Not specified",
                processing_speed=processing_speed or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COGNITIVE_REHAB_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "attention_deficit": attention_deficit[:200],
            "cognitive_rehab_needed": data.get("cognitive_rehab_needed", False),
            "severity": data.get("severity", ""),
            "memory_loss": data.get("memory_loss", ""),
            "executive_dysfunction": data.get("executive_dysfunction", ""),
            "processing_speed": data.get("processing_speed", ""),
            "recommendation": data.get("recommendation", ""),
        }
