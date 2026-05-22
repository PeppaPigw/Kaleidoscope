"""EpistemicFogService — Epistemic Fog Detection.

Detects epistemic fog — confusion and lack of clarity obscuring
reasoning and preventing clear thought.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FOG_SYSTEM = """You are an epistemic fog specialist. Given a reasoning situation, assess whether confusion and lack of clarity are obscuring thought:

Key concepts:
- Epistemic fog: confusion obscuring reasoning
- Clarity failure: inability to see clearly
- Conceptual murkiness: concepts unclear and blurred
- Reasoning obscured: reasoning hidden behind confusion
- Visibility loss: loss of intellectual visibility
- Disorientation: intellectual disorientation
- Navigation failure: inability to navigate through ideas

When epistemic fog IS present:
- Confusion obscuring reasoning
- Inability to see clearly through ideas
- Concepts unclear and blurred together
- Reasoning hidden behind confusion
- Loss of intellectual visibility
- Intellectual disorientation present
- Unable to navigate through ideas clearly

When productive complexity is present:
- Complexity present but navigable
- Ideas clear even if numerous
- Concepts distinct even if related
- Reasoning visible even if complex
- Intellectual visibility maintained
- Orientation maintained despite complexity
- Navigation possible through clear structure

Output JSON with: fog_present (bool), severity (none/mild/moderate/severe), situation (what situation exists), obscured (what is obscured), source (what generates the fog), navigation (how navigation is affected), recommendation (productive_complexity/mild_confusion/significant_fog/major_visibility_loss/clarify_and_structure)."""

EPISTEMIC_FOG_PROMPT = """Detect epistemic fog:

Situation: {situation}
Obscured: {obscured}
Source: {source}
Navigation: {navigation}
Domain: {domain}
Context: {context}

Is confusion and lack of clarity obscuring reasoning? Return ONLY valid JSON."""


class EpistemicFogService:
    """Detects epistemic fog — confusion obscuring reasoning."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        obscured: str = "",
        source: str = "",
        navigation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic fog."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FOG_PROMPT.format(
                situation=situation,
                obscured=obscured or "Not specified",
                source=source or "Not specified",
                navigation=navigation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FOG_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "fog_present": data.get("fog_present", False),
            "severity": data.get("severity", ""),
            "obscured": data.get("obscured", ""),
            "source": data.get("source", ""),
            "navigation": data.get("navigation", ""),
            "recommendation": data.get("recommendation", ""),
        }
