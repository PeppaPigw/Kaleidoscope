"""EpistemicCognitiveOffloadingService — Epistemic Cognitive Offloading Detection.

Detects epistemic cognitive offloading — offloading thinking to external
systems without verification, creating false confidence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COGNITIVE_OFFLOADING_SYSTEM = """You are an epistemic cognitive offloading specialist. Given offloading thinking without verification, assess cognitive offloading:

Key concepts:
- Epistemic cognitive offloading: offloading thinking to external systems without verification
- Tool dependency: depending on tools without understanding
- Algorithm trust: trusting algorithms without checking
- Memory outsourcing: outsourcing memory without backup understanding
- Calculation delegation: delegating calculation without sanity checks
- Judgment automation: automating judgment without oversight
- Understanding bypass: bypassing understanding via external tools

When epistemic cognitive offloading IS present:
- Offloading without verification
- Depending on tools blindly
- Trusting algorithms unchecked
- Outsourcing memory completely
- Delegating without sanity checks
- Automating judgment unsupervised
- Bypassing understanding

When no cognitive offloading:
- Offloading with verification
- Using tools with understanding
- Checking algorithm outputs
- Memory backed by understanding
- Calculations sanity-checked
- Judgment maintained with oversight
- Understanding preserved

Output JSON with: cognitive_offloading_detected (bool), severity (none/mild/moderate/severe), tool_dependency (what tools depended on blindly), algorithm_trust (what algorithms trusted unchecked), memory_outsourcing (what memory outsourced without backup), judgment_automation (what judgment automated without oversight), recommendation (no_cognitive_offloading/mild_verification_practice/significant_understanding_recovery/major_intensive_independence_building/emergency_complete_cognitive_offloading)."""

EPISTEMIC_COGNITIVE_OFFLOADING_PROMPT = """Detect epistemic cognitive offloading:

Tool dependency: {tool_dependency}
Algorithm trust: {algorithm_trust}
Memory outsourcing: {memory_outsourcing}
Judgment automation: {judgment_automation}
Domain: {domain}
Context: {context}

Is thinking being offloaded to external systems without verification? Return ONLY valid JSON."""


class EpistemicCognitiveOffloadingService:
    """Detects epistemic cognitive offloading — offloading thinking without verification."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        tool_dependency: str,
        *,
        algorithm_trust: str = "",
        memory_outsourcing: str = "",
        judgment_automation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic cognitive offloading."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COGNITIVE_OFFLOADING_PROMPT.format(
                tool_dependency=tool_dependency,
                algorithm_trust=algorithm_trust or "Not specified",
                memory_outsourcing=memory_outsourcing or "Not specified",
                judgment_automation=judgment_automation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COGNITIVE_OFFLOADING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "tool_dependency": tool_dependency[:200],
            "cognitive_offloading_detected": data.get("cognitive_offloading_detected", False),
            "severity": data.get("severity", ""),
            "algorithm_trust": data.get("algorithm_trust", ""),
            "memory_outsourcing": data.get("memory_outsourcing", ""),
            "judgment_automation": data.get("judgment_automation", ""),
            "recommendation": data.get("recommendation", ""),
        }
