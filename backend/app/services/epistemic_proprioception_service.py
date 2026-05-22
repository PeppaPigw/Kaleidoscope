"""EpistemicProprioceptionService — Epistemic Proprioception Detection.

Detects epistemic proprioception — the sense of where one's own
knowledge is positioned without needing to look at it directly.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PROPRIOCEPTION_SYSTEM = """You are an epistemic proprioception specialist. Given a knowledge awareness pattern, assess whether there is a sense of knowledge position without direct observation:

Key concepts:
- Epistemic proprioception: sensing knowledge position without looking
- Body schema: internal map of one's own knowledge
- Position sense: knowing where knowledge is without checking
- Kinesthesia: sensing knowledge movement without watching
- Phantom knowledge: sensing knowledge that is no longer there
- Ataxia: loss of coordination from proprioception failure
- Calibration: accuracy of the internal position sense

When epistemic proprioception IS present:
- Sensing where knowledge is without directly examining it
- Internal map of one's own knowledge landscape
- Knowing knowledge position without checking
- Sensing knowledge movement without watching it
- Feeling knowledge that is no longer there
- Loss of coordination when proprioception fails
- Accuracy or inaccuracy of internal knowledge sense

When direct observation is present:
- Only knowing knowledge position by examining it directly
- No internal map of knowledge landscape
- Must check to know knowledge position
- Must watch knowledge to sense its movement
- No phantom sensations of absent knowledge
- Coordination maintained through direct observation
- No internal sense to be accurate or inaccurate

Output JSON with: proprioception_present (bool), severity (none/mild/moderate/severe), body_schema (what internal map exists), position_sense (what is sensed without looking), phantom (what absent knowledge is still felt), ataxia (what coordination is lost), recommendation (direct_observation/mild_internal_sense/significant_proprioception/major_internal_mapping/calibrate_knowledge_sense)."""

EPISTEMIC_PROPRIOCEPTION_PROMPT = """Detect epistemic proprioception:

Body schema: {body_schema}
Position sense: {position_sense}
Phantom: {phantom}
Ataxia: {ataxia}
Domain: {domain}
Context: {context}

Is there a sense of where knowledge is positioned without needing to look at it directly? Return ONLY valid JSON."""


class EpistemicProprioceptionService:
    """Detects epistemic proprioception — sensing knowledge position without looking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        body_schema: str,
        *,
        position_sense: str = "",
        phantom: str = "",
        ataxia: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic proprioception."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PROPRIOCEPTION_PROMPT.format(
                body_schema=body_schema,
                position_sense=position_sense or "Not specified",
                phantom=phantom or "Not specified",
                ataxia=ataxia or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PROPRIOCEPTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "body_schema": body_schema[:200],
            "proprioception_present": data.get("proprioception_present", False),
            "severity": data.get("severity", ""),
            "position_sense": data.get("position_sense", ""),
            "phantom": data.get("phantom", ""),
            "ataxia": data.get("ataxia", ""),
            "recommendation": data.get("recommendation", ""),
        }
