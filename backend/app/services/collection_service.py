"""Collection and tag service — CRUD, smart collections, paper management.

All operations accept a user_id parameter (defaults to DEFAULT_USER_ID).
Collection/tag queries filter by user_id to ensure per-user scoping.
Reading status uses the UserReadingStatus table, not Paper.reading_status.
"""

from datetime import UTC, datetime

import structlog
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.collection import (
    CollectionChatMessage,
    CollectionChatThread,
    CollectionFeedSubscription,
    DEFAULT_USER_ID,
    Collection,
    CollectionPaper,
    PaperTag,
    Tag,
    UserReadingStatus,
)
from app.models.feed import RSSFeed
from app.models.paper import Paper

logger = structlog.get_logger(__name__)


class CollectionService:
    """Business logic for collections and tags."""

    def __init__(self, db: AsyncSession, user_id: str = DEFAULT_USER_ID):
        self.db = db
        self.user_id = user_id

    # ─── Collection CRUD ─────────────────────────────────────────

    async def create_collection(
        self,
        name: str,
        description: str | None = None,
        kind: str = "workspace",
        color: str | None = None,
        icon: str | None = None,
        parent_collection_id: str | None = None,
        is_smart: bool = False,
        smart_filter: dict | None = None,
    ) -> Collection:
        """Create a new collection scoped to this user."""
        collection = Collection(
            user_id=self.user_id,
            name=name,
            description=description,
            kind=kind,
            color=color,
            icon=icon,
            parent_collection_id=parent_collection_id,
            is_smart=is_smart,
            smart_filter=smart_filter,
        )
        self.db.add(collection)
        await self.db.flush()
        return collection

    async def list_collections(
        self,
        include_deleted: bool = False,
        *,
        kind: str | None = None,
        parent_collection_id: str | None = None,
    ) -> list[Collection]:
        """List collections for this user."""
        query = select(Collection).where(Collection.user_id == self.user_id)
        if not include_deleted:
            query = query.where(Collection.deleted_at.is_(None))
        if kind is not None:
            query = query.where(Collection.kind == kind)
        if parent_collection_id is not None:
            query = query.where(Collection.parent_collection_id == parent_collection_id)
        query = query.order_by(Collection.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_collection(self, collection_id: str) -> Collection | None:
        """Get a collection (user-scoped) with its papers."""
        result = await self.db.execute(
            select(Collection)
            .where(
                Collection.id == collection_id,
                Collection.user_id == self.user_id,
                Collection.deleted_at.is_(None),
            )
            .options(selectinload(Collection.papers))
        )
        return result.scalar_one_or_none()

    async def update_collection(
        self, collection_id: str, **kwargs
    ) -> Collection | None:
        """Update collection fields."""
        collection = await self.get_collection(collection_id)
        if not collection:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(collection, key):
                setattr(collection, key, value)
        return collection

    async def delete_collection(self, collection_id: str) -> bool:
        """Soft-delete a collection (user-scoped)."""
        result = await self.db.execute(
            update(Collection)
            .where(
                Collection.id == collection_id,
                Collection.user_id == self.user_id,
            )
            .values(deleted_at=func.now())
        )
        return result.rowcount > 0

    async def list_child_collections(
        self,
        parent_collection_id: str,
        *,
        kind: str | None = None,
    ) -> list[Collection]:
        """List child collections under a parent container."""
        return await self.list_collections(
            kind=kind,
            parent_collection_id=parent_collection_id,
        )

    async def attach_feeds(self, collection_id: str, feed_ids: list[str]) -> int:
        """Attach RSS feeds to a subscription collection."""
        collection = await self.get_collection(collection_id)
        if not collection or collection.kind != "subscription_collection":
            return 0

        existing = await self.db.execute(
            select(CollectionFeedSubscription.feed_id).where(
                CollectionFeedSubscription.collection_id == collection_id,
                CollectionFeedSubscription.feed_id.in_(feed_ids),
            )
        )
        existing_ids = {str(row[0]) for row in existing.all()}
        added = 0
        for feed_id in feed_ids:
            if str(feed_id) in existing_ids:
                continue
            self.db.add(
                CollectionFeedSubscription(
                    collection_id=collection_id,
                    feed_id=feed_id,
                )
            )
            added += 1
        await self.db.flush()
        return added

    async def list_feed_subscriptions(self, collection_id: str) -> list[dict]:
        """Return attached feeds for a subscription collection."""
        result = await self.db.execute(
            select(
                CollectionFeedSubscription.id,
                CollectionFeedSubscription.feed_id,
                CollectionFeedSubscription.collection_id,
                CollectionFeedSubscription.created_at,
                RSSFeed.name.label("feed_name"),
                RSSFeed.publisher,
                RSSFeed.category,
            )
            .join(RSSFeed, RSSFeed.id == CollectionFeedSubscription.feed_id)
            .where(CollectionFeedSubscription.collection_id == collection_id)
            .order_by(RSSFeed.name)
        )
        return [dict(row._mapping) for row in result.all()]

    async def detach_feed(self, collection_id: str, feed_id: str) -> bool:
        """Detach an RSS feed from a subscription collection."""
        result = await self.db.execute(
            delete(CollectionFeedSubscription).where(
                CollectionFeedSubscription.collection_id == collection_id,
                CollectionFeedSubscription.feed_id == feed_id,
            )
        )
        return result.rowcount > 0

    # ─── Paper Management ────────────────────────────────────────

    async def add_papers(
        self,
        collection_id: str,
        paper_ids: list[str],
        note: str | None = None,
    ) -> int:
        """Add papers to a collection. Returns number added (skips existing)."""
        # Check which papers already in collection
        existing = await self.db.execute(
            select(CollectionPaper.paper_id).where(
                CollectionPaper.collection_id == collection_id,
                CollectionPaper.paper_id.in_(paper_ids),
            )
        )
        existing_ids = {str(row[0]) for row in existing.all()}

        # Get max position
        max_pos_result = await self.db.execute(
            select(func.coalesce(func.max(CollectionPaper.position), 0)).where(
                CollectionPaper.collection_id == collection_id
            )
        )
        max_pos = max_pos_result.scalar()

        added = 0
        for pid in paper_ids:
            if str(pid) not in existing_ids:
                max_pos += 1
                self.db.add(
                    CollectionPaper(
                        collection_id=collection_id,
                        paper_id=pid,
                        position=max_pos,
                        note=note,
                    )
                )
                added += 1

        # Update denormalized count
        if added > 0:
            await self._refresh_paper_count(collection_id)

        return added

    async def remove_paper(self, collection_id: str, paper_id: str) -> bool:
        """Remove a paper from a collection."""
        result = await self.db.execute(
            delete(CollectionPaper).where(
                CollectionPaper.collection_id == collection_id,
                CollectionPaper.paper_id == paper_id,
            )
        )
        if result.rowcount > 0:
            await self._refresh_paper_count(collection_id)
            return True
        return False

    async def reorder_papers(self, collection_id: str, paper_ids: list[str]) -> None:
        """Set paper ordering in a collection."""
        for position, paper_id in enumerate(paper_ids, start=1):
            await self.db.execute(
                update(CollectionPaper)
                .where(
                    CollectionPaper.collection_id == collection_id,
                    CollectionPaper.paper_id == paper_id,
                )
                .values(position=position)
            )

    async def get_collection_papers(
        self, collection_id: str, limit: int = 50, offset: int = 0
    ) -> list[dict]:
        """Get papers in a collection with inline details + user reading status."""
        result = await self.db.execute(
            select(
                CollectionPaper.paper_id,
                CollectionPaper.position,
                CollectionPaper.note,
                CollectionPaper.added_at,
                Paper.title,
                Paper.doi,
                Paper.arxiv_id,
                Paper.published_at,
                UserReadingStatus.status.label("reading_status"),
            )
            .join(Paper, CollectionPaper.paper_id == Paper.id)
            .outerjoin(
                UserReadingStatus,
                (UserReadingStatus.paper_id == Paper.id)
                & (UserReadingStatus.user_id == self.user_id),
            )
            .where(CollectionPaper.collection_id == collection_id)
            .order_by(CollectionPaper.position)
            .limit(limit)
            .offset(offset)
        )
        rows = []
        for row in result.all():
            d = dict(row._mapping)
            # Default to "unread" if no UserReadingStatus row
            if d.get("reading_status") is None:
                d["reading_status"] = "unread"
            rows.append(d)
        return rows

    async def _refresh_paper_count(self, collection_id: str) -> None:
        """Refresh denormalized paper_count on collection."""
        count_result = await self.db.execute(
            select(func.count()).where(CollectionPaper.collection_id == collection_id)
        )
        count = count_result.scalar()
        await self.db.execute(
            update(Collection)
            .where(Collection.id == collection_id)
            .values(paper_count=count)
        )

    # ─── Smart Collections ───────────────────────────────────────

    async def evaluate_smart_collection(
        self, collection_id: str, limit: int = 100
    ) -> list[Paper]:
        """
        Evaluate a smart collection's filter and return matching papers.

        Supported filter keys:
        - year_gte, year_lte: published year range
        - has_full_text: bool
        - keywords: list[str] (any match in paper.keywords)
        - reading_status: str (joins UserReadingStatus for this user)
        - paper_type: str
        """
        collection = await self.get_collection(collection_id)
        if not collection or not collection.is_smart or not collection.smart_filter:
            return []

        filt = collection.smart_filter
        query = select(Paper).where(Paper.deleted_at.is_(None))

        if "year_gte" in filt and filt["year_gte"]:
            from datetime import date

            query = query.where(Paper.published_at >= date(filt["year_gte"], 1, 1))
        if "year_lte" in filt and filt["year_lte"]:
            from datetime import date

            query = query.where(Paper.published_at <= date(filt["year_lte"], 12, 31))
        if "has_full_text" in filt:
            query = query.where(Paper.has_full_text == filt["has_full_text"])
        if "paper_type" in filt:
            query = query.where(Paper.paper_type == filt["paper_type"])

        # Reading status: join UserReadingStatus for this user
        # Special case: "unread" includes papers with NO status row (LEFT JOIN + IS NULL)
        if "reading_status" in filt:
            target_status = filt["reading_status"]
            if target_status == "unread":
                # LEFT JOIN: papers with no row OR status = 'unread'
                from sqlalchemy import or_

                query = query.outerjoin(
                    UserReadingStatus,
                    (UserReadingStatus.paper_id == Paper.id)
                    & (UserReadingStatus.user_id == self.user_id),
                ).where(
                    or_(
                        UserReadingStatus.status.is_(None),
                        UserReadingStatus.status == "unread",
                    )
                )
            else:
                # INNER JOIN: require explicit status row
                query = query.join(
                    UserReadingStatus,
                    (UserReadingStatus.paper_id == Paper.id)
                    & (UserReadingStatus.user_id == self.user_id),
                ).where(UserReadingStatus.status == target_status)

        # Keywords: filter for papers that have ANY matching keyword (OR logic)
        if "keywords" in filt and filt["keywords"]:
            from sqlalchemy import or_
            from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB

            keyword_conditions = [
                Paper.keywords.cast(PG_JSONB).contains([kw]) for kw in filt["keywords"]
            ]
            query = query.where(or_(*keyword_conditions))

        # oa_status
        if filt.get("oa_status"):
            query = query.where(Paper.oa_status == filt["oa_status"])

        # min_citations
        if filt.get("min_citations"):
            query = query.where(Paper.citation_count >= filt["min_citations"])

        # venue: substring in raw_metadata->>'crossref_venue'
        if filt.get("venue"):
            from sqlalchemy import cast as sa_cast, String

            venue_expr = Paper.raw_metadata["crossref_venue"].as_string()
            query = query.where(venue_expr.ilike(f"%{filt['venue']}%"))

        # text_search: substring in title or abstract
        if filt.get("text_search"):
            from sqlalchemy import or_

            term = f"%{filt['text_search']}%"
            query = query.where(
                or_(
                    Paper.title.ilike(term),
                    Paper.abstract.ilike(term),
                )
            )

        query = query.order_by(Paper.published_at.desc().nullslast()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ─── Smart Collection Auto-Add ────────────────────────────────

    async def evaluate_smart_collections(self, paper: Paper) -> list[str]:
        """
        Match a newly indexed paper against ALL smart collections for this user
        and auto-add it to any that match.

        Filter keys (aligned with evaluate_smart_collection / smart_filter schema):
          year_gte / year_lte : int  — published year range
          has_full_text       : bool
          paper_type          : str  — exact match
          reading_status      : str  — requires UserReadingStatus row
          keywords            : list[str] — any keyword in paper.keywords array
          venue               : str  — substring match on raw_metadata crossref_venue
          oa_status           : str  — exact match
          min_citations       : int
          text_search         : str  — substring in title or abstract

        Returns list of collection IDs the paper was auto-added to.
        """
        smart_result = await self.db.execute(
            select(Collection).where(
                Collection.user_id == self.user_id,
                Collection.is_smart.is_(True),
                Collection.deleted_at.is_(None),
            )
        )
        added_to: list[str] = []
        for col in smart_result.scalars().all():
            filt = col.smart_filter or {}
            if not filt:
                continue
            if not self._paper_matches_smart_filter(paper, filt):
                continue
            count = await self.add_papers(str(col.id), [str(paper.id)])
            if count > 0:
                added_to.append(str(col.id))
                logger.info(
                    "smart_collection_auto_add",
                    collection=col.name,
                    paper_id=str(paper.id),
                )
        return added_to

    @staticmethod
    def _paper_matches_smart_filter(paper: Paper, filt: dict) -> bool:
        """Evaluate whether a paper matches a smart_filter dict (in-process check)."""
        from datetime import date

        # year_gte / year_lte
        if paper.published_at:
            year = paper.published_at.year
            if filt.get("year_gte") and year < filt["year_gte"]:
                return False
            if filt.get("year_lte") and year > filt["year_lte"]:
                return False
        elif filt.get("year_gte") or filt.get("year_lte"):
            return False

        # has_full_text
        if "has_full_text" in filt:
            if bool(paper.has_full_text) != bool(filt["has_full_text"]):
                return False

        # paper_type
        if filt.get("paper_type") and paper.paper_type != filt["paper_type"]:
            return False

        # oa_status
        if filt.get("oa_status") and paper.oa_status != filt["oa_status"]:
            return False

        # min_citations
        if filt.get("min_citations"):
            if (paper.citation_count or 0) < filt["min_citations"]:
                return False

        # keywords: any keyword in paper.keywords array
        if filt.get("keywords"):
            paper_kws = [k.lower() for k in (paper.keywords or [])]
            if not any(kw.lower() in paper_kws for kw in filt["keywords"]):
                return False

        # venue: substring in raw_metadata crossref_venue
        if filt.get("venue"):
            raw = paper.raw_metadata or {}
            paper_venue = (raw.get("crossref_venue") or "").lower()
            if filt["venue"].lower() not in paper_venue:
                return False

        # text_search: substring in title or abstract
        if filt.get("text_search"):
            haystack = f"{paper.title or ''} {paper.abstract or ''}".lower()
            if filt["text_search"].lower() not in haystack:
                return False

        return True


class CollectionChatService:
    """Collection-scoped chat thread and message persistence."""

    def __init__(self, db: AsyncSession, user_id: str = DEFAULT_USER_ID):
        self.db = db
        self.user_id = user_id

    async def list_threads(self, collection_id: str) -> list[CollectionChatThread]:
        result = await self.db.execute(
            select(CollectionChatThread)
            .where(
                CollectionChatThread.collection_id == collection_id,
                CollectionChatThread.user_id == self.user_id,
                CollectionChatThread.deleted_at.is_(None),
            )
            .order_by(
                CollectionChatThread.updated_at.desc().nullslast(),
                CollectionChatThread.created_at.desc(),
            )
        )
        return list(result.scalars().all())

    async def create_thread(
        self,
        collection_id: str,
        title: str | None = None,
    ) -> CollectionChatThread:
        thread = CollectionChatThread(
            collection_id=collection_id,
            user_id=self.user_id,
            title=title,
        )
        self.db.add(thread)
        await self.db.flush()
        return thread

    async def get_thread(
        self,
        collection_id: str,
        thread_id: str,
    ) -> CollectionChatThread | None:
        result = await self.db.execute(
            select(CollectionChatThread)
            .where(
                CollectionChatThread.id == thread_id,
                CollectionChatThread.collection_id == collection_id,
                CollectionChatThread.user_id == self.user_id,
                CollectionChatThread.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_messages(
        self,
        collection_id: str,
        thread_id: str,
    ) -> list[CollectionChatMessage]:
        thread = await self.get_thread(collection_id, thread_id)
        if thread is None:
            return []
        result = await self.db.execute(
            select(CollectionChatMessage)
            .where(
                CollectionChatMessage.thread_id == thread_id,
                CollectionChatMessage.deleted_at.is_(None),
            )
            .order_by(CollectionChatMessage.created_at)
        )
        return list(result.scalars().all())

    async def create_message(
        self,
        thread_id: str,
        role: str,
        content: str,
        *,
        sources: dict | None = None,
        metadata_json: dict | None = None,
    ) -> CollectionChatMessage:
        message = CollectionChatMessage(
            thread_id=thread_id,
            user_id=self.user_id,
            role=role,
            content=content,
            sources=sources,
            metadata_json=metadata_json,
        )
        self.db.add(message)
        await self.db.flush()

        result = await self.db.execute(
            select(CollectionChatThread).where(CollectionChatThread.id == thread_id)
        )
        thread = result.scalar_one_or_none()
        if thread is not None:
            if not thread.title and role == "user":
                thread.title = content.strip()[:80]
            thread.updated_at = datetime.now(UTC)
        return message


class ReadingStatusService:
    """Per-user, per-paper reading status operations."""

    def __init__(self, db: AsyncSession, user_id: str = DEFAULT_USER_ID):
        self.db = db
        self.user_id = user_id

    async def get_status(self, paper_id: str) -> str:
        """Get reading status for a paper (defaults to 'unread')."""
        result = await self.db.execute(
            select(UserReadingStatus.status).where(
                UserReadingStatus.user_id == self.user_id,
                UserReadingStatus.paper_id == paper_id,
            )
        )
        row = result.scalar_one_or_none()
        return row if row else "unread"

    async def set_status(self, paper_id: str, status: str) -> str:
        """Set reading status for a paper (upsert)."""
        existing = await self.db.execute(
            select(UserReadingStatus).where(
                UserReadingStatus.user_id == self.user_id,
                UserReadingStatus.paper_id == paper_id,
            )
        )
        row = existing.scalar_one_or_none()
        if row:
            row.status = status
        else:
            self.db.add(
                UserReadingStatus(
                    user_id=self.user_id,
                    paper_id=paper_id,
                    status=status,
                )
            )
        return status


class TagService:
    """Business logic for tags (user-scoped)."""

    def __init__(self, db: AsyncSession, user_id: str = DEFAULT_USER_ID):
        self.db = db
        self.user_id = user_id

    async def create_tag(
        self,
        name: str,
        color: str | None = None,
        description: str | None = None,
    ) -> Tag:
        """Create a new tag scoped to this user."""
        tag = Tag(user_id=self.user_id, name=name, color=color, description=description)
        self.db.add(tag)
        await self.db.flush()
        return tag

    async def list_tags(self) -> list[dict]:
        """List tags for this user with paper counts."""
        result = await self.db.execute(
            select(
                Tag.id,
                Tag.name,
                Tag.color,
                Tag.description,
                func.count(PaperTag.id).label("paper_count"),
            )
            .where(Tag.user_id == self.user_id)
            .outerjoin(PaperTag, Tag.id == PaperTag.tag_id)
            .group_by(Tag.id)
            .order_by(Tag.name)
        )
        return [dict(row._mapping) for row in result.all()]

    async def get_tag(self, tag_id: str) -> Tag | None:
        result = await self.db.execute(
            select(Tag).where(Tag.id == tag_id, Tag.user_id == self.user_id)
        )
        return result.scalar_one_or_none()

    async def update_tag(self, tag_id: str, **kwargs) -> Tag | None:
        tag = await self.get_tag(tag_id)
        if not tag:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(tag, key):
                setattr(tag, key, value)
        return tag

    async def delete_tag(self, tag_id: str) -> bool:
        result = await self.db.execute(
            delete(Tag).where(Tag.id == tag_id, Tag.user_id == self.user_id)
        )
        return result.rowcount > 0

    async def add_tag_to_paper(self, paper_id: str, tag_id: str) -> bool:
        """Add a tag to a paper. Returns False if already exists."""
        existing = await self.db.execute(
            select(PaperTag.id).where(
                PaperTag.paper_id == paper_id,
                PaperTag.tag_id == tag_id,
            )
        )
        if existing.scalar_one_or_none():
            return False
        self.db.add(PaperTag(paper_id=paper_id, tag_id=tag_id))
        return True

    async def remove_tag_from_paper(self, paper_id: str, tag_id: str) -> bool:
        result = await self.db.execute(
            delete(PaperTag).where(
                PaperTag.paper_id == paper_id,
                PaperTag.tag_id == tag_id,
            )
        )
        return result.rowcount > 0

    async def get_paper_tags(self, paper_id: str) -> list[Tag]:
        result = await self.db.execute(
            select(Tag)
            .join(PaperTag, Tag.id == PaperTag.tag_id)
            .where(
                PaperTag.paper_id == paper_id,
                Tag.user_id == self.user_id,
            )
            .order_by(Tag.name)
        )
        return list(result.scalars().all())
