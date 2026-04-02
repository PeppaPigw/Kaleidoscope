"""Writing Support API — persisted documents plus AI writing utilities.

P2 WS-3: §22 (#189-200) from FeasibilityAnalysis.md
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db
from app.schemas.writing import (
    WritingDocumentListResponse,
    WritingDocumentResponse,
    WritingDocumentUpdateRequest,
    WritingImageUploadResponse,
)
from app.services.writing.document_service import WritingDocumentService
from app.services.writing.writing_service import WritingService

router = APIRouter(prefix="/writing", tags=["writing"])

MAX_WRITING_IMAGE_BYTES = 10 * 1024 * 1024


def _raise_writing_error(result: dict) -> None:
    error = result.get("error")
    if not error:
        return
    detail = str(error)
    if "not found" in detail.lower() or detail.lower() == "no papers found":
        raise HTTPException(status_code=404, detail=detail)
    raise HTTPException(
        status_code=502,
        detail=f"Writing service error: {detail[:200]}",
    )


# ─── Schemas ─────────────────────────────────────────────────────


class RelatedWorkRequest(BaseModel):
    paper_ids: list[str]
    style: str = Field("narrative", description="narrative, thematic, or chronological")
    format: str = Field("markdown", description="markdown or latex")


class AnnotatedBibRequest(BaseModel):
    paper_ids: list[str]
    annotation_depth: str = Field("detailed", description="brief or detailed")


class GapAnalysisRequest(BaseModel):
    paper_ids: list[str]
    research_question: str


class RebuttalRequest(BaseModel):
    paper_id: str
    reviewer_comments: str


# ─── Persisted Writing Documents ─────────────────────────────────


@router.get("/documents", response_model=WritingDocumentListResponse)
async def list_writing_documents(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List all writing documents for the current user."""
    svc = WritingDocumentService(db)
    return await svc.list_documents(user_id=user_id)


@router.post("/documents", response_model=WritingDocumentResponse, status_code=201)
async def create_writing_document(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Create a new empty writing document."""
    svc = WritingDocumentService(db)
    return await svc.create_document(user_id=user_id)


@router.get("/documents/{document_id}", response_model=WritingDocumentResponse)
async def get_writing_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Load a single user-owned writing document."""
    svc = WritingDocumentService(db)
    document = await svc.get_document(document_id=document_id, user_id=user_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Writing document not found")
    return document


@router.patch("/documents/{document_id}", response_model=WritingDocumentResponse)
async def update_writing_document(
    document_id: str,
    body: WritingDocumentUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Update a user-owned writing document."""
    svc = WritingDocumentService(db)
    document = await svc.update_document(
        document_id=document_id,
        user_id=user_id,
        title=body.title,
        markdown_content=body.markdown_content,
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Writing document not found")
    return document


@router.delete("/documents/{document_id}", status_code=204)
async def delete_writing_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Soft-delete a user-owned writing document."""
    svc = WritingDocumentService(db)
    deleted = await svc.delete_document(document_id=document_id, user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Writing document not found")


@router.post("/images", response_model=WritingImageUploadResponse, status_code=201)
async def upload_writing_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Upload a writing image via the configured OSS image host."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are accepted")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(data) > MAX_WRITING_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image too large")

    svc = WritingDocumentService(db)
    return await svc.upload_image(
        user_id=user_id,
        filename=file.filename,
        content_type=file.content_type,
        data=data,
    )


# ─── AI Writing Endpoints ───────────────────────────────────────


@router.post("/related-work")
async def generate_related_work(
    body: RelatedWorkRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a Related Work section from selected papers.

    Supports three writing styles:
    - **narrative**: flowing prose connecting papers
    - **thematic**: grouped by research themes
    - **chronological**: ordered by publication date

    Output in Markdown or LaTeX format.
    """
    svc = WritingService(db)
    try:
        result = await svc.generate_related_work(
            paper_ids=body.paper_ids,
            style=body.style,
            format=body.format,
        )
        _raise_writing_error(result)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Writing service error: {str(e)[:200]}",
        ) from e
    finally:
        await svc.close()


@router.post("/annotated-bibliography")
async def generate_annotated_bibliography(
    body: AnnotatedBibRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate an annotated bibliography for selected papers.

    Each entry includes: citation, summary, evaluation, and relevance note.
    """
    svc = WritingService(db)
    try:
        result = await svc.generate_annotated_bibliography(
            paper_ids=body.paper_ids,
            annotation_depth=body.annotation_depth,
        )
        _raise_writing_error(result)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Writing service error: {str(e)[:200]}",
        ) from e
    finally:
        await svc.close()


@router.post("/gap-analysis")
async def analyze_research_gaps(
    body: GapAnalysisRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Identify research gaps from literature relative to a research question.

    Returns structured analysis: well-covered areas, partially addressed,
    unexplored gaps, methodological gaps, and recommended directions.
    """
    svc = WritingService(db)
    try:
        result = await svc.analyze_gaps(
            paper_ids=body.paper_ids,
            research_question=body.research_question,
        )
        _raise_writing_error(result)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Writing service error: {str(e)[:200]}",
        ) from e
    finally:
        await svc.close()


@router.post("/rebuttal")
async def draft_rebuttal(
    body: RebuttalRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Draft a point-by-point rebuttal to reviewer comments.

    Generates professional, diplomatic responses to each concern.
    """
    svc = WritingService(db)
    try:
        result = await svc.draft_rebuttal(
            paper_id=body.paper_id,
            reviewer_comments=body.reviewer_comments,
        )
        _raise_writing_error(result)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Writing service error: {str(e)[:200]}",
        ) from e
    finally:
        await svc.close()
