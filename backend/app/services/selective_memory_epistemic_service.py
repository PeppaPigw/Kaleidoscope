"""SelectiveMemoryEpistemicService — Epistemic Selective Memory Detection.

Detects epistemic selective memory — remembering evidence that confirms
beliefs while forgetting disconfirming evidence, where memory itself
becomes a tool of confirmation bias.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SELECTIVE_MEMORY_EPISTEMIC_SYSTEM = """You are an epistemic selective memory specialist. Given a belief and its evidential history, assess whether memory is selectively retaining confirming evidence:

Key concepts:
- Selective memory: remembering confirming, forgetting disconfirming
- Memory-confirmation loop: memory reinforcing existing beliefs
- Evidence amnesia: forgetting evidence that challenged beliefs
- Recall asymmetry: easier recall of supporting evidence
- Memory editing: unconsciously editing memories to fit beliefs
- Confirmation through forgetting: beliefs strengthened by forgetting challenges
- Retrospective evidence selection: past evidence remembered selectively

When selective memory IS present:
- Confirming evidence readily recalled
- Disconfirming evidence forgotten or minimized
- Memory serving belief maintenance
- Past challenges to belief not remembered
- Evidence history reconstructed to support current belief
- Recall asymmetry between supporting and challenging
- Memory functioning as confirmation mechanism

When differential recall is appropriate:
- More important evidence better remembered
- Higher quality evidence retained preferentially
- Recall proportionate to evidence strength
- Both confirming and disconfirming remembered
- Memory reflects evidence quality not direction
- Forgetting random not systematic
- Recall based on relevance not confirmation

Output JSON with: selective_memory_present (bool), severity (none/mild/moderate/severe), belief (what belief is maintained), remembered (what evidence is remembered), forgotten (what evidence is forgotten), asymmetry (how memory is asymmetric), recommendation (balanced_recall/mild_memory_preference/significant_selective_memory/major_evidence_amnesia/audit_evidence_history_systematically)."""

SELECTIVE_MEMORY_EPISTEMIC_PROMPT = """Detect epistemic selective memory:

Belief: {belief}
Evidence remembered: {remembered}
Evidence forgotten: {forgotten}
Recall pattern: {pattern}
Domain: {domain}
Context: {context}

Is memory selectively retaining confirming evidence while forgetting disconfirming? Return ONLY valid JSON."""


class SelectiveMemoryEpistemicService:
    """Detects epistemic selective memory — confirming evidence remembered, disconfirming forgotten."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        belief: str,
        *,
        remembered: str = "",
        forgotten: str = "",
        pattern: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic selective memory."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SELECTIVE_MEMORY_EPISTEMIC_PROMPT.format(
                belief=belief,
                remembered=remembered or "Not specified",
                forgotten=forgotten or "Not specified",
                pattern=pattern or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SELECTIVE_MEMORY_EPISTEMIC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "belief": belief[:200],
            "selective_memory_present": data.get("selective_memory_present", False),
            "severity": data.get("severity", ""),
            "remembered": data.get("remembered", ""),
            "forgotten": data.get("forgotten", ""),
            "asymmetry": data.get("asymmetry", ""),
            "recommendation": data.get("recommendation", ""),
        }
