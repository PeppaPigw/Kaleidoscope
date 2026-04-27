"""Retrieval evaluation harness — offline benchmarks and grounding checks."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

BENCHMARK_DIR = Path(__file__).resolve().parent.parent.parent / "benchmarks"


class RetrievalBenchmark:
    """Gold-corpus QA evaluation harness."""

    def __init__(self, corpus_path: str | Path | None = None):
        self.corpus_path = (
            Path(corpus_path) if corpus_path else BENCHMARK_DIR / "gold_corpus.json"
        )
        self._corpus: list[dict[str, Any]] = []

    def load_corpus(self) -> list[dict[str, Any]]:
        """Load the gold QA corpus from JSON."""
        if not self.corpus_path.exists():
            logger.warning("benchmark_corpus_not_found", path=str(self.corpus_path))
            return []
        with open(self.corpus_path) as f:
            self._corpus = json.load(f)
        logger.info("benchmark_corpus_loaded", count=len(self._corpus))
        return self._corpus

    async def evaluate_retrieval(
        self,
        retriever_fn: Any,
        top_k: int = 10,
    ) -> dict[str, Any]:
        """Run retrieval evaluation against the gold corpus."""
        if not self._corpus:
            self.load_corpus()
        if not self._corpus:
            return {"error": "No benchmark corpus available"}

        results: list[dict[str, Any]] = []
        total_recall = 0.0
        total_precision = 0.0
        total_latency = 0.0

        for item in self._corpus:
            question = item["question"]
            gold_paper_ids = set(item.get("gold_paper_ids", []))

            started = time.perf_counter()
            try:
                retrieved = await retriever_fn(question, top_k=top_k)
            except Exception as exc:  # noqa: BLE001
                results.append(
                    {
                        "question": question,
                        "error": str(exc),
                        "recall": 0.0,
                        "precision": 0.0,
                    }
                )
                continue
            latency = (time.perf_counter() - started) * 1000

            retrieved_ids = set()
            for chunk in retrieved:
                pid = chunk.get(
                    "paper_id", chunk.get("metadata", {}).get("paper_id", "")
                )
                if pid:
                    retrieved_ids.add(pid)

            if gold_paper_ids:
                recall = len(retrieved_ids & gold_paper_ids) / len(gold_paper_ids)
                precision = (
                    len(retrieved_ids & gold_paper_ids) / len(retrieved_ids)
                    if retrieved_ids
                    else 0.0
                )
            else:
                recall = 0.0
                precision = 0.0

            total_recall += recall
            total_precision += precision
            total_latency += latency

            results.append(
                {
                    "question": question,
                    "category": item.get("category", "unknown"),
                    "recall": round(recall, 3),
                    "precision": round(precision, 3),
                    "retrieved_count": len(retrieved_ids),
                    "gold_count": len(gold_paper_ids),
                    "latency_ms": round(latency, 1),
                }
            )

        n = len(results) or 1
        return {
            "total_questions": len(results),
            "avg_recall_at_k": round(total_recall / n, 3),
            "avg_precision_at_k": round(total_precision / n, 3),
            "avg_latency_ms": round(total_latency / n, 1),
            "results": results,
        }


class GroundingChecker:
    """Verify that generated answers are grounded in retrieved evidence."""

    @staticmethod
    def check_grounding(
        answer: str,
        sources: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Check how well an answer is grounded in its sources."""
        if not answer or not sources:
            return {
                "grounded": False,
                "coverage": 0.0,
                "source_count": len(sources),
                "sentences_checked": 0,
            }

        sentences = [s.strip() for s in answer.split(".") if len(s.strip()) > 10]
        source_text = " ".join(
            s.get("content", s.get("text", "")) for s in sources
        ).lower()

        grounded_count = 0
        for sentence in sentences:
            words = sentence.lower().split()
            key_words = [w for w in words if len(w) > 4]
            if not key_words:
                continue
            match_count = sum(1 for w in key_words if w in source_text)
            if match_count / len(key_words) > 0.4:
                grounded_count += 1

        coverage = grounded_count / len(sentences) if sentences else 0.0
        return {
            "grounded": coverage > 0.7,
            "coverage": round(coverage, 3),
            "source_count": len(sources),
            "sentences_checked": len(sentences),
            "sentences_grounded": grounded_count,
        }


class LatencyCostTracker:
    """Track latency and cost metrics for observability."""

    MAX_ENTRIES = 10_000

    def __init__(self) -> None:
        self._metrics: list[dict[str, Any]] = []

    def record(
        self,
        operation: str,
        latency_ms: float,
        tokens_used: int = 0,
        route: str = "",
    ) -> None:
        """Record a single operation metric (capped at MAX_ENTRIES)."""
        self._metrics.append(
            {
                "operation": operation,
                "latency_ms": round(latency_ms, 1),
                "tokens_used": tokens_used,
                "route": route,
                "timestamp": time.time(),
            }
        )
        # Evict oldest entries if over cap
        if len(self._metrics) > self.MAX_ENTRIES:
            self._metrics = self._metrics[-self.MAX_ENTRIES :]

    def summary(self) -> dict[str, Any]:
        """Get summary statistics."""
        if not self._metrics:
            return {"count": 0}

        latencies = [m["latency_ms"] for m in self._metrics]
        latencies.sort()
        n = len(latencies)
        return {
            "count": n,
            "avg_latency_ms": round(sum(latencies) / n, 1),
            "p50_latency_ms": latencies[n // 2],
            "p95_latency_ms": latencies[int(n * 0.95)],
            "p99_latency_ms": latencies[int(n * 0.99)],
            "total_tokens": sum(m["tokens_used"] for m in self._metrics),
            "by_route": self._group_by("route"),
            "by_operation": self._group_by("operation"),
        }

    def _group_by(self, key: str) -> dict[str, dict[str, Any]]:
        """Group metrics by a key and compute per-group stats."""
        groups: dict[str, list[float]] = {}
        for m in self._metrics:
            group = m.get(key, "unknown")
            groups.setdefault(group, []).append(m["latency_ms"])
        return {
            group: {
                "count": len(vals),
                "avg_ms": round(sum(vals) / len(vals), 1),
            }
            for group, vals in groups.items()
        }
