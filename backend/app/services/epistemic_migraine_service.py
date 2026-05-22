"""EpistemicMigraineService — Epistemic Migraine Detection.

Detects epistemic migraine — severe episodic intellectual headache with
aura, photophobia, and debilitating intensity.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MIGRAINE_SYSTEM = """You are an epistemic migraine specialist. Given severe episodic intellectual headache, assess migraine:

Key concepts:
- Epistemic migraine: severe episodic intellectual headache
- Aura: warning signs before attack (visual, sensory disturbance)
- Photophobia: sensitivity to intellectual light/scrutiny during attack
- Prodrome: early warning phase hours before
- Trigger identification: what precipitates attacks
- Abortive therapy: stopping attack once started
- Prophylaxis: preventing attacks from occurring

When epistemic migraine IS present:
- Severe episodic intellectual headache
- Warning signs before attack
- Sensitivity to scrutiny during attack
- Early warning phase present
- Identifiable triggers
- Attacks need stopping once started
- Prevention strategy needed

When no migraine:
- No severe episodic headache
- No warning signs
- Normal scrutiny tolerance
- No prodrome phase
- No identifiable triggers
- No abortive therapy needed
- No prevention needed

Output JSON with: migraine_detected (bool), severity (none/mild/moderate/severe), aura_type (what warning signs), trigger_pattern (what precipitates), frequency (what episode rate), disability_level (what functional impact), recommendation (no_migraine/mild_abortive/significant_prophylaxis/major_combination/emergency_status_migrainosus)."""

EPISTEMIC_MIGRAINE_PROMPT = """Detect epistemic migraine:

Aura type: {aura_type}
Trigger pattern: {trigger_pattern}
Frequency: {frequency}
Disability level: {disability_level}
Domain: {domain}
Context: {context}

Is there severe episodic intellectual headache with aura and debilitating intensity? Return ONLY valid JSON."""


class EpistemicMigraineService:
    """Detects epistemic migraine — severe episodic intellectual headache."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        aura_type: str,
        *,
        trigger_pattern: str = "",
        frequency: str = "",
        disability_level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic migraine."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MIGRAINE_PROMPT.format(
                aura_type=aura_type,
                trigger_pattern=trigger_pattern or "Not specified",
                frequency=frequency or "Not specified",
                disability_level=disability_level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MIGRAINE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "aura_type": aura_type[:200],
            "migraine_detected": data.get("migraine_detected", False),
            "severity": data.get("severity", ""),
            "trigger_pattern": data.get("trigger_pattern", ""),
            "frequency": data.get("frequency", ""),
            "disability_level": data.get("disability_level", ""),
            "recommendation": data.get("recommendation", ""),
        }
