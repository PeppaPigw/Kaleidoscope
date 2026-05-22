"""EpistemicFrameLockService — Epistemic Frame Lock Detection.

Detects epistemic frame lock — being locked into a frame that determines
what counts as relevant, preventing seeing outside the frame.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FRAME_LOCK_SYSTEM = """You are an epistemic frame lock specialist. Given locked frames determining relevance, assess frame lock:

Key concepts:
- Epistemic frame lock: locked into a frame determining what counts as relevant
- Invisible frame: frame so naturalized it's invisible
- Relevance filter: frame filtering what's considered relevant
- Question constraint: frame constraining what questions can be asked
- Solution space limitation: frame limiting possible solutions
- Evidence filter: frame filtering what counts as evidence
- Perspective monopoly: frame monopolizing perspective

When epistemic frame lock IS present:
- Locked into frame
- Frame invisible
- Relevance filtered by frame
- Questions constrained
- Solutions limited
- Evidence filtered
- Perspective monopolized

When no frame lock:
- Multiple frames available
- Frame visible and chosen
- Relevance broadly assessed
- Questions unconstrained
- Solutions open
- Evidence broadly considered
- Multiple perspectives

Output JSON with: frame_lock_detected (bool), severity (none/mild/moderate/severe), invisible_frame (what frame invisible), relevance_filter (what filtered), question_constraint (what questions constrained), solution_limitation (what solutions limited), recommendation (no_frame_lock/mild_frame_awareness/significant_frame_shifting/major_intensive_frame_liberation/emergency_complete_frame_lock)."""

EPISTEMIC_FRAME_LOCK_PROMPT = """Detect epistemic frame lock:

Invisible frame: {invisible_frame}
Relevance filter: {relevance_filter}
Question constraint: {question_constraint}
Solution limitation: {solution_limitation}
Domain: {domain}
Context: {context}

Is thinking locked into a frame that determines what counts as relevant? Return ONLY valid JSON."""


class EpistemicFrameLockService:
    """Detects epistemic frame lock — invisible frame constraining thought."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        invisible_frame: str,
        *,
        relevance_filter: str = "",
        question_constraint: str = "",
        solution_limitation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic frame lock."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FRAME_LOCK_PROMPT.format(
                invisible_frame=invisible_frame,
                relevance_filter=relevance_filter or "Not specified",
                question_constraint=question_constraint or "Not specified",
                solution_limitation=solution_limitation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FRAME_LOCK_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "invisible_frame": invisible_frame[:200],
            "frame_lock_detected": data.get("frame_lock_detected", False),
            "severity": data.get("severity", ""),
            "relevance_filter": data.get("relevance_filter", ""),
            "question_constraint": data.get("question_constraint", ""),
            "solution_limitation": data.get("solution_limitation", ""),
            "recommendation": data.get("recommendation", ""),
        }
