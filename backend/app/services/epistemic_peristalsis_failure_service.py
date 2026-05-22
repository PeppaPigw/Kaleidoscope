"""EpistemicPeristalsisFailureService — Epistemic Peristalsis Failure Detection.

Detects epistemic peristalsis failure — loss of rhythmic movement that
pushes ideas through the intellectual processing pipeline.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PERISTALSIS_FAILURE_SYSTEM = """You are an epistemic peristalsis failure specialist. Given intellectual transit, assess whether rhythmic movement has failed:

Key concepts:
- Epistemic peristalsis failure: loss of rhythmic movement pushing ideas
- Ileus: complete cessation of intellectual movement
- Dysmotility: disordered movement patterns
- Retrograde peristalsis: ideas moving backward
- Transit time: how long ideas take to process
- Prokinetic: agent that stimulates movement
- Gastroparesis: delayed emptying of intellectual stomach

When epistemic peristalsis failure IS present:
- Loss of rhythmic movement pushing ideas through
- Complete cessation of intellectual transit
- Disordered movement patterns
- Ideas moving backward through the pipeline
- Abnormally long processing transit times
- Need for agents to stimulate movement
- Delayed emptying of intellectual processing stages

When healthy peristalsis is present:
- Regular rhythmic movement
- Continuous intellectual transit
- Ordered movement patterns
- Forward-only idea flow
- Normal transit times
- No prokinetics needed
- Timely stage emptying

Output JSON with: peristalsis_failure_present (bool), severity (none/mild/moderate/severe), ileus (what cessation), dysmotility (what disordered movement), retrograde (what backward flow), transit_time (what delay), recommendation (healthy_peristalsis/mild_failure/significant_peristalsis_failure/major_transit_arrest/restore_intellectual_motility)."""

EPISTEMIC_PERISTALSIS_FAILURE_PROMPT = """Detect epistemic peristalsis failure:

Ileus: {ileus}
Dysmotility: {dysmotility}
Retrograde: {retrograde}
Transit time: {transit_time}
Domain: {domain}
Context: {context}

Has rhythmic movement pushing ideas through the processing pipeline failed? Return ONLY valid JSON."""


class EpistemicPeristalsisFailureService:
    """Detects epistemic peristalsis failure — loss of rhythmic idea movement."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        ileus: str,
        *,
        dysmotility: str = "",
        retrograde: str = "",
        transit_time: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic peristalsis failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PERISTALSIS_FAILURE_PROMPT.format(
                ileus=ileus,
                dysmotility=dysmotility or "Not specified",
                retrograde=retrograde or "Not specified",
                transit_time=transit_time or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PERISTALSIS_FAILURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "ileus": ileus[:200],
            "peristalsis_failure_present": data.get("peristalsis_failure_present", False),
            "severity": data.get("severity", ""),
            "dysmotility": data.get("dysmotility", ""),
            "retrograde": data.get("retrograde", ""),
            "transit_time": data.get("transit_time", ""),
            "recommendation": data.get("recommendation", ""),
        }
