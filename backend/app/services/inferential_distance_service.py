"""InferentialDistanceService — Inferential Distance Detection.

Detects inferential distance problems — underestimating how many
steps of reasoning separate you from your audience, leading to
communication that assumes shared background knowledge that doesn't
exist. Yudkowsky (2007).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

INFERENTIAL_DISTANCE_SYSTEM = """You are an inferential distance specialist. Given a communication, assess whether it underestimates the reasoning gap between communicator and audience:

Key concepts (Yudkowsky, 2007):
- Inferential distance: number of reasoning steps between positions
- Shared background: knowledge both parties have
- Illusion of transparency: assuming your reasoning is obvious
- Curse of knowledge: can't imagine not knowing what you know
- Chunking: experts compress many steps into single concepts
- Prerequisite chain: each step requires understanding previous ones
- Double illusion: both sides think the gap is smaller than it is

When inferential distance IS underestimated:
- Communication assumes background knowledge the audience lacks
- Conclusions are stated without the reasoning chain
- Technical jargon is used without definition
- The communicator is frustrated that "obvious" points aren't understood
- Multiple prerequisite concepts are skipped
- The audience nods along without genuine understanding
- Disagreement is attributed to stupidity rather than different starting points

When communication IS calibrated:
- The communicator checks what the audience already knows
- Reasoning is built step by step from shared foundations
- Technical terms are defined or avoided
- The communicator verifies understanding at each step
- Prerequisites are identified and addressed
- The communication adapts to audience feedback
- Disagreement is explored for its source rather than dismissed

Output JSON with: inferential_distance_problem (bool), severity (none/mild/moderate/severe), communication (what is being communicated), assumed_knowledge (what knowledge is assumed), actual_knowledge (what audience likely knows), gap_size (how large is the inferential gap), missing_steps (what reasoning steps are skipped), recommendation (communication_calibrated/mild_gap/significant_inferential_distance/major_communication_failure/bridge_the_gap_step_by_step)."""

INFERENTIAL_DISTANCE_PROMPT = """Detect inferential distance problem:

Communication: {communication}
Audience: {audience}
Assumed knowledge: {assumed}
Feedback: {feedback}
Domain: {domain}
Context: {context}

Does this communication underestimate the reasoning gap with its audience? Return ONLY valid JSON."""


class InferentialDistanceService:
    """Detects inferential distance problems — underestimating reasoning gaps."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        communication: str,
        *,
        audience: str = "",
        assumed: str = "",
        feedback: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect inferential distance problem."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=INFERENTIAL_DISTANCE_PROMPT.format(
                communication=communication,
                audience=audience or "Not specified",
                assumed=assumed or "Not specified",
                feedback=feedback or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=INFERENTIAL_DISTANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "communication": communication[:200],
            "inferential_distance_problem": data.get("inferential_distance_problem", False),
            "severity": data.get("severity", ""),
            "assumed_knowledge": data.get("assumed_knowledge", ""),
            "gap_size": data.get("gap_size", ""),
            "missing_steps": data.get("missing_steps", ""),
            "recommendation": data.get("recommendation", ""),
        }
