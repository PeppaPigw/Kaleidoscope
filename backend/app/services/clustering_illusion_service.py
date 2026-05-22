"""ClusteringIllusionService — Clustering Illusion Detection.

Detects the clustering illusion — seeing meaningful patterns in
random data. Gilovich (1991). The "hot hand" in basketball,
cancer clusters that are actually random, stock chart patterns.
Humans are pattern-seeking machines that find signal in noise.
Related to apophenia and the Texas sharpshooter fallacy.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CLUSTERING_SYSTEM = """You are a clustering illusion specialist. Given a claimed pattern, assess whether the pattern is likely real or an artifact of randomness:

Key concepts (Gilovich, 1991):
- Clustering illusion: seeing patterns in random sequences
- Hot hand fallacy: believing streaks in random events are meaningful
- Apophenia: tendency to perceive connections between unrelated things
- Texas sharpshooter overlap: but clustering is about perceiving, not selecting
- Misconceptions of randomness: expecting random data to "look random"
- Law of small numbers: expecting small samples to be representative

When the clustering illusion IS present:
- Seeing streaks or patterns in genuinely random data
- "Hot hand" beliefs in independent events
- Cancer cluster fears in areas with expected random variation
- Stock chart "patterns" in random walks
- Believing coincidences are meaningful
- "This can't be random" when it statistically can be

When the pattern IS real:
- Statistical tests confirm the pattern exceeds chance
- There's a plausible causal mechanism
- The pattern replicates in independent samples
- The effect size is large relative to expected random variation
- The pattern was predicted before being observed (not post-hoc)
- Base rates and sample sizes support the inference

Output JSON with: clustering_illusion_present (bool), severity (none/mild/moderate/severe), claimed_pattern (what pattern is being perceived), data_source (where does the data come from), sample_size (how much data is the pattern based on), expected_randomness (what would random data look like here?), statistical_test (has the pattern been tested?), base_rate (what's the expected frequency by chance?), causal_mechanism (is there a plausible cause?), replication (has the pattern been replicated?), prediction_vs_postdiction (was the pattern predicted or found after?), hot_hand_variant (bool — is this a streak belief in independent events?), recommendation (pattern_likely_real/mild_clustering_illusion/significant_apophenia/major_pattern_in_noise/test_statistically)."""

CLUSTERING_PROMPT = """Detect clustering illusion:

Claimed pattern: {pattern}
Data: {data}
Sample size: {sample}
Statistical evidence: {statistics}
Domain: {domain}
Context: {context}

Is this a real pattern or an illusion from random data? Return ONLY valid JSON."""


class ClusteringIllusionService:
    """Detects clustering illusion — seeing patterns in random data."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        pattern: str,
        *,
        data: str = "",
        sample: str = "",
        statistics: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect clustering illusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CLUSTERING_PROMPT.format(
                pattern=pattern,
                data=data or "Not specified",
                sample=sample or "Not specified",
                statistics=statistics or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CLUSTERING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data_result = parse_llm_json(raw)

        return {
            "pattern": pattern[:200],
            "clustering_illusion_present": data_result.get("clustering_illusion_present", False),
            "severity": data_result.get("severity", ""),
            "claimed_pattern": data_result.get("claimed_pattern", ""),
            "data_source": data_result.get("data_source", ""),
            "sample_size": data_result.get("sample_size", ""),
            "expected_randomness": data_result.get("expected_randomness", ""),
            "statistical_test": data_result.get("statistical_test", ""),
            "base_rate": data_result.get("base_rate", ""),
            "causal_mechanism": data_result.get("causal_mechanism", ""),
            "replication": data_result.get("replication", ""),
            "prediction_vs_postdiction": data_result.get("prediction_vs_postdiction", ""),
            "hot_hand_variant": data_result.get("hot_hand_variant", False),
            "recommendation": data_result.get("recommendation", ""),
        }
