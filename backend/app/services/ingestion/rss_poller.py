"""RSS feed poller — discovers new papers from subscribed RSS feeds."""

from datetime import UTC, datetime

import feedparser
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feed import RSSFeed
from app.utils.doi import extract_arxiv_id, normalize_doi

logger = structlog.get_logger(__name__)


class DiscoveredPaper:
    """A paper discovered from an RSS feed, before deduplication/enrichment."""

    def __init__(
        self,
        title: str,
        doi: str | None = None,
        arxiv_id: str | None = None,
        link: str | None = None,
        abstract: str | None = None,
        published: str | None = None,
        authors: list[str] | None = None,
        source_feed_id: str | None = None,
    ):
        self.title = title
        self.doi = normalize_doi(doi) if doi else None
        self.arxiv_id = arxiv_id
        self.link = link
        self.abstract = abstract
        self.published = published
        self.authors = authors or []
        self.source_feed_id = source_feed_id


class RSSPollerService:
    """
    Poll RSS feeds, discover new papers, and return structured results.

    Implements ETag/Last-Modified conditional requests to avoid
    re-processing unchanged feeds.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_feeds(self) -> list[RSSFeed]:
        """Get all active RSS feed subscriptions."""
        result = await self.db.execute(
            select(RSSFeed).where(RSSFeed.is_active.is_(True))
        )
        return list(result.scalars().all())

    async def poll_feed(self, feed: RSSFeed) -> list[DiscoveredPaper]:
        """
        Poll a single RSS feed and return newly discovered papers.

        Uses ETag/Last-Modified for conditional requests.
        Updates feed's polling state in database.
        """
        log = logger.bind(feed_name=feed.name, feed_url=feed.url)
        log.info("polling_feed_start")

        try:
            # Parse with conditional headers
            parsed = feedparser.parse(
                feed.url,
                etag=feed.etag or "",
                modified=feed.last_modified or "",
            )

            # Check for HTTP status
            status = parsed.get("status", 200)
            if status == 304:
                log.info("feed_not_modified")
                feed.last_polled_at = datetime.now(UTC)
                return []

            if status >= 400:
                log.warning("feed_http_error", status=status)
                feed.poll_error_count += 1
                feed.last_error = f"HTTP {status}"
                feed.last_polled_at = datetime.now(UTC)
                return []

            # Update conditional request headers
            if hasattr(parsed, "etag"):
                feed.etag = parsed.etag
            if hasattr(parsed, "modified"):
                feed.last_modified = parsed.modified

            # Process entries
            papers = []
            for entry in parsed.entries:
                paper = self._parse_entry(entry, feed)
                if paper:
                    papers.append(paper)

            # Update feed stats
            feed.last_polled_at = datetime.now(UTC)
            feed.last_item_count = len(parsed.entries)
            feed.total_items_discovered += len(papers)
            feed.poll_error_count = 0
            feed.last_error = None

            log.info(
                "polling_feed_complete",
                new_papers=len(papers),
                total_entries=len(parsed.entries),
            )
            return papers

        except Exception as e:
            log.error("polling_feed_error", error=str(e))
            feed.poll_error_count += 1
            feed.last_error = str(e)[:500]
            feed.last_polled_at = datetime.now(UTC)
            return []

    def _parse_entry(self, entry: dict, feed: RSSFeed) -> DiscoveredPaper | None:
        """Parse a single RSS entry into a DiscoveredPaper."""
        title = entry.get("title", "").strip()
        if not title:
            return None

        link = entry.get("link", "")

        # Extract DOI from various sources
        doi = None
        # Check dc:identifier or prism:doi
        for key in ("dc_identifier", "prism_doi", "doi"):
            if key in entry:
                doi = normalize_doi(entry[key])
                if doi:
                    break

        # Try extracting DOI from link URL
        if not doi and link:
            doi = normalize_doi(link)

        # Extract arXiv ID
        arxiv_id = None
        if "arxiv" in link.lower() or "arxiv" in feed.url.lower():
            arxiv_id = extract_arxiv_id(link)

        # Abstract / summary
        abstract = entry.get("summary", entry.get("description", ""))
        if abstract:
            # Strip HTML tags from feed summaries
            import re

            abstract = re.sub(r"<[^>]+>", "", abstract).strip()

        # Authors
        authors = []
        if "authors" in entry:
            authors = [
                a.get("name", "") for a in entry.get("authors", []) if a.get("name")
            ]
        elif "author" in entry:
            authors = [entry["author"]]

        # Published date
        published = entry.get("published", entry.get("updated"))

        return DiscoveredPaper(
            title=title,
            doi=doi,
            arxiv_id=arxiv_id,
            link=link,
            abstract=abstract,
            published=published,
            authors=authors,
            source_feed_id=str(feed.id),
        )

    async def poll_all_active_feeds(self) -> dict:
        """Poll all active feeds. Returns summary of results."""
        feeds = await self.get_active_feeds()
        total_new = 0
        errors = 0
        all_papers: list[DiscoveredPaper] = []

        for feed in feeds:
            try:
                papers = await self.poll_feed(feed)
                all_papers.extend(papers)
                total_new += len(papers)
            except Exception:
                errors += 1

        logger.info(
            "poll_all_complete",
            feeds_polled=len(feeds),
            new_papers=total_new,
            errors=errors,
        )

        return {
            "feeds_polled": len(feeds),
            "new_papers_discovered": total_new,
            "errors": errors,
            "papers": all_papers,
        }
