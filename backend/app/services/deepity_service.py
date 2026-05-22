"""DeepityService — Deepity Detection.

Detects deepities — statements that seem profound but operate on
two levels: one reading is trivially true but uninteresting, and
the other reading is interesting but false. Daniel Dennett (2009).
The profundity comes from conflating the two readings.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DEEPITY_SYSTEM = """You are a deepity specialist. Given a statement presented as profound, assess whether it operates on two levels — one trivially true and one meaningfully false:

Key concepts (Dennett, 2009):
- Deepity: statement with trivial true reading and false profound reading
- Pseudo-profundity: appearance of depth without substance
- Equivocation: switching between meanings to create false depth
- Trivial truth: one reading is obviously true but uninteresting
- False profundity: the interesting reading is actually false
- Ambiguity exploitation: profundity comes from vagueness
- Unfalsifiable depth: too vague to be wrong, too vague to be useful

When deepity IS present:
- "Love is just a word" (trivially: yes, it's a word; profoundly: no, it's an experience)
- "Everything happens for a reason" (trivially: causation exists; profoundly: teleology is unproven)
- Statements that sound deep but dissolve under analysis
- Profundity that depends on ambiguity between readings
- Claims that are either trivially true or meaningfully false
- Wisdom that provides no actionable information
- Statements that resist disagreement through vagueness

When apparent simplicity IS genuinely profound:
- The statement captures a genuine insight concisely
- Both readings are true and the connection is illuminating
- The statement generates useful predictions or actions
- Unpacking the statement reveals genuine depth
- The profundity survives precise reformulation
- Domain experts find it genuinely insightful
- The statement can be tested or applied

Output JSON with: deepity_present (bool), severity (none/mild/moderate/severe), statement (the statement analyzed), trivial_reading (the trivially true interpretation), profound_reading (the seemingly profound interpretation), trivial_truth (is the trivial reading true), profound_truth (is the profound reading true), recommendation (genuinely_profound/mild_vagueness/significant_deepity/major_pseudo_profundity/reformulate_precisely)."""

DEEPITY_PROMPT = """Detect deepity:

Statement: {statement}
Claimed insight: {insight}
Trivial reading: {trivial}
Profound reading: {profound}
Domain: {domain}
Context: {context}

Does this statement seem profound by conflating a trivially true reading with a meaningfully false one? Return ONLY valid JSON."""


class DeepityService:
    """Detects deepities — pseudo-profound statements."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        statement: str,
        *,
        insight: str = "",
        trivial: str = "",
        profound: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect deepity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DEEPITY_PROMPT.format(
                statement=statement,
                insight=insight or "Not specified",
                trivial=trivial or "Not specified",
                profound=profound or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DEEPITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "statement": statement[:200],
            "deepity_present": data.get("deepity_present", False),
            "severity": data.get("severity", ""),
            "trivial_reading": data.get("trivial_reading", ""),
            "profound_reading": data.get("profound_reading", ""),
            "trivial_truth": data.get("trivial_truth", ""),
            "profound_truth": data.get("profound_truth", ""),
            "recommendation": data.get("recommendation", ""),
        }
