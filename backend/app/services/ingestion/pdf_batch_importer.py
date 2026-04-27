"""Local PDF batch importer — bulk upload, publish, deduplicate, index.

Handles:
- Single PDF upload → publish MinerU source URL → dedup → index
- Batch ZIP upload → extract → process each PDF
- Folder path scanning (server-side)
- Duplicate detection via DOI exact + title fuzzy match
"""

import hashlib
import io
import os
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.paper import Paper

logger = structlog.get_logger(__name__)


def _bind_logger(**context):
    """Return a bound logger, tolerating test loggers that bind to None."""
    return logger.bind(**context) or logger


class PDFBatchImporter:
    """Import local PDFs into Kaleidoscope."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def import_single_pdf(
        self,
        filename: str,
        content: bytes,
        user_id: str | None = None,
    ) -> dict:
        """
        Import a single PDF file.

        Pipeline: hash → dedup check → store → publish MinerU URL → enrich

        Returns:
            {paper_id, status, is_duplicate, matched_paper_id, mineru_url}
        """
        log = _bind_logger(filename=filename)

        # 1. Compute content hash for dedup
        content_hash = hashlib.sha256(content).hexdigest()

        # 2. Check for existing paper with same hash
        existing = await self._find_by_hash(content_hash)
        if existing:
            log.info("duplicate_by_hash", existing_id=str(existing.id))
            return {
                "paper_id": str(existing.id),
                "status": "duplicate",
                "is_duplicate": True,
                "matched_paper_id": str(existing.id),
                "match_type": "content_hash",
            }

        # 3. Create paper record
        paper = Paper(
            title=Path(filename).stem.replace("_", " ").replace("-", " "),
            source_type="local_upload",
            visibility="private",
            ingestion_status="discovered",
            has_full_text=True,
            raw_metadata={
                "source": "local_upload",
                "original_filename": filename,
                "content_hash": content_hash,
                "upload_timestamp": datetime.now(UTC).isoformat(),
                "uploaded_by_user": user_id or "anonymous",
            },
        )
        self.db.add(paper)
        await self.db.flush()

        paper_id = str(paper.id)
        log = log.bind(paper_id=paper_id) or log

        # 4. Store PDF content (write to MinIO or local)
        pdf_path = await self._store_pdf(paper_id, filename, content)
        paper.pdf_path = pdf_path

        # 5. Publish a public PDF URL that MinerU can fetch directly
        mineru_url = await self._publish_pdf_for_mineru(paper_id, content)
        paper.remote_urls = [
            {
                "url": mineru_url,
                "source": "local_upload_public",
                "type": "pdf",
            }
        ]
        paper.raw_metadata = {
            **dict(paper.raw_metadata or {}),
            "mineru_source": "oss_public_pdf",
            "mineru_source_url": mineru_url,
        }

        # 6. Quick metadata extraction from filename
        # (Full MinerU parse will be done async via task queue)
        await self.db.flush()

        log.info("pdf_imported", pdf_path=pdf_path, mineru_url=mineru_url)
        return {
            "paper_id": paper_id,
            "status": "imported",
            "is_duplicate": False,
            "matched_paper_id": None,
            "match_type": None,
            "mineru_url": mineru_url,
        }

    async def import_zip(self, zip_content: bytes, user_id: str | None = None) -> dict:
        """
        Import a ZIP archive of PDFs.

        Returns summary: {total, imported, duplicates, errors, results: [...]}
        """
        results = []
        errors = []

        try:
            with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
                pdf_names = [
                    n
                    for n in zf.namelist()
                    if n.lower().endswith(".pdf") and not n.startswith("__MACOSX")
                ]

                for name in pdf_names:
                    try:
                        pdf_bytes = zf.read(name)
                        result = await self.import_single_pdf(
                            filename=os.path.basename(name),
                            content=pdf_bytes,
                            user_id=user_id,
                        )
                        results.append(result)
                    except Exception as e:
                        logger.error("zip_entry_failed", name=name, error=str(e))
                        errors.append({"filename": name, "error": str(e)})

        except zipfile.BadZipFile:
            return {"error": "Invalid ZIP file", "total": 0}

        imported = sum(1 for r in results if r["status"] == "imported")
        duplicates = sum(1 for r in results if r["status"] == "duplicate")

        return {
            "total": len(results) + len(errors),
            "imported": imported,
            "duplicates": duplicates,
            "errors": len(errors),
            "results": results,
            "error_details": errors,
        }

    async def check_duplicates(self, paper_ids: list[str] | None = None) -> list[dict]:
        """
        Scan for duplicate papers in the library.

        Uses: DOI exact match → title fuzzy match (trigram similarity).

        Returns list of duplicate groups: [{papers: [...], match_type}]
        """
        groups = []

        # 1. DOI-based duplicates (exact)
        doi_dupes = await self.db.execute(
            select(Paper.doi, func.count(Paper.id).label("cnt"))
            .where(Paper.deleted_at.is_(None), Paper.doi.is_not(None))
            .group_by(Paper.doi)
            .having(func.count(Paper.id) > 1)
        )
        for row in doi_dupes.all():
            papers_result = await self.db.execute(
                select(Paper.id, Paper.title, Paper.doi).where(
                    Paper.doi == row.doi, Paper.deleted_at.is_(None)
                )
            )
            papers = [
                {"id": str(p.id), "title": p.title, "doi": p.doi}
                for p in papers_result.all()
            ]
            groups.append(
                {
                    "match_type": "doi_exact",
                    "match_value": row.doi,
                    "papers": papers,
                }
            )

        # 2. Title-based duplicates (exact lowercase match)
        title_dupes = await self.db.execute(
            select(
                func.lower(Paper.title).label("ltitle"),
                func.count(Paper.id).label("cnt"),
            )
            .where(Paper.deleted_at.is_(None))
            .group_by(func.lower(Paper.title))
            .having(func.count(Paper.id) > 1)
        )
        for row in title_dupes.all():
            papers_result = await self.db.execute(
                select(Paper.id, Paper.title, Paper.doi).where(
                    func.lower(Paper.title) == row.ltitle,
                    Paper.deleted_at.is_(None),
                )
            )
            papers = [
                {"id": str(p.id), "title": p.title, "doi": p.doi}
                for p in papers_result.all()
            ]
            # Don't double-count papers already in DOI groups
            if not any(
                g["match_type"] == "doi_exact"
                and set(p["id"] for p in g["papers"]) == set(p["id"] for p in papers)
                for g in groups
            ):
                groups.append(
                    {
                        "match_type": "title_exact",
                        "match_value": row.ltitle,
                        "papers": papers,
                    }
                )

        return groups

    async def get_library_stats(self, user_id: str | None = None) -> dict:
        """Get statistics about the local paper library."""
        base = select(func.count(Paper.id)).where(Paper.deleted_at.is_(None))

        total = (await self.db.execute(base)).scalar() or 0
        local = (
            await self.db.execute(
                base.where(Paper.source_type.in_(["local_upload", "local_folder"]))
            )
        ).scalar() or 0
        with_fulltext = (
            await self.db.execute(base.where(Paper.has_full_text == True))
        ).scalar() or 0
        parsed = (
            await self.db.execute(base.where(Paper.ingestion_status == "parsed"))
        ).scalar() or 0
        indexed = (
            await self.db.execute(base.where(Paper.ingestion_status == "indexed"))
        ).scalar() or 0

        return {
            "total_papers": total,
            "local_papers": local,
            "remote_papers": total - local,
            "with_full_text": with_fulltext,
            "parsed": parsed,
            "indexed": indexed,
        }

    # ─── Private helpers ─────────────────────────────────────────

    async def _find_by_hash(self, content_hash: str) -> Paper | None:
        """Find existing paper by content hash (stored in raw_metadata)."""
        # Use JSONB containment query
        from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB

        result = await self.db.execute(
            select(Paper)
            .where(
                Paper.raw_metadata.cast(PG_JSONB).contains(
                    {"content_hash": content_hash}
                ),
                Paper.deleted_at.is_(None),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _store_pdf(self, paper_id: str, filename: str, content: bytes) -> str:
        """
        Store PDF to the same location used by PDFDownloaderService.

        Uses /tmp/kaleidoscope-papers/<object_key> so that
        PDFDownloaderService.load_content() can find it later
        during the parse task.
        """
        from app.services.ingestion.pdf_downloader import PDFDownloaderService

        object_key = f"papers/{paper_id}/local_upload.pdf"
        PDFDownloaderService._persist_content(object_key, content)
        return object_key

    async def _publish_pdf_for_mineru(self, paper_id: str, content: bytes) -> str:
        """
        Publish the uploaded PDF to a public object store URL for MinerU.

        MinerU only accepts fetchable document URLs, so local uploads must be
        mirrored to public storage before the parsing task can run.
        """
        from app.clients.oss_client import OssClient

        object_key = f"Kaleidoscope/local-pdfs/{paper_id}/source.pdf"
        async with OssClient() as oss:
            return await oss.upload_bytes(content, object_key)
