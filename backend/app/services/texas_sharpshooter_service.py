"""TexasSharpshooterService — Texas Sharpshooter Fallacy Detection.

Detects the Texas Sharpshooter fallacy — drawing the target around
the bullet holes after shooting. Finding patterns in random data
and treating them as meaningful. Cherry-picking data clusters and
ignoring the misses. Named after the joke about the Texan who
shoots at a barn wall then paints the bullseye around the tightest
cluster of holes.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TEXAS_SYSTEM = """You are a Texas Sharpshooter fallacy specialist. Given a claimed pattern or finding, assess whether the target was drawn after the shot:

Key concepts:
- Texas Sharpshooter: finding patterns in random data after the fact
- Post-hoc pattern matching: seeing clusters in noise and calling them significant
- Multiple comparisons problem: test enough hypotheses and some will be "significant" by chance
- Data dredging/p-hacking: mining data until something looks significant
- Cherry-picking: selecting data that supports a conclusion, ignoring the rest
- Apophenia: perceiving meaningful connections in random information
- Look-elsewhere effect: the more places you look, the more "patterns" you find

When the fallacy IS present:
- The hypothesis was formed AFTER seeing the data
- Only the "hits" are counted, misses are ignored
- Multiple comparisons without correction
- The pattern was not predicted in advance
- No pre-registration or pre-specified analysis plan
- Subgroup analysis without theoretical justification

When the pattern IS meaningful:
- Hypothesis was specified before data collection
- The pattern replicates in independent data
- There's a causal mechanism explaining the pattern
- Appropriate statistical corrections were applied
- The effect size is large relative to noise
- Pre-registered analysis plan was followed

Output JSON with: texas_sharpshooter_present (bool), severity (none/mild/moderate/severe), claimed_pattern (what pattern is being claimed), data_examined (how much data was searched), hypothesis_timing (was the hypothesis before or after the data?), cherry_picking (bool — are misses being ignored?), multiple_comparisons (bool — were many tests run?), correction_applied (bool — was Bonferroni or similar correction used?), replication (bool — has the pattern been independently replicated?), causal_mechanism (is there a plausible explanation?), base_rate_of_pattern (how likely is this pattern by chance?), degrees_of_freedom (how many ways could a "pattern" have been found?), pre_registration (bool — was the analysis pre-specified?), effect_size (how large is the claimed effect?), noise_level (how noisy is the underlying data?), what_was_ignored (what data points don't fit the pattern?), recommendation (pattern_genuine/mild_post_hoc/significant_sharpshooter/major_data_dredging/replicate_before_believing)."""

TEXAS_PROMPT = """Detect Texas Sharpshooter fallacy:

Claimed pattern: {pattern}
Data source: {data_source}
How discovered: {discovery}
What was tested: {tested}
Domain: {domain}
Context: {context}

Was the target drawn after the shot? Return ONLY valid JSON."""


class TexasSharpshooterService:
    """Detects Texas Sharpshooter fallacy — post-hoc pattern finding in random data."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        pattern: str,
        *,
        data_source: str = "",
        discovery: str = "",
        tested: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect Texas Sharpshooter fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TEXAS_PROMPT.format(
                pattern=pattern,
                data_source=data_source or "Not specified",
                discovery=discovery or "Not specified",
                tested=tested or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=TEXAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "pattern": pattern[:200],
            "texas_sharpshooter_present": data.get("texas_sharpshooter_present", False),
            "severity": data.get("severity", ""),
            "claimed_pattern": data.get("claimed_pattern", ""),
            "data_examined": data.get("data_examined", ""),
            "hypothesis_timing": data.get("hypothesis_timing", ""),
            "cherry_picking": data.get("cherry_picking", False),
            "multiple_comparisons": data.get("multiple_comparisons", False),
            "correction_applied": data.get("correction_applied", False),
            "replication": data.get("replication", False),
            "causal_mechanism": data.get("causal_mechanism", ""),
            "base_rate_of_pattern": data.get("base_rate_of_pattern", ""),
            "degrees_of_freedom": data.get("degrees_of_freedom", ""),
            "pre_registration": data.get("pre_registration", False),
            "effect_size": data.get("effect_size", ""),
            "noise_level": data.get("noise_level", ""),
            "what_was_ignored": data.get("what_was_ignored", ""),
            "recommendation": data.get("recommendation", ""),
        }
