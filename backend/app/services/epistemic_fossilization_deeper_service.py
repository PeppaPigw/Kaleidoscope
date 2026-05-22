"""EpistemicFossilizationDeeperService — Epistemic Fossilization (Deeper) Detection.

Detects epistemic fossilization — ideas preserved in rigid form
long past their useful life, blocking evolution.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FOSSILIZATION_DEEPER_SYSTEM = """You are an epistemic fossilization specialist. Given a knowledge domain, assess whether ideas are preserved in rigid form past their useful life:

Key concepts:
- Epistemic fossilization: ideas preserved rigidly past usefulness
- Intellectual petrification: ideas turned to stone, unable to evolve
- Outdated preservation: preserving what should have evolved
- Rigidity trap: trapped in rigid form unable to adapt
- Living fossil ideas: ideas surviving unchanged despite changed context
- Evolution resistance: resistance to necessary evolution
- Museum thinking: treating living knowledge as museum pieces

When epistemic fossilization IS present:
- Ideas preserved in rigid form past their useful life
- Ideas turned to stone, unable to evolve with context
- Preserving what should have evolved long ago
- Trapped in rigid form unable to adapt to new evidence
- Ideas surviving unchanged despite radically changed context
- Resistance to necessary evolution of understanding
- Living knowledge treated as museum pieces

When healthy preservation is present:
- Important ideas maintained while allowing evolution
- Core insights preserved while form adapts
- Preservation serving ongoing utility
- Ideas maintained in living, adaptable form
- Context changes reflected in updated understanding
- Evolution welcomed while preserving core value
- Knowledge alive and responsive to new evidence

Output JSON with: fossilization_present (bool), severity (none/mild/moderate/severe), domain (what domain is affected), fossil (what idea is fossilized), rigidity (how rigidity manifests), obsolescence (what has become obsolete), recommendation (healthy_preservation/mild_rigidity/significant_fossilization/major_intellectual_petrification/allow_ideas_to_evolve)."""

EPISTEMIC_FOSSILIZATION_DEEPER_PROMPT = """Detect epistemic fossilization:

Domain: {target_domain}
Fossil: {fossil}
Rigidity: {rigidity}
Obsolescence: {obsolescence}
Field: {field}
Context: {context}

Are ideas preserved in rigid form long past their useful life? Return ONLY valid JSON."""


class EpistemicFossilizationDeeperService:
    """Detects epistemic fossilization — ideas preserved rigidly past usefulness."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        target_domain: str,
        *,
        fossil: str = "",
        rigidity: str = "",
        obsolescence: str = "",
        field: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic fossilization."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FOSSILIZATION_DEEPER_PROMPT.format(
                target_domain=target_domain,
                fossil=fossil or "Not specified",
                rigidity=rigidity or "Not specified",
                obsolescence=obsolescence or "Not specified",
                field=field or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FOSSILIZATION_DEEPER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "target_domain": target_domain[:200],
            "fossilization_present": data.get("fossilization_present", False),
            "severity": data.get("severity", ""),
            "fossil": data.get("fossil", ""),
            "rigidity": data.get("rigidity", ""),
            "obsolescence": data.get("obsolescence", ""),
            "recommendation": data.get("recommendation", ""),
        }
