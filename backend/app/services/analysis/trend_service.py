"""Trend & Topic Analysis service — BERTopic clustering, hot topics, emerging entities.

P2 WS-2: §10 (#73-80) from FeasibilityAnalysis.md

Provides:
- Topic clustering using BERTopic on paper abstracts
- Hot keyword detection via frequency time series
- Emerging author/institution discovery
- Topic evolution tracking
"""

from collections import Counter, defaultdict
from datetime import date, timedelta

import structlog
from sqlalchemy import func, select, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.paper import Paper
from app.models.author import Author, PaperAuthor
from app.models.topic import Topic, PaperTopic

logger = structlog.get_logger(__name__)


class TopicService:
    """BERTopic-based topic clustering and management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_topics(
        self, limit: int = 50, sort_by: str = "paper_count"
    ) -> list[dict]:
        """List all discovered topics, sorted by paper count or trend."""
        order = Topic.paper_count.desc()
        if sort_by == "label":
            order = Topic.label.asc()
        elif sort_by == "trend":
            order = Topic.trend_direction.asc()

        result = await self.db.execute(
            select(Topic).order_by(order).limit(limit)
        )
        topics = result.scalars().all()
        return [
            {
                "id": str(t.id),
                "label": t.label,
                "keywords": t.keywords or [],
                "paper_count": t.paper_count,
                "trend_direction": t.trend_direction,
                "description": t.description,
            }
            for t in topics
        ]

    async def get_topic(self, topic_id: str) -> dict | None:
        """Get topic detail with representative papers."""
        result = await self.db.execute(
            select(Topic).where(Topic.id == topic_id)
        )
        topic = result.scalar_one_or_none()
        if not topic:
            return None

        # Get associated papers
        papers_result = await self.db.execute(
            select(Paper.id, Paper.title, Paper.doi, Paper.published_at, PaperTopic.probability)
            .join(PaperTopic, PaperTopic.paper_id == Paper.id)
            .where(PaperTopic.topic_id == topic_id, Paper.deleted_at.is_(None))
            .order_by(PaperTopic.probability.desc())
            .limit(50)
        )
        papers = [
            {
                "id": str(r.id),
                "title": r.title,
                "doi": r.doi,
                "published_at": str(r.published_at) if r.published_at else None,
                "probability": round(r.probability, 4),
            }
            for r in papers_result.all()
        ]

        return {
            "id": str(topic.id),
            "label": topic.label,
            "keywords": topic.keywords or [],
            "paper_count": topic.paper_count,
            "trend_direction": topic.trend_direction,
            "description": topic.description,
            "papers": papers,
        }

    async def refresh_topics(self) -> dict:
        """
        Re-run BERTopic clustering on all paper abstracts.

        This is an expensive operation — should be run as a background task.
        """
        log = logger.bind(operation="topic_refresh")

        # 1. Load abstracts
        result = await self.db.execute(
            select(Paper.id, Paper.abstract)
            .where(Paper.deleted_at.is_(None), Paper.abstract.is_not(None))
        )
        rows = result.all()
        if len(rows) < 20:
            return {"status": "skipped", "reason": "too_few_papers", "count": len(rows)}

        paper_ids = [str(r.id) for r in rows]
        docs = [r.abstract for r in rows]
        log.info("topic_clustering_start", n_docs=len(docs))

        # 2. Run BERTopic
        try:
            from bertopic import BERTopic

            topic_model = BERTopic(
                language="english",
                min_topic_size=max(5, len(docs) // 50),
                nr_topics="auto",
                verbose=False,
            )
            topics_assigned, probs = topic_model.fit_transform(docs)
        except ImportError:
            log.warning("bertopic_not_installed")
            return {"status": "error", "reason": "bertopic not installed"}
        except Exception as e:
            log.error("bertopic_failed", error=str(e))
            return {"status": "error", "reason": str(e)}

        # 3. Clear old topic assignments
        await self.db.execute(
            PaperTopic.__table__.delete()
        )
        await self.db.execute(
            Topic.__table__.delete()
        )

        # 4. Create new topics and assignments
        topic_info = topic_model.get_topic_info()
        topic_map = {}  # bertopic_id → db Topic

        for _, row_info in topic_info.iterrows():
            bt_id = row_info["Topic"]
            if bt_id == -1:  # Outlier topic
                continue

            # Get top keywords for this topic
            topic_words = topic_model.get_topic(bt_id)
            keywords = [w for w, _ in (topic_words or [])[:10]]

            # Get representative doc indices
            rep_indices = [
                i for i, t in enumerate(topics_assigned) if t == bt_id
            ][:5]
            rep_docs = [paper_ids[i] for i in rep_indices]

            topic = Topic(
                label=", ".join(keywords[:3]),
                keywords=keywords,
                representative_docs=rep_docs,
                paper_count=row_info.get("Count", 0),
                cluster_id=bt_id,
                trend_direction="stable",
            )
            self.db.add(topic)
            await self.db.flush()
            topic_map[bt_id] = topic

        # 5. Create paper-topic assignments
        for i, (pid, bt_topic) in enumerate(zip(paper_ids, topics_assigned)):
            if bt_topic == -1 or bt_topic not in topic_map:
                continue
            prob = float(probs[i]) if probs is not None and i < len(probs) else 1.0
            assignment = PaperTopic(
                paper_id=pid,
                topic_id=str(topic_map[bt_topic].id),
                probability=prob,
            )
            self.db.add(assignment)

        await self.db.commit()

        n_topics = len(topic_map)
        log.info("topic_clustering_complete", n_topics=n_topics, n_papers=len(docs))
        return {
            "status": "complete",
            "topics_created": n_topics,
            "papers_processed": len(docs),
        }


class TrendService:
    """Time series analysis for keyword trends and emerging entities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def hot_keywords(
        self, top_k: int = 30, years_back: int = 3
    ) -> list[dict]:
        """
        Discover hot keywords by frequency growth rate.

        Computes keyword frequency per year, then ranks by
        year-over-year growth rate.
        """
        cutoff = date.today() - timedelta(days=years_back * 365)

        result = await self.db.execute(
            select(Paper.keywords, Paper.published_at)
            .where(
                Paper.deleted_at.is_(None),
                Paper.keywords.is_not(None),
                Paper.published_at >= cutoff,
            )
        )

        # Count keywords per year
        year_counts: dict[str, Counter] = defaultdict(Counter)
        for row in result.all():
            if not row.keywords or not row.published_at:
                continue
            year = row.published_at.year
            kws = row.keywords if isinstance(row.keywords, list) else []
            for kw in kws:
                if isinstance(kw, str):
                    year_counts[str(year)][kw.lower()] += 1

        if not year_counts:
            return []

        # Compute growth rates
        years = sorted(year_counts.keys())
        all_keywords: set[str] = set()
        for counts in year_counts.values():
            all_keywords.update(counts.keys())

        growth_data = []
        for kw in all_keywords:
            total = sum(year_counts[y].get(kw, 0) for y in years)
            if total < 3:
                continue  # Skip very rare keywords

            # Simple growth rate: (last year / first year) normalized
            first_count = year_counts[years[0]].get(kw, 0)
            last_count = year_counts[years[-1]].get(kw, 0)
            if first_count == 0:
                growth = float(last_count) if last_count > 0 else 0.0
            else:
                growth = (last_count - first_count) / first_count

            per_year = {y: year_counts[y].get(kw, 0) for y in years}
            growth_data.append({
                "keyword": kw,
                "total_count": total,
                "growth_rate": round(growth, 3),
                "per_year": per_year,
                "trend": "rising" if growth > 0.3 else "declining" if growth < -0.3 else "stable",
            })

        growth_data.sort(key=lambda x: x["growth_rate"], reverse=True)
        return growth_data[:top_k]

    async def emerging_authors(
        self, top_k: int = 20, recent_years: int = 2
    ) -> list[dict]:
        """
        Find emerging researchers: first publication in recent N years + high impact.

        Ranks by citation growth rate among recent-entry authors.
        """
        from app.models.author import Institution

        cutoff = date.today() - timedelta(days=recent_years * 365)

        # Find authors whose earliest paper is after cutoff
        # Author model uses display_name (not name) and institution_id FK
        result = await self.db.execute(
            select(
                Author.id,
                Author.display_name,
                Institution.name.label("affiliation"),
                func.min(Paper.published_at).label("first_pub"),
                func.sum(Paper.citation_count).label("total_cites"),
                func.count(Paper.id).label("paper_count"),
            )
            .join(PaperAuthor, PaperAuthor.author_id == Author.id)
            .join(Paper, Paper.id == PaperAuthor.paper_id)
            .outerjoin(Institution, Institution.id == Author.institution_id)
            .where(Paper.deleted_at.is_(None))
            .group_by(Author.id, Author.display_name, Institution.name)
            .having(func.min(Paper.published_at) >= cutoff)
            .order_by(func.sum(Paper.citation_count).desc().nullslast())
            .limit(top_k)
        )

        return [
            {
                "author_id": str(r.id),
                "name": r.display_name,
                "affiliation": r.affiliation,
                "first_publication": str(r.first_pub) if r.first_pub else None,
                "total_citations": r.total_cites or 0,
                "paper_count": r.paper_count,
            }
            for r in result.all()
        ]

    async def sleeping_beauties(self, top_k: int = 10) -> list[dict]:
        """
        Find 'sleeping beauty' papers: old papers with recent citation spikes.

        Simplified heuristic: papers published >5 years ago with high
        citation count relative to their age.
        """
        cutoff_old = date.today() - timedelta(days=5 * 365)
        cutoff_recent = date.today() - timedelta(days=2 * 365)

        result = await self.db.execute(
            select(Paper)
            .where(
                Paper.deleted_at.is_(None),
                Paper.published_at <= cutoff_old,
                Paper.citation_count > 10,
                Paper.citation_count_updated_at >= cutoff_recent,
            )
            .order_by(Paper.citation_count.desc())
            .limit(top_k)
        )

        papers = result.scalars().all()
        return [
            {
                "id": str(p.id),
                "title": p.title,
                "doi": p.doi,
                "published_at": str(p.published_at) if p.published_at else None,
                "citation_count": p.citation_count,
                "years_old": (
                    (date.today() - p.published_at).days // 365
                    if p.published_at else None
                ),
            }
            for p in papers
        ]
