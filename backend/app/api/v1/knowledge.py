"""Personal knowledge API — annotations, glossary, flashcards, reading log.

P3 WS-4: §24 (#213-224)
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user_id

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


# ─── Pydantic models ─────────────────────────────────────────────

class LogEventRequest(BaseModel):
    paper_id: str
    event_type: str
    duration_seconds: int | None = None
    metadata: dict | None = None


class AnnotationCreateRequest(BaseModel):
    paper_id: str
    annotation_type: str = "note"
    text: str | None = None
    note: str | None = None
    color: str | None = None
    page: int | None = None
    position: dict | None = None


class AddTermRequest(BaseModel):
    term: str
    definition: str | None = None
    domain: str | None = None
    paper_id: str | None = None


class ReviewCardRequest(BaseModel):
    quality: int = Field(..., ge=0, le=5)


# ─── Reading Log ─────────────────────────────────────────────────

@router.post("/reading-log")
async def log_reading_event(
    req: LogEventRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Log a reading interaction (open, read, annotate, etc.)."""
    from app.services.knowledge.knowledge_service import ReadingLogService

    svc = ReadingLogService(db, user_id)
    result = await svc.log_event(req.paper_id, req.event_type, req.duration_seconds, req.metadata)
    await db.commit()
    return result


@router.get("/reading-log")
async def get_reading_history(
    limit: int = 50,
    paper_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get reading history."""
    from app.services.knowledge.knowledge_service import ReadingLogService

    svc = ReadingLogService(db, user_id)
    return {"history": await svc.get_reading_history(limit, paper_id)}


@router.get("/reading-stats")
async def get_reading_stats(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get reading statistics."""
    from app.services.knowledge.knowledge_service import ReadingLogService

    svc = ReadingLogService(db, user_id)
    return await svc.get_reading_stats()


# ─── Annotations ─────────────────────────────────────────────────

@router.post("/annotations")
async def create_annotation(
    req: AnnotationCreateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Create a highlight, note, or question on a paper."""
    from app.services.knowledge.knowledge_service import AnnotationService

    svc = AnnotationService(db, user_id)
    result = await svc.create(
        req.paper_id, req.annotation_type, req.text, req.note, req.color, req.page, req.position
    )
    await db.commit()
    return result


@router.get("/annotations/papers/{paper_id}")
async def list_annotations(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List all annotations for a paper."""
    from app.services.knowledge.knowledge_service import AnnotationService

    svc = AnnotationService(db, user_id)
    return {"annotations": await svc.list_for_paper(paper_id)}


@router.delete("/annotations/{annotation_id}")
async def delete_annotation(
    annotation_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Delete an annotation."""
    from app.services.knowledge.knowledge_service import AnnotationService

    svc = AnnotationService(db, user_id)
    deleted = await svc.delete(annotation_id)
    if not deleted:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Annotation not found")
    await db.commit()
    return {"deleted": True}


# ─── Glossary ────────────────────────────────────────────────────

@router.post("/glossary")
async def add_glossary_term(
    req: AddTermRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Add a term to your personal glossary."""
    from app.services.knowledge.knowledge_service import GlossaryService

    svc = GlossaryService(db, user_id)
    result = await svc.add_term(req.term, req.definition, req.domain, req.paper_id)
    await db.commit()
    return result


@router.post("/glossary/auto-extract/{paper_id}")
async def auto_extract_terms(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Auto-extract technical terms from a paper using LLM."""
    from app.services.knowledge.knowledge_service import GlossaryService

    svc = GlossaryService(db, user_id)
    result = await svc.auto_extract_terms(paper_id)
    await db.commit()
    return result


@router.get("/glossary")
async def list_glossary(
    domain: str | None = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List glossary terms."""
    from app.services.knowledge.knowledge_service import GlossaryService

    svc = GlossaryService(db, user_id)
    return {"terms": await svc.list_terms(domain, limit)}


@router.get("/glossary/search")
async def search_glossary(
    q: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Search glossary terms."""
    from app.services.knowledge.knowledge_service import GlossaryService

    svc = GlossaryService(db, user_id)
    return {"terms": await svc.search_terms(q)}


# ─── Knowledge Cards ─────────────────────────────────────────────

@router.post("/cards/generate/{paper_id}")
async def generate_cards(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Generate flashcards from a paper using LLM."""
    from app.services.knowledge.knowledge_service import KnowledgeCardService

    svc = KnowledgeCardService(db, user_id)
    result = await svc.generate_cards(paper_id)
    await db.commit()
    return result


@router.get("/cards/due")
async def get_due_cards(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get flashcards due for review (spaced repetition)."""
    from app.services.knowledge.knowledge_service import KnowledgeCardService

    svc = KnowledgeCardService(db, user_id)
    return {"cards": await svc.get_due_cards(limit)}


@router.post("/cards/{card_id}/review")
async def review_card(
    card_id: str,
    req: ReviewCardRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Record a flashcard review (SM-2 spaced repetition)."""
    from app.services.knowledge.knowledge_service import KnowledgeCardService

    svc = KnowledgeCardService(db, user_id)
    result = await svc.review_card(card_id, req.quality)
    await db.commit()
    return result


@router.get("/cards")
async def list_cards(
    paper_id: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List flashcards."""
    from app.services.knowledge.knowledge_service import KnowledgeCardService

    svc = KnowledgeCardService(db, user_id)
    return {"cards": await svc.list_cards(paper_id, limit)}
