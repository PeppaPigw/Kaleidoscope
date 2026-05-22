"""ResearchMemoryService — Persistent Research Intelligence.

Manages persistent research memory: stores insights, tracks what's been
learned across sessions, identifies patterns across investigations, and
prevents re-discovery of known facts. The agent's long-term memory for
research intelligence.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MEMORY_DIR = Path("/Users/pigpeppa/Downloads/Kaleidoscope/backend/.research_memory")


class ResearchMemoryService:
    """Persistent research memory across sessions."""

    def __init__(self, db: AsyncSession):
        self.db = db
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    async def store_insight(
        self,
        insight: str,
        *,
        domain: str = "",
        confidence: float = 0.5,
        source_tools: list[str] | None = None,
        question: str = "",
        tags: list[str] | None = None,
    ) -> dict:
        """Store a research insight for future reference."""
        entry = {
            "id": datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f"),
            "insight": insight,
            "domain": domain,
            "confidence": confidence,
            "source_tools": source_tools or [],
            "question": question,
            "tags": tags or [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        file_path = MEMORY_DIR / f"{entry['id']}.json"
        file_path.write_text(json.dumps(entry, indent=2))

        return {"stored": True, "id": entry["id"], "path": str(file_path)}

    async def recall(
        self,
        query: str,
        *,
        domain: str = "",
        limit: int = 10,
    ) -> dict:
        """Recall relevant insights from memory."""
        all_insights = self._load_all()

        # Simple relevance scoring: keyword overlap
        query_words = set(query.lower().split())
        scored = []
        for entry in all_insights:
            text = f"{entry.get('insight', '')} {entry.get('domain', '')} {' '.join(entry.get('tags', []))}".lower()
            text_words = set(text.split())
            overlap = len(query_words & text_words)
            if domain and domain.lower() in text:
                overlap += 3
            if overlap > 0:
                scored.append((overlap, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = [entry for _, entry in scored[:limit]]

        return {
            "query": query,
            "results": results,
            "total_in_memory": len(all_insights),
            "matched": len(results),
        }

    async def summarize_memory(
        self,
        *,
        domain: str = "",
    ) -> dict:
        """Summarize what's in research memory."""
        all_insights = self._load_all()

        if domain:
            all_insights = [i for i in all_insights if domain.lower() in i.get("domain", "").lower()]

        domains = {}
        for entry in all_insights:
            d = entry.get("domain", "general")
            domains[d] = domains.get(d, 0) + 1

        high_confidence = [i for i in all_insights if i.get("confidence", 0) >= 0.8]
        low_confidence = [i for i in all_insights if i.get("confidence", 0) < 0.4]

        return {
            "total_insights": len(all_insights),
            "domains": domains,
            "high_confidence_count": len(high_confidence),
            "low_confidence_count": len(low_confidence),
            "recent": all_insights[-5:] if all_insights else [],
        }

    def _load_all(self) -> list[dict]:
        insights = []
        if not MEMORY_DIR.exists():
            return insights
        for f in sorted(MEMORY_DIR.glob("*.json")):
            try:
                insights.append(json.loads(f.read_text()))
            except (json.JSONDecodeError, OSError):
                continue
        return insights
