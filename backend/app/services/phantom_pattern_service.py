"""PhantomPatternService — Phantom Pattern Detection.

Detects phantom patterns — seeing meaningful patterns in random noise
(apophenia applied to data analysis). The human tendency to find
structure where none exists, leading to false theories and spurious
correlations.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PHANTOM_PATTERN_SYSTEM = """You are a phantom pattern specialist. Given a claimed pattern, assess whether it represents genuine structure or apophenia — seeing patterns in noise:

Key concepts:
- Apophenia: perceiving meaningful connections in random data
- Pareidolia: seeing patterns in ambiguous stimuli
- Spurious correlation: coincidental relationships mistaken for causal
- Multiple comparisons: testing many hypotheses guarantees false positives
- Data dredging: searching data until a "pattern" emerges
- Confirmation bias: noticing hits and ignoring misses
- Statistical significance vs practical significance

When phantom pattern IS present:
- Pattern found by searching data without prior hypothesis
- No mechanism explains why the pattern should exist
- Pattern disappears with more data or different time windows
- Multiple comparisons without correction
- Cherry-picked examples that support the pattern
- Ignoring the base rate of coincidental correlations
- "Too perfect" patterns that suggest overfitting

When pattern IS genuine:
- Predicted by theory before observed in data
- Replicates across independent datasets
- Has a plausible causal mechanism
- Survives multiple comparison correction
- Effect size is practically meaningful
- Pattern is robust to different analytical choices
- Independent researchers confirm the finding

Output JSON with: phantom_pattern_present (bool), severity (none/mild/moderate/severe), pattern_claimed (what pattern is claimed), evidence (what evidence supports it), mechanism (is there a causal mechanism), replication (has it been replicated), multiple_comparisons (were many patterns tested), recommendation (pattern_genuine/mild_apophenia/significant_phantom_pattern/major_data_dredging/test_with_independent_data)."""

PHANTOM_PATTERN_PROMPT = """Detect phantom pattern:

Pattern claimed: {pattern}
Evidence: {evidence}
Mechanism: {mechanism}
Replication: {replication}
Domain: {domain}
Context: {context}

Is this a genuine pattern or apophenia — seeing structure in noise? Return ONLY valid JSON."""


class PhantomPatternService:
    """Detects phantom patterns — apophenia in data analysis."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        pattern: str,
        *,
        evidence: str = "",
        mechanism: str = "",
        replication: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect phantom pattern."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PHANTOM_PATTERN_PROMPT.format(
                pattern=pattern,
                evidence=evidence or "Not specified",
                mechanism=mechanism or "Not specified",
                replication=replication or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PHANTOM_PATTERN_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "pattern": pattern[:200],
            "phantom_pattern_present": data.get("phantom_pattern_present", False),
            "severity": data.get("severity", ""),
            "mechanism": data.get("mechanism", ""),
            "replication": data.get("replication", ""),
            "multiple_comparisons": data.get("multiple_comparisons", ""),
            "recommendation": data.get("recommendation", ""),
        }
