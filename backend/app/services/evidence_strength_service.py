"""EvidenceStrengthService — scores claims by methodology, sample size, and replication signals."""

import re
import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim_ledger import ClaimMention, GlobalClaim

logger = structlog.get_logger(__name__)

METHODOLOGY_KEYWORDS = {
    "meta_analysis": (["meta-analysis", "meta analysis", "systematic review", "pooled analysis"], 25),
    "rct": (["randomized controlled", "randomised controlled", "rct", "double-blind", "placebo-controlled"], 22),
    "longitudinal": (["longitudinal", "cohort study", "prospective study", "follow-up study"], 18),
    "experimental": (["experiment", "controlled experiment", "ablation study", "a/b test"], 16),
    "benchmark": (["benchmark", "evaluation on", "tested on", "evaluated on", "sota", "state-of-the-art"], 14),
    "observational": (["observational", "cross-sectional", "survey", "case study", "retrospective"], 10),
    "theoretical": (["theoretical", "proof", "theorem", "formal analysis", "mathematical"], 8),
    "anecdotal": (["anecdotal", "preliminary", "pilot", "exploratory", "qualitative"], 5),
}

SAMPLE_SIZE_PATTERNS = [
    (r"n\s*[=≈>]\s*([\d,]+)", 1),
    (r"(\d[\d,]*)\s*(participants|subjects|patients|samples|instances|examples|documents|images)", 1),
    (r"([\d,]+)\s*(datasets?|benchmarks?|tasks?)", 1),
    (r"trained on\s*([\d.]+)\s*(million|billion|M|B|k|K)", 1),
]

REPLICATION_SIGNALS = [
    "replicated", "reproduced", "independently confirmed", "consistent with",
    "corroborates", "in line with", "aligns with previous", "confirms earlier",
    "multiple studies", "across datasets", "cross-validated",
]

STATISTICAL_RIGOR_SIGNALS = [
    "p < ", "p-value", "confidence interval", "ci ", "statistical significance",
    "effect size", "cohen's d", "standard deviation", "standard error",
    "bonferroni", "bootstrap", "permutation test", "t-test", "anova",
    "regression analysis", "odds ratio", "hazard ratio",
]

WEAKNESS_SIGNALS = [
    "preliminary", "limited sample", "small-scale", "pilot study",
    "further research needed", "may not generalize", "single dataset",
    "not statistically significant", "marginal improvement", "anecdotal",
]


class EvidenceStrengthService:
    """Scores evidence strength for claims in the global ledger."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def score_text(self, text: str, context: str = "") -> dict:
        """Score a piece of evidence text. Returns breakdown and total score (0-100)."""
        combined = f"{text} {context}".lower()

        methodology = self._score_methodology(combined)
        sample = self._score_sample_size(combined)
        statistical = self._score_statistical_rigor(combined)
        replication = self._score_replication(combined)
        recency = self._score_recency(combined)
        weakness_penalty = self._score_weaknesses(combined)

        raw_total = (
            methodology["score"]
            + sample["score"]
            + statistical["score"]
            + replication["score"]
            + recency["score"]
            - weakness_penalty["penalty"]
        )
        total = max(0, min(100, raw_total))

        return {
            "total": round(total, 1),
            "methodology": methodology,
            "sample_adequacy": sample,
            "statistical_rigor": statistical,
            "replication": replication,
            "recency": recency,
            "weaknesses": weakness_penalty,
        }

    def _score_methodology(self, text: str) -> dict:
        """Score methodology rigor (0-25)."""
        best_type = "unknown"
        best_score = 3

        for method_type, (keywords, score) in METHODOLOGY_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                if score > best_score:
                    best_type = method_type
                    best_score = score

        return {"score": min(25, best_score), "type": best_type}

    def _score_sample_size(self, text: str) -> dict:
        """Score sample adequacy (0-20)."""
        max_n = 0
        for pattern, group in SAMPLE_SIZE_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    num_str = match[0]
                else:
                    num_str = match
                try:
                    n = int(num_str.replace(",", ""))
                    max_n = max(max_n, n)
                except ValueError:
                    pass

        if "million" in text or "billion" in text:
            max_n = max(max_n, 1_000_000)

        if max_n == 0:
            score = 5
        elif max_n < 30:
            score = 8
        elif max_n < 100:
            score = 12
        elif max_n < 1000:
            score = 16
        else:
            score = 20

        return {"score": score, "detected_n": max_n if max_n > 0 else None}

    def _score_statistical_rigor(self, text: str) -> dict:
        """Score statistical reporting quality (0-25)."""
        found = [s for s in STATISTICAL_RIGOR_SIGNALS if s in text]
        count = len(found)

        if count == 0:
            score = 5
        elif count == 1:
            score = 12
        elif count == 2:
            score = 18
        else:
            score = 25

        return {"score": score, "signals_found": count, "signals": found[:5]}

    def _score_replication(self, text: str) -> dict:
        """Score replication/convergence signals (0-15)."""
        found = [s for s in REPLICATION_SIGNALS if s in text]
        count = len(found)

        if count == 0:
            score = 3
        elif count == 1:
            score = 8
        elif count == 2:
            score = 12
        else:
            score = 15

        return {"score": score, "signals_found": count}

    def _score_recency(self, text: str) -> dict:
        """Score recency (0-10). More recent = higher score."""
        year_matches = re.findall(r"20(1\d|2[0-6])", text)
        if not year_matches:
            return {"score": 5, "latest_year": None}

        latest = max(int(f"20{y}") for y in year_matches)
        current_year = datetime.now(timezone.utc).year

        age = current_year - latest
        if age <= 1:
            score = 10
        elif age <= 3:
            score = 8
        elif age <= 5:
            score = 6
        else:
            score = 4

        return {"score": score, "latest_year": latest}

    def _score_weaknesses(self, text: str) -> dict:
        """Detect weakness signals that reduce confidence."""
        found = [s for s in WEAKNESS_SIGNALS if s in text]
        penalty = min(15, len(found) * 5)
        return {"penalty": penalty, "signals": found[:5]}

    async def score_mention(self, mention_id: str) -> dict:
        """Score a specific claim mention and persist the result."""
        result = await self.db.execute(
            select(ClaimMention).where(ClaimMention.id == uuid.UUID(mention_id))
        )
        mention = result.scalar_one_or_none()
        if not mention:
            return {"error": "Mention not found"}

        context_parts = []
        if mention.evidence:
            for ev in mention.evidence:
                if isinstance(ev, dict):
                    context_parts.append(ev.get("text", ""))
                elif isinstance(ev, str):
                    context_parts.append(ev)
        if mention.metadata_json:
            context_parts.append(str(mention.metadata_json))

        breakdown = self.score_text(mention.original_text, " ".join(context_parts))

        mention.strength_score = breakdown["total"]
        mention.strength_breakdown = breakdown
        await self.db.commit()

        return {
            "mention_id": mention_id,
            "strength_score": breakdown["total"],
            "breakdown": breakdown,
        }

    async def score_global_claim(self, claim_id: str) -> dict:
        """Aggregate evidence strength across all mentions of a global claim."""
        result = await self.db.execute(
            select(GlobalClaim).where(GlobalClaim.id == uuid.UUID(claim_id))
        )
        claim = result.scalar_one_or_none()
        if not claim:
            return {"error": "Claim not found"}

        mentions_q = await self.db.execute(
            select(ClaimMention).where(ClaimMention.global_claim_id == claim.id)
        )
        mentions = mentions_q.scalars().all()

        if not mentions:
            return {"claim_id": claim_id, "evidence_strength_score": 0, "mentions_scored": 0}

        support_scores = []
        contradict_scores = []
        all_scores = []

        for mention in mentions:
            if not mention.strength_score:
                context_parts = []
                if mention.evidence:
                    for ev in mention.evidence:
                        if isinstance(ev, dict):
                            context_parts.append(ev.get("text", ""))
                        elif isinstance(ev, str):
                            context_parts.append(ev)

                breakdown = self.score_text(mention.original_text, " ".join(context_parts))
                mention.strength_score = breakdown["total"]
                mention.strength_breakdown = breakdown

            all_scores.append(mention.strength_score)
            if mention.stance in ("supports", "supported"):
                support_scores.append(mention.strength_score)
            elif mention.stance in ("contradicts", "refuted"):
                contradict_scores.append(mention.strength_score)

        weighted_support = sum(support_scores) / len(support_scores) if support_scores else 0
        weighted_contradict = sum(contradict_scores) / len(contradict_scores) if contradict_scores else 0

        unique_sources = len(set(m.paper_id for m in mentions if m.paper_id))
        replication_bonus = min(15, unique_sources * 5) if unique_sources > 1 else 0

        overall = max(all_scores) if all_scores else 0
        overall_with_replication = min(100, overall + replication_bonus)

        claim.evidence_strength_score = round(overall_with_replication, 1)
        claim.weighted_support = round(weighted_support, 1)
        claim.weighted_contradict = round(weighted_contradict, 1)
        claim.replication_score = round(replication_bonus, 1)
        claim.strength_breakdown = {
            "max_mention_score": round(overall, 1),
            "replication_bonus": replication_bonus,
            "mentions_scored": len(all_scores),
            "support_avg": round(weighted_support, 1),
            "contradict_avg": round(weighted_contradict, 1),
        }

        await self.db.commit()

        return {
            "claim_id": claim_id,
            "canonical_text": claim.canonical_text,
            "evidence_strength_score": claim.evidence_strength_score,
            "weighted_support": claim.weighted_support,
            "weighted_contradict": claim.weighted_contradict,
            "replication_score": claim.replication_score,
            "mentions_scored": len(all_scores),
            "breakdown": claim.strength_breakdown,
        }

    async def score_all_claims(self) -> dict:
        """Score all active global claims. Used for batch scoring."""
        result = await self.db.execute(
            select(GlobalClaim).where(GlobalClaim.status != "rejected")
        )
        claims = result.scalars().all()

        scored = []
        for claim in claims:
            r = await self.score_global_claim(str(claim.id))
            if "error" not in r:
                scored.append({
                    "claim_id": str(claim.id),
                    "text": claim.canonical_text[:80],
                    "score": r["evidence_strength_score"],
                })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return {
            "total_scored": len(scored),
            "claims": scored,
        }
