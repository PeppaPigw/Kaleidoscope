"""TopicMonitorService — living research surveillance for dossiers."""

import uuid
from datetime import datetime, timedelta, timezone

import httpx
import structlog
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dossier import ResearchDossier
from app.models.paper import Paper
from app.models.topic_monitor import TopicMonitor, TopicMonitorRun
from app.services.claim_ledger_service import ClaimLedgerService

logger = structlog.get_logger(__name__)

CLAIM_INDICATORS = [
    "we show", "we demonstrate", "we find", "results show",
    "outperform", "achieve", "improve", "significantly",
    "we propose", "we introduce", "our method", "our approach",
    "we present", "we develop", "novel", "state-of-the-art",
]


class TopicMonitorService:
    """Watches dossier topics for new papers and claim changes."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._ledger = ClaimLedgerService(db)

    async def create_monitor(
        self,
        dossier_id: str,
        topic: str,
        cadence: str = "daily",
        query_config: dict | None = None,
    ) -> dict:
        monitor = TopicMonitor(
            dossier_id=uuid.UUID(dossier_id),
            topic=topic,
            cadence=cadence,
            query_config=query_config or {},
        )
        self.db.add(monitor)
        await self.db.commit()
        return {"monitor_id": str(monitor.id), "topic": topic, "status": "active"}

    async def run_monitor(
        self,
        monitor_id: str | None = None,
        dossier_id: str | None = None,
        lookback_days: int = 30,
        max_papers: int = 20,
    ) -> dict:
        """Run one monitoring cycle: discover papers, extract claims, detect conflicts."""
        # Load monitor
        if monitor_id:
            result = await self.db.execute(
                select(TopicMonitor).where(TopicMonitor.id == uuid.UUID(monitor_id))
            )
            monitor = result.scalar_one_or_none()
        elif dossier_id:
            result = await self.db.execute(
                select(TopicMonitor).where(
                    TopicMonitor.dossier_id == uuid.UUID(dossier_id),
                    TopicMonitor.status == "active",
                ).order_by(TopicMonitor.created_at.desc()).limit(1)
            )
            monitor = result.scalar_one_or_none()
            if not monitor:
                # Get topic from dossier
                dossier_q = await self.db.execute(
                    select(ResearchDossier).where(ResearchDossier.id == uuid.UUID(dossier_id))
                )
                d = dossier_q.scalar_one_or_none()
                topic_for_monitor = d.topic if d else "unknown"
                create_result = await self.create_monitor(dossier_id, topic_for_monitor)
                result = await self.db.execute(
                    select(TopicMonitor).where(
                        TopicMonitor.id == uuid.UUID(create_result["monitor_id"])
                    )
                )
                monitor = result.scalar_one()
        else:
            return {"error": "monitor_id or dossier_id required"}

        # Load dossier
        dossier_result = await self.db.execute(
            select(ResearchDossier).where(
                ResearchDossier.id == monitor.dossier_id
            )
        )
        dossier = dossier_result.scalar_one_or_none()
        if not dossier:
            return {"error": "Dossier not found"}

        topic = monitor.topic or dossier.topic
        papers_seen = dossier.papers_seen or {}

        # Create run record
        run = TopicMonitorRun(monitor_id=monitor.id)
        self.db.add(run)
        await self.db.flush()

        # Build search queries
        queries = [topic]
        if dossier.open_questions:
            for q in dossier.open_questions[:2]:
                if isinstance(q, str) and len(q) > 10:
                    queries.append(q[:100])

        # Discover new papers from OpenAlex
        from_date = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        new_papers = []
        seen_titles = set(
            info.get("title", "").lower()[:60] for info in papers_seen.values()
        )

        async with httpx.AsyncClient(timeout=20.0) as client:
            for query in queries[:3]:
                try:
                    params = {
                        "filter": f"title_and_abstract.search:{query[:80]},from_publication_date:{from_date}",
                        "sort": "cited_by_count:desc",
                        "per_page": min(10, max_papers),
                        "mailto": "kaleidoscope@research.app",
                    }
                    resp = await client.get("https://api.openalex.org/works", params=params)
                    if resp.status_code == 200:
                        for work in resp.json().get("results", []):
                            title = work.get("title", "")
                            if not title or title.lower()[:60] in seen_titles:
                                continue
                            seen_titles.add(title.lower()[:60])
                            abstract_inv = work.get("abstract_inverted_index")
                            abstract = ""
                            if abstract_inv and isinstance(abstract_inv, dict):
                                words = sorted(
                                    ((pos, w) for w, positions in abstract_inv.items() for pos in positions),
                                    key=lambda x: x[0],
                                )
                                abstract = " ".join(w for _, w in words)[:600]
                            new_papers.append({
                                "title": title,
                                "abstract": abstract,
                                "year": work.get("publication_year"),
                                "citations": work.get("cited_by_count", 0),
                                "doi": (work.get("doi") or "").replace("https://doi.org/", ""),
                                "openalex_id": work.get("id", ""),
                                "source": "openalex",
                                "query": query,
                            })
                except Exception as e:
                    logger.warning("monitor_openalex_error", error=str(e)[:100])

        # Also check local DB for recent papers not in dossier
        try:
            local_result = await self.db.execute(text("""
                SELECT id, title, abstract, citation_count, published_at
                FROM papers
                WHERE deleted_at IS NULL
                  AND published_at > :from_date
                  AND title ILIKE :pattern
                ORDER BY citation_count DESC NULLS LAST
                LIMIT :limit
            """), {"from_date": from_date, "pattern": f"%{topic.split()[0]}%", "limit": 10})
            for row in local_result.all():
                title = row[1] or ""
                if title.lower()[:60] not in seen_titles:
                    seen_titles.add(title.lower()[:60])
                    new_papers.append({
                        "title": title,
                        "abstract": row[2] or "",
                        "citations": row[3] or 0,
                        "paper_id": str(row[0]),
                        "source": "local",
                    })
        except Exception:
            pass

        run.papers_checked = len(new_papers)

        # Process new papers: extract claims, upsert to ledger, detect conflicts
        alerts = []
        claims_extracted = 0
        ledger_mentions = 0
        conflicts_found = 0
        papers_added = {}

        for paper in new_papers[:max_papers]:
            title = paper["title"]
            abstract = paper.get("abstract", "")
            combined = f"{title}. {abstract}"

            # Extract claim-like sentences
            claims = self._extract_claims(combined)
            claims_extracted += len(claims)

            # Record paper in dossier
            paper_key = paper.get("paper_id") or paper.get("doi") or title[:50]
            papers_added[paper_key] = {
                "title": title,
                "source": paper.get("source"),
                "citations": paper.get("citations", 0),
                "discovered_by": "monitor",
                "discovered_at": datetime.now(timezone.utc).isoformat(),
            }

            # Upsert claims to ledger and check conflicts
            for claim_text in claims:
                try:
                    upsert_result = await self._ledger.upsert_claim(
                        claim_text,
                        dossier_id=str(monitor.dossier_id),
                        source_tool="topic_monitor",
                        stance="supports",
                    )
                    ledger_mentions += 1

                    conflict_result = await self._ledger.detect_conflicts(
                        claim_text, dossier_id=str(monitor.dossier_id), limit=3
                    )
                    if conflict_result.get("conflicts"):
                        conflicts_found += len(conflict_result["conflicts"])
                        alerts.append({
                            "type": "new_contradiction",
                            "claim": claim_text[:100],
                            "conflicts": [c["text"][:80] for c in conflict_result["conflicts"][:2]],
                            "paper": title,
                        })
                except Exception as e:
                    logger.warning("monitor_claim_error", error=str(e)[:80])

            # High-impact paper alert
            if paper.get("citations", 0) > 50:
                alerts.append({
                    "type": "high_impact_new_paper",
                    "title": title,
                    "citations": paper["citations"],
                })

        # Update dossier
        run.papers_new = len(papers_added)
        run.claims_extracted = claims_extracted
        run.ledger_mentions_added = ledger_mentions
        run.conflicts_found = conflicts_found
        run.alerts_emitted = len(alerts)
        # PLACEHOLDER_FINALIZE
        if papers_added:
            updated_seen = dict(papers_seen)
            updated_seen.update(papers_added)
            await self.db.execute(text("""
                UPDATE research_dossiers
                SET papers_seen = CAST(:papers AS jsonb), updated_at = NOW()
                WHERE id = :id
            """), {"papers": __import__("json").dumps(updated_seen), "id": str(monitor.dossier_id)})

        # Update next_actions if conflicts found
        if alerts:
            conflict_alerts = [a for a in alerts if a["type"] == "new_contradiction"]
            if conflict_alerts:
                new_actions = dossier.next_actions or []
                new_actions.insert(0, f"Investigate {len(conflict_alerts)} new contradiction(s) from monitor")
                await self.db.execute(text("""
                    UPDATE research_dossiers
                    SET next_actions = CAST(:actions AS jsonb), updated_at = NOW()
                    WHERE id = :id
                """), {"actions": __import__("json").dumps(new_actions[:10]), "id": str(monitor.dossier_id)})

        run.finished_at = datetime.now(timezone.utc)
        run.summary = {
            "topic": topic,
            "queries_used": queries[:3],
            "alerts": alerts[:10],
            "new_papers": [p["title"][:80] for p in new_papers[:max_papers]],
        }
        monitor.last_run_at = datetime.now(timezone.utc)
        await self.db.commit()

        return {
            "monitor_id": str(monitor.id),
            "run_id": str(run.id),
            "dossier_id": str(monitor.dossier_id),
            "topic": topic,
            "papers_checked": run.papers_checked,
            "papers_new": run.papers_new,
            "claims_extracted": claims_extracted,
            "ledger_mentions_added": ledger_mentions,
            "conflicts_found": conflicts_found,
            "alerts": alerts[:10],
            "new_papers": [{"title": p["title"], "citations": p.get("citations", 0)} for p in new_papers[:5]],
        }

    def _extract_claims(self, text: str) -> list[str]:
        """Extract claim-like sentences from text."""
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        claims = []
        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 30 or len(sent) > 300:
                continue
            sent_lower = sent.lower()
            if any(ind in sent_lower for ind in CLAIM_INDICATORS):
                claims.append(sent)
                if len(claims) >= 2:
                    break
        # Fallback: last sentence of abstract often contains a claim
        if not claims and len(sentences) > 2:
            last = sentences[-1].strip()
            if 30 < len(last) < 300:
                claims.append(last)
        return claims

    async def get_digest(
        self,
        dossier_id: str,
        since: str | None = None,
    ) -> dict:
        """Get a compact 'what changed' report from recent monitor runs."""
        if since:
            since_dt = datetime.fromisoformat(since)
        else:
            since_dt = datetime.now(timezone.utc) - timedelta(days=7)

        # Find monitor
        result = await self.db.execute(
            select(TopicMonitor).where(
                TopicMonitor.dossier_id == uuid.UUID(dossier_id),
                TopicMonitor.status == "active",
            )
        )
        monitor = result.scalar_one_or_none()
        if not monitor:
            return {"error": "No active monitor for this dossier"}

        # Get recent runs
        runs_result = await self.db.execute(
            select(TopicMonitorRun).where(
                TopicMonitorRun.monitor_id == monitor.id,
                TopicMonitorRun.started_at >= since_dt,
            ).order_by(TopicMonitorRun.started_at.desc())
        )
        runs = runs_result.scalars().all()

        if not runs:
            return {
                "dossier_id": dossier_id,
                "monitor_id": str(monitor.id),
                "since": since_dt.isoformat(),
                "runs": 0,
                "summary": "No monitor runs in this period.",
            }

        total_papers = sum(r.papers_new for r in runs)
        total_claims = sum(r.claims_extracted for r in runs)
        total_conflicts = sum(r.conflicts_found for r in runs)
        all_alerts = []
        for r in runs:
            if r.summary and isinstance(r.summary, dict):
                all_alerts.extend(r.summary.get("alerts", []))

        return {
            "dossier_id": dossier_id,
            "monitor_id": str(monitor.id),
            "since": since_dt.isoformat(),
            "runs": len(runs),
            "total_new_papers": total_papers,
            "total_claims_extracted": total_claims,
            "total_conflicts_found": total_conflicts,
            "alerts": all_alerts[:15],
            "last_run": runs[0].started_at.isoformat() if runs else None,
        }
