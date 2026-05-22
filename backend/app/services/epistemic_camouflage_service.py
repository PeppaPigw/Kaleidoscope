"""EpistemicCamouflageService — Epistemic Camouflage Detection.

Detects epistemic camouflage — ideas disguising themselves to blend
into intellectual environments where they don't naturally belong.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CAMOUFLAGE_SYSTEM = """You are an epistemic camouflage specialist. Given an idea presentation, assess whether ideas are disguising themselves to blend in:

Key concepts:
- Epistemic camouflage: ideas disguising themselves to blend in
- Mimicry: ideas imitating other ideas to avoid detection
- Crypsis: ideas hiding in plain sight through resemblance
- Warning coloration: ideas that should signal danger but don't
- Disruptive pattern: disguise that breaks up recognizable outline
- Background matching: ideas matching their intellectual environment
- Predator avoidance: ideas hiding from intellectual scrutiny

When epistemic camouflage IS present:
- Ideas disguising themselves to blend into environments
- Ideas imitating other ideas to avoid detection or scrutiny
- Ideas hiding in plain sight through surface resemblance
- Ideas that should signal danger appearing harmless
- Disguise breaking up the recognizable outline of an idea
- Ideas matching their intellectual environment deceptively
- Ideas hiding from intellectual scrutiny through disguise

When transparent ideas are present:
- Ideas presenting themselves honestly
- No imitation or disguise
- Ideas clearly visible for what they are
- Dangerous ideas clearly signaling their nature
- Ideas maintaining their recognizable form
- Ideas distinct from their environment
- Ideas open to intellectual scrutiny

Output JSON with: camouflage_present (bool), severity (none/mild/moderate/severe), idea (what idea is camouflaged), disguise (what disguise is used), environment (what environment it blends into), detection (what scrutiny it avoids), recommendation (transparent_ideas/mild_disguise/significant_camouflage/major_deception/expose_true_nature)."""

EPISTEMIC_CAMOUFLAGE_PROMPT = """Detect epistemic camouflage:

Idea: {idea}
Disguise: {disguise}
Environment: {environment}
Detection: {detection}
Domain: {domain}
Context: {context}

Are ideas disguising themselves to blend into intellectual environments where they don't belong? Return ONLY valid JSON."""


class EpistemicCamouflageService:
    """Detects epistemic camouflage — ideas disguising themselves to blend in."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        idea: str,
        *,
        disguise: str = "",
        environment: str = "",
        detection: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic camouflage."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CAMOUFLAGE_PROMPT.format(
                idea=idea,
                disguise=disguise or "Not specified",
                environment=environment or "Not specified",
                detection=detection or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CAMOUFLAGE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "idea": idea[:200],
            "camouflage_present": data.get("camouflage_present", False),
            "severity": data.get("severity", ""),
            "disguise": data.get("disguise", ""),
            "environment": data.get("environment", ""),
            "detection": data.get("detection", ""),
            "recommendation": data.get("recommendation", ""),
        }
