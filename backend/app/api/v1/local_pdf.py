"""Local PDF Intelligence API — upload, batch import, dedup, library management.

P2 WS-6: §6 (#41-48) from FeasibilityAnalysis.md
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user_id
from app.models.paper import Paper
from app.services.ingestion.pdf_batch_importer import PDFBatchImporter

router = APIRouter(prefix="/local", tags=["local-pdf"])

MAX_SINGLE_PDF_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_ZIP_SIZE = 500 * 1024 * 1024  # 500 MB


@router.post("/upload")
async def upload_single_pdf(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Upload a single PDF file for ingestion.

    The PDF is stored, a paper record is created, and GROBID parsing
    is queued automatically. Returns the paper ID and import status.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    content = await file.read()
    if len(content) > MAX_SINGLE_PDF_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 100 MB)")
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    importer = PDFBatchImporter(db)
    result = await importer.import_single_pdf(
        filename=file.filename,
        content=content,
        user_id=user_id,
    )

    # COMMIT FIRST, then queue parsing — prevents race condition
    await db.commit()

    if result["status"] == "imported":
        try:
            from app.tasks.ingest_tasks import parse_fulltext_task
            parse_fulltext_task.delay(result["paper_id"])
        except Exception:
            pass  # Task queue may not be running in dev

    return result


@router.post("/batch-upload")
async def batch_upload_pdfs(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Upload a ZIP archive of PDFs for batch ingestion.

    Extracts all .pdf files from the ZIP, deduplicates,
    and queues each for GROBID parsing.

    Returns summary with counts and per-file results.
    """
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only ZIP files are accepted")

    content = await file.read()
    if len(content) > MAX_ZIP_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 500 MB)")

    importer = PDFBatchImporter(db)
    result = await importer.import_zip(zip_content=content, user_id=user_id)

    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])

    # COMMIT FIRST, then queue parsing — prevents race condition
    await db.commit()

    imported_ids = [
        r["paper_id"]
        for r in result.get("results", [])
        if r["status"] == "imported"
    ]
    for paper_id in imported_ids:
        try:
            from app.tasks.ingest_tasks import parse_fulltext_task
            parse_fulltext_task.delay(paper_id)
        except Exception:
            pass

    return result


@router.get("/library")
async def list_local_papers(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List papers imported from local PDFs, scoped to the current user."""
    result = await db.execute(
        select(Paper)
        .where(
            Paper.deleted_at.is_(None),
            Paper.source_type.in_(["local_upload", "local_folder"]),
            Paper.raw_metadata["uploaded_by_user"].astext == user_id,
        )
        .order_by(Paper.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    papers = result.scalars().all()

    count_result = await db.execute(
        select(func.count(Paper.id)).where(
            Paper.deleted_at.is_(None),
            Paper.source_type.in_(["local_upload", "local_folder"]),
            Paper.raw_metadata["uploaded_by_user"].astext == user_id,
        )
    )
    total = count_result.scalar() or 0

    return {
        "total": total,
        "papers": [
            {
                "id": str(p.id),
                "title": p.title,
                "doi": p.doi,
                "arxiv_id": p.arxiv_id,
                "source_type": p.source_type,
                "ingestion_status": p.ingestion_status,
                "has_full_text": p.has_full_text,
                "created_at": str(p.created_at),
            }
            for p in papers
        ],
        "limit": limit,
        "offset": offset,
    }


@router.post("/deduplicate")
async def check_duplicates(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Scan the library for duplicate papers.

    Finds duplicates by DOI exact match and title exact match.
    Returns groups of duplicate papers.
    """
    importer = PDFBatchImporter(db)
    groups = await importer.check_duplicates()
    return {
        "duplicate_groups": len(groups),
        "groups": groups,
    }


@router.get("/library/stats")
async def library_stats(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get statistics about the paper library."""
    importer = PDFBatchImporter(db)
    return await importer.get_library_stats(user_id=user_id)
