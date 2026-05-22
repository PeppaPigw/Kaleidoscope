"""EpistemicLearnedHelplessnessService — Epistemic Learned Helplessness Detection.

Detects epistemic learned helplessness — giving up on evaluating
arguments because past attempts at evaluation have failed or been
manipulated. "I can't tell what's true anymore, so I'll just
believe whatever feels right / whatever authority says." A
rational response to being repeatedly deceived, but one that
leaves you vulnerable to whoever fills the vacuum.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LEARNED_HELPLESSNESS_SYSTEM = """You are an epistemic learned helplessness specialist. Given a reasoning pattern, assess whether someone has given up on evaluating arguments due to past failures:

Key concepts:
- Epistemic learned helplessness: giving up on evaluation
- Rational response to manipulation: past deception → distrust of own judgment
- Authority default: deferring to authority because own evaluation seems hopeless
- Gut feeling default: trusting intuition because analysis seems futile
- Epistemic fatigue: exhaustion from trying to evaluate competing claims
- Information overwhelm: too many claims to evaluate → evaluate none
- Cynical epistemology: "you can't trust anything" as endpoint

When epistemic learned helplessness IS present:
- "I can't tell what's true anymore" (giving up on evaluation)
- Defaulting to authority without any personal evaluation
- "All sources are biased, so why bother checking"
- Refusing to engage with arguments because "you can prove anything"
- "I'll just go with my gut" on questions that require analysis
- Treating all claims as equally (un)trustworthy
- "Who knows what's really true" as conversation-ender

When epistemic caution IS appropriate:
- Genuine uncertainty about one's ability to evaluate specific domains
- Appropriate deference to expertise in unfamiliar areas
- Acknowledging limits of one's knowledge
- Healthy skepticism that motivates further investigation
- Recognizing when one lacks the background to evaluate

Output JSON with: epistemic_helplessness_present (bool), severity (none/mild/moderate/severe), pattern (what reasoning pattern is observed), trigger (what caused the helplessness), default_strategy (what replaces evaluation), evaluation_capacity (is evaluation actually impossible), recovery_path (how could evaluation capacity be rebuilt), vulnerability (what manipulation does this enable), recommendation (caution_appropriate/mild_epistemic_fatigue/significant_learned_helplessness/major_evaluation_abandonment/rebuild_evaluation_capacity)."""

EPISTEMIC_LEARNED_HELPLESSNESS_PROMPT = """Detect epistemic learned helplessness:

Pattern: {pattern}
History: {history}
Current strategy: {strategy}
Domain: {domain_input}
Domain category: {domain}
Context: {context}

Has someone given up on evaluating arguments due to past failures or manipulation? Return ONLY valid JSON."""


class EpistemicLearnedHelplessnessService:
    """Detects epistemic learned helplessness — giving up on evaluation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        pattern: str,
        *,
        history: str = "",
        strategy: str = "",
        domain_input: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic learned helplessness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LEARNED_HELPLESSNESS_PROMPT.format(
                pattern=pattern,
                history=history or "Not specified",
                strategy=strategy or "Not specified",
                domain_input=domain_input or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LEARNED_HELPLESSNESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "pattern": pattern[:200],
            "epistemic_helplessness_present": data.get("epistemic_helplessness_present", False),
            "severity": data.get("severity", ""),
            "trigger": data.get("trigger", ""),
            "default_strategy": data.get("default_strategy", ""),
            "evaluation_capacity": data.get("evaluation_capacity", ""),
            "recovery_path": data.get("recovery_path", ""),
            "vulnerability": data.get("vulnerability", ""),
            "recommendation": data.get("recommendation", ""),
        }
