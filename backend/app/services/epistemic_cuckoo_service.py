"""EpistemicCuckooService — Epistemic Cuckoo Detection.

Detects epistemic cuckoo behavior — inserting one's ideas into
others' epistemic frameworks deceptively, like a cuckoo bird
placing eggs in another's nest.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CUCKOO_SYSTEM = """You are an epistemic cuckoo specialist. Given a knowledge-sharing context, assess whether ideas are being deceptively inserted into others' frameworks:

Key concepts:
- Epistemic cuckoo: inserting ideas deceptively into others' frameworks
- Idea implantation: planting ideas as if they were the host's own
- Framework infiltration: infiltrating others' belief systems
- Attribution manipulation: manipulating who gets credit for ideas
- Inception-style planting: making others think ideas are their own
- Intellectual parasitism: parasitizing others' intellectual frameworks
- Stealth influence: influencing without acknowledgment

When epistemic cuckoo IS present:
- Ideas inserted deceptively into others' frameworks
- Others made to think ideas are their own
- Framework infiltrated without acknowledgment
- Attribution manipulated to hide source
- Ideas planted through stealth influence
- Intellectual frameworks parasitized
- Influence hidden from the influenced

When legitimate influence is present:
- Ideas shared openly and attributed
- Influence acknowledged and transparent
- Frameworks engaged with honestly
- Attribution clear and fair
- Ideas offered for consideration
- Intellectual exchange reciprocal
- Influence visible and consensual

Output JSON with: cuckoo_present (bool), severity (none/mild/moderate/severe), situation (what situation exists), inserted_idea (what idea is inserted), host_framework (whose framework is targeted), deception_method (how insertion is hidden), recommendation (legitimate_influence/mild_suggestion/significant_epistemic_cuckoo/major_idea_implantation/influence_transparently)."""

EPISTEMIC_CUCKOO_PROMPT = """Detect epistemic cuckoo behavior:

Situation: {situation}
Inserted idea: {idea}
Host framework: {framework}
Deception method: {deception}
Domain: {domain}
Context: {context}

Are ideas being deceptively inserted into others' epistemic frameworks? Return ONLY valid JSON."""


class EpistemicCuckooService:
    """Detects epistemic cuckoo — inserting ideas deceptively into others' frameworks."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        idea: str = "",
        framework: str = "",
        deception: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic cuckoo behavior."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CUCKOO_PROMPT.format(
                situation=situation,
                idea=idea or "Not specified",
                framework=framework or "Not specified",
                deception=deception or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CUCKOO_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "cuckoo_present": data.get("cuckoo_present", False),
            "severity": data.get("severity", ""),
            "inserted_idea": data.get("inserted_idea", ""),
            "host_framework": data.get("host_framework", ""),
            "deception_method": data.get("deception_method", ""),
            "recommendation": data.get("recommendation", ""),
        }
