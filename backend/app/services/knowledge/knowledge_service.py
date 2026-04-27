"""Personal knowledge service — annotations, glossary, flashcards, learning.

P3 WS-4: §24 (#213-224) from FeasibilityAnalysis.md

Provides:
- Reading interaction logging
- Annotation CRUD (highlights, notes, questions)
- Auto/manual glossary term management
- Knowledge card generation (LLM) + spaced repetition (SM-2)
"""

import json
from datetime import datetime, timedelta

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import Annotation, GlossaryTerm, KnowledgeCard, ReadingLog
from app.models.paper import Paper

logger = structlog.get_logger(__name__)


class ReadingLogService:
    """Track user reading interactions."""

    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id

    async def log_event(
        self,
        paper_id: str,
        event_type: str,
        duration_seconds: int | None = None,
        metadata: dict | None = None,
    ) -> dict:
        entry = ReadingLog(
            user_id=self.user_id,
            paper_id=paper_id,
            event_type=event_type,
            duration_seconds=duration_seconds,
            metadata_json=metadata,
        )
        self.db.add(entry)
        await self.db.flush()
        return {"id": str(entry.id), "event_type": event_type}

    async def get_reading_history(
        self, limit: int = 50, paper_id: str | None = None
    ) -> list[dict]:
        query = (
            select(ReadingLog)
            .where(ReadingLog.user_id == self.user_id)
            .order_by(ReadingLog.created_at.desc())
            .limit(limit)
        )
        if paper_id:
            query = query.where(ReadingLog.paper_id == paper_id)

        result = await self.db.execute(query)
        return [
            {
                "id": str(r.id),
                "paper_id": str(r.paper_id),
                "event_type": r.event_type,
                "duration_seconds": r.duration_seconds,
                "created_at": str(r.created_at),
            }
            for r in result.scalars().all()
        ]

    async def get_reading_stats(self) -> dict:
        """Get user's reading statistics."""
        total_events = await self.db.execute(
            select(func.count(ReadingLog.id)).where(ReadingLog.user_id == self.user_id)
        )
        total_time = await self.db.execute(
            select(func.sum(ReadingLog.duration_seconds)).where(
                ReadingLog.user_id == self.user_id,
                ReadingLog.duration_seconds.is_not(None),
            )
        )
        unique_papers = await self.db.execute(
            select(func.count(ReadingLog.paper_id.distinct())).where(
                ReadingLog.user_id == self.user_id
            )
        )
        return {
            "total_events": total_events.scalar() or 0,
            "total_reading_seconds": total_time.scalar() or 0,
            "unique_papers_read": unique_papers.scalar() or 0,
        }


class AnnotationService:
    """Manage user annotations (highlights, notes, questions)."""

    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id

    async def create(
        self,
        paper_id: str,
        annotation_type: str,
        text: str | None = None,
        note: str | None = None,
        color: str | None = None,
        page: int | None = None,
        position: dict | None = None,
    ) -> dict:
        ann = Annotation(
            user_id=self.user_id,
            paper_id=paper_id,
            annotation_type=annotation_type,
            text=text,
            note=note,
            color=color,
            page=page,
            position=position,
        )
        self.db.add(ann)
        await self.db.flush()
        return {
            "id": str(ann.id),
            "paper_id": paper_id,
            "annotation_type": annotation_type,
        }

    async def list_for_paper(self, paper_id: str) -> list[dict]:
        result = await self.db.execute(
            select(Annotation)
            .where(
                Annotation.user_id == self.user_id,
                Annotation.paper_id == paper_id,
            )
            .order_by(Annotation.page.asc().nullslast(), Annotation.created_at)
        )
        return [
            {
                "id": str(a.id),
                "type": a.annotation_type,
                "text": a.text,
                "note": a.note,
                "color": a.color,
                "page": a.page,
                "created_at": str(a.created_at),
            }
            for a in result.scalars().all()
        ]

    async def delete(self, annotation_id: str) -> bool:
        result = await self.db.execute(
            select(Annotation).where(
                Annotation.id == annotation_id,
                Annotation.user_id == self.user_id,
            )
        )
        ann = result.scalar_one_or_none()
        if not ann:
            return False
        await self.db.delete(ann)
        return True


class GlossaryService:
    """Manage personal research glossary."""

    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id

    async def add_term(
        self,
        term: str,
        definition: str | None = None,
        domain: str | None = None,
        paper_id: str | None = None,
    ) -> dict:
        entry = GlossaryTerm(
            user_id=self.user_id,
            term=term,
            definition=definition,
            domain=domain,
            source_paper_id=paper_id,
            is_auto_generated=False,
        )
        self.db.add(entry)
        await self.db.flush()
        return {"id": str(entry.id), "term": term}

    async def auto_extract_terms(self, paper_id: str) -> dict:
        """Use LLM to extract key technical terms from a paper."""
        result = await self.db.execute(
            select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
        )
        paper = result.scalar_one_or_none()
        if not paper:
            return {"error": "Paper not found"}

        from app.clients.llm_client import LLMClient

        llm = LLMClient()
        # Use full text if available for better extraction
        paper_text = paper.abstract or ""
        if paper.full_text_markdown:
            paper_text = paper.full_text_markdown[:8000]
        prompt = (
            f"Extract the 10-15 most important technical terms from this paper.\n\n"
            f"Title: {paper.title}\n"
            f"Content: {paper_text}\n\n"
            f"For each term provide a 1-2 sentence definition.\n"
            f'Return JSON: [{{"term": "...", "definition": "...", "domain": "..."}}]\n'
            f"Return ONLY the JSON array."
        )

        try:
            response = await llm.complete(prompt=prompt, temperature=0.2)
            terms_data = json.loads(response)
            await llm.close()
        except Exception as e:
            logger.error("term_extraction_failed", error=str(e))
            return {"error": str(e)}

        created = []
        for td in terms_data:
            entry = GlossaryTerm(
                user_id=self.user_id,
                term=td.get("term", ""),
                definition=td.get("definition"),
                domain=td.get("domain"),
                source_paper_id=paper_id,
                is_auto_generated=True,
            )
            self.db.add(entry)
            created.append(td.get("term", ""))

        return {"paper_id": paper_id, "terms_created": len(created), "terms": created}

    async def list_terms(
        self, domain: str | None = None, limit: int = 100
    ) -> list[dict]:
        query = (
            select(GlossaryTerm)
            .where(GlossaryTerm.user_id == self.user_id)
            .order_by(GlossaryTerm.term.asc())
            .limit(limit)
        )
        if domain:
            query = query.where(GlossaryTerm.domain == domain)

        result = await self.db.execute(query)
        return [
            {
                "id": str(g.id),
                "term": g.term,
                "definition": g.definition,
                "domain": g.domain,
                "is_auto_generated": g.is_auto_generated,
            }
            for g in result.scalars().all()
        ]

    async def search_terms(self, query: str) -> list[dict]:
        result = await self.db.execute(
            select(GlossaryTerm)
            .where(
                GlossaryTerm.user_id == self.user_id,
                GlossaryTerm.term.ilike(f"%{query}%"),
            )
            .limit(20)
        )
        return [
            {"id": str(g.id), "term": g.term, "definition": g.definition}
            for g in result.scalars().all()
        ]


class KnowledgeCardService:
    """Generate and manage flashcards with spaced repetition."""

    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id

    async def generate_cards(self, paper_id: str) -> dict:
        """Generate flashcards from a paper using LLM."""
        result = await self.db.execute(
            select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
        )
        paper = result.scalar_one_or_none()
        if not paper:
            return {"error": "Paper not found"}

        from app.clients.llm_client import LLMClient

        llm = LLMClient()
        # Use full text if available for better card generation
        paper_text = paper.abstract or ""
        if paper.full_text_markdown:
            paper_text = paper.full_text_markdown[:8000]
        prompt = (
            f"Generate 8-12 flashcards from this paper for study.\n\n"
            f"Title: {paper.title}\n"
            f"Content: {paper_text}\n\n"
            f"Create cards that cover:\n"
            f"- Key concepts and definitions\n"
            f"- Main methods and how they work\n"
            f"- Principal findings and numbers\n"
            f"- Novel contributions\n\n"
            f"Return JSON: [{{"
            f'"question": "...", "answer": "...", '
            f'"card_type": "concept|formula|method|result", '
            f'"difficulty": "easy|medium|hard"'
            f"}}]\n"
            f"Return ONLY the JSON array."
        )

        try:
            response = await llm.complete(prompt=prompt, temperature=0.3)
            cards_data = json.loads(response)
            await llm.close()
        except Exception as e:
            logger.error("card_generation_failed", error=str(e))
            return {"error": str(e)}

        created = []
        for cd in cards_data:
            card = KnowledgeCard(
                user_id=self.user_id,
                paper_id=paper_id,
                question=cd.get("question", ""),
                answer=cd.get("answer", ""),
                card_type=cd.get("card_type", "concept"),
                difficulty=cd.get("difficulty"),
                next_review_at=datetime.utcnow(),
            )
            self.db.add(card)
            await self.db.flush()
            created.append(
                {
                    "id": str(card.id),
                    "question": card.question,
                    "card_type": card.card_type,
                }
            )

        return {"paper_id": paper_id, "cards_created": len(created), "cards": created}

    async def get_due_cards(self, limit: int = 20) -> list[dict]:
        """Get cards due for review (spaced repetition)."""
        result = await self.db.execute(
            select(KnowledgeCard)
            .where(
                KnowledgeCard.user_id == self.user_id,
                KnowledgeCard.next_review_at <= func.now(),
            )
            .order_by(KnowledgeCard.next_review_at)
            .limit(limit)
        )
        return [
            {
                "id": str(c.id),
                "question": c.question,
                "answer": c.answer,
                "card_type": c.card_type,
                "difficulty": c.difficulty,
                "review_count": c.review_count,
            }
            for c in result.scalars().all()
        ]

    async def review_card(self, card_id: str, quality: int) -> dict:
        """
        Record a review using SM-2 spaced repetition algorithm.

        quality: 0-5 (0=complete blackout, 5=perfect recall)
        """
        result = await self.db.execute(
            select(KnowledgeCard).where(
                KnowledgeCard.id == card_id,
                KnowledgeCard.user_id == self.user_id,
            )
        )
        card = result.scalar_one_or_none()
        if not card:
            return {"error": "Card not found"}

        # SM-2 algorithm
        # review_count = total reviews; repetition = successful streak
        quality = max(0, min(5, quality))
        card.review_count += 1

        if quality >= 3:
            # Successful recall: advance repetition stage
            if card.repetition == 0:
                card.interval_days = 1
            elif card.repetition == 1:
                card.interval_days = 6
            else:
                card.interval_days = round(card.interval_days * card.ease_factor)
            card.repetition += 1
        else:
            # Failed recall: reset streak and interval
            card.repetition = 0
            card.interval_days = 1

        # Update ease factor (always, regardless of pass/fail)
        card.ease_factor = max(
            1.3,
            card.ease_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02),
        )
        next_review = datetime.utcnow() + timedelta(days=card.interval_days)
        card.next_review_at = next_review

        return {
            "id": str(card.id),
            "next_review_at": next_review.isoformat(),
            "interval_days": card.interval_days,
            "repetition": card.repetition,
            "ease_factor": round(card.ease_factor, 2),
        }

    async def list_cards(
        self, paper_id: str | None = None, limit: int = 50
    ) -> list[dict]:
        query = (
            select(KnowledgeCard)
            .where(KnowledgeCard.user_id == self.user_id)
            .order_by(KnowledgeCard.created_at.desc())
            .limit(limit)
        )
        if paper_id:
            query = query.where(KnowledgeCard.paper_id == paper_id)

        result = await self.db.execute(query)
        return [
            {
                "id": str(c.id),
                "question": c.question,
                "answer": c.answer,
                "card_type": c.card_type,
                "review_count": c.review_count,
                "next_review_at": str(c.next_review_at) if c.next_review_at else None,
            }
            for c in result.scalars().all()
        ]
