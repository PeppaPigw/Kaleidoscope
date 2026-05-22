"""EpistemicNarcissisticInjuryService — Epistemic Narcissistic Injury Detection.

Detects epistemic narcissistic injury — rage or shame responses when
intellectual superiority is challenged or not recognized.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NARCISSISTIC_INJURY_SYSTEM = """You are an epistemic narcissistic injury specialist. Given rage/shame at intellectual challenge, assess narcissistic injury:

Key concepts:
- Epistemic narcissistic injury: wound to intellectual self-image
- Narcissistic rage: disproportionate anger at challenge
- Shame spiral: collapse into worthlessness when challenged
- Fragile grandiosity: superiority that shatters easily
- Perceived slight: seeing attack where none intended
- Retaliation: punishing the challenger
- Decompensation: falling apart when image threatened

When epistemic narcissistic injury IS present:
- Wound to intellectual self-image
- Disproportionate anger at challenge
- Collapse into worthlessness
- Superiority shattering easily
- Seeing attack where none intended
- Punishing challengers
- Falling apart when threatened

When no narcissistic injury:
- Resilient self-image
- Proportionate response to challenge
- Stable self-worth
- Flexible self-concept
- Accurate perception of intent
- Constructive engagement
- Maintaining composure

Output JSON with: narcissistic_injury_detected (bool), severity (none/mild/moderate/severe), rage_pattern (what anger), shame_response (what collapse), fragility_level (what shattering), retaliation_type (what punishing), recommendation (no_narcissistic_injury/mild_resilience_building/significant_injury_processing/major_intensive_restructuring/emergency_decompensation)."""

EPISTEMIC_NARCISSISTIC_INJURY_PROMPT = """Detect epistemic narcissistic injury:

Rage pattern: {rage_pattern}
Shame response: {shame_response}
Fragility level: {fragility_level}
Retaliation type: {retaliation_type}
Domain: {domain}
Context: {context}

Is there rage or shame when intellectual superiority is challenged? Return ONLY valid JSON."""


class EpistemicNarcissisticInjuryService:
    """Detects epistemic narcissistic injury — rage/shame at intellectual challenge."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        rage_pattern: str,
        *,
        shame_response: str = "",
        fragility_level: str = "",
        retaliation_type: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic narcissistic injury."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NARCISSISTIC_INJURY_PROMPT.format(
                rage_pattern=rage_pattern,
                shame_response=shame_response or "Not specified",
                fragility_level=fragility_level or "Not specified",
                retaliation_type=retaliation_type or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NARCISSISTIC_INJURY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "rage_pattern": rage_pattern[:200],
            "narcissistic_injury_detected": data.get("narcissistic_injury_detected", False),
            "severity": data.get("severity", ""),
            "shame_response": data.get("shame_response", ""),
            "fragility_level": data.get("fragility_level", ""),
            "retaliation_type": data.get("retaliation_type", ""),
            "recommendation": data.get("recommendation", ""),
        }
