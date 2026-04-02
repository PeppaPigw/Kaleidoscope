"""Business logic for persisted writing draft documents."""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.oss_client import OssClient
from app.models.writing import WritingDocument


_MARKDOWN_CODE_FENCE_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
_MARKDOWN_INLINE_CODE_RE = re.compile(r"`([^`]+)`")
_MARKDOWN_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\([^)]+\)")
_MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_MARKDOWN_FORMATTING_RE = re.compile(r"[*_>#~\-]+")
_MULTISPACE_RE = re.compile(r"\s+")


class WritingDocumentService:
    """Persist and fetch user-scoped writing documents."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_documents(self, user_id: str) -> dict[str, object]:
        result = await self.db.execute(
            select(WritingDocument)
            .where(
                WritingDocument.user_id == user_id,
                WritingDocument.deleted_at.is_(None),
            )
            .order_by(
                func.coalesce(
                    WritingDocument.updated_at,
                    WritingDocument.created_at,
                ).desc()
            )
        )
        items = list(result.scalars().all())
        return {"items": items, "total": len(items)}

    async def create_document(
        self,
        user_id: str,
        title: str = "Untitled",
    ) -> WritingDocument:
        document = WritingDocument(
            user_id=user_id,
            title=title,
            markdown_content="",
            plain_text_excerpt="",
            word_count=0,
            last_opened_at=datetime.now(timezone.utc),
        )
        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)
        return document

    async def get_document(
        self,
        document_id: str,
        user_id: str,
    ) -> WritingDocument | None:
        result = await self.db.execute(
            select(WritingDocument).where(
                WritingDocument.id == self._to_uuid(document_id),
                WritingDocument.user_id == user_id,
                WritingDocument.deleted_at.is_(None),
            )
        )
        document = result.scalar_one_or_none()
        if document is not None:
            document.last_opened_at = datetime.now(timezone.utc)
            await self.db.flush()
            await self.db.refresh(document)
        return document

    async def update_document(
        self,
        document_id: str,
        user_id: str,
        title: str | None,
        markdown_content: str | None,
    ) -> WritingDocument | None:
        document = await self._get_owned_document(document_id, user_id)
        if document is None:
            return None

        if title is not None:
            document.title = title
        if markdown_content is not None:
            document.markdown_content = markdown_content
            plain_text = self._markdown_to_plain_text(markdown_content)
            document.plain_text_excerpt = plain_text[:280]
            document.word_count = self._count_words(plain_text)

        await self.db.flush()
        await self.db.refresh(document)
        return document

    async def delete_document(self, document_id: str, user_id: str) -> bool:
        document = await self._get_owned_document(document_id, user_id)
        if document is None:
            return False
        document.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True

    async def upload_image(
        self,
        *,
        user_id: str,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> dict[str, str]:
        safe_name = self._sanitize_filename(filename)
        object_key = f"Kaleidoscope/writing/{user_id}/{uuid.uuid4()}-{safe_name}"
        async with OssClient() as oss:
            url = await oss.upload_bytes(data, object_key)
        return {"url": url}

    async def _get_owned_document(
        self,
        document_id: str,
        user_id: str,
    ) -> WritingDocument | None:
        result = await self.db.execute(
            select(WritingDocument).where(
                WritingDocument.id == self._to_uuid(document_id),
                WritingDocument.user_id == user_id,
                WritingDocument.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    def _to_uuid(self, value: str) -> uuid.UUID:
        return uuid.UUID(str(value))

    def _sanitize_filename(self, filename: str) -> str:
        base_name = Path(filename).name or "image.bin"
        return re.sub(r"[^A-Za-z0-9._-]+", "-", base_name)

    def _markdown_to_plain_text(self, markdown_content: str) -> str:
        text = _MARKDOWN_CODE_FENCE_RE.sub(" ", markdown_content)
        text = _MARKDOWN_INLINE_CODE_RE.sub(r"\1", text)
        text = _MARKDOWN_IMAGE_RE.sub(r"\1", text)
        text = _MARKDOWN_LINK_RE.sub(r"\1", text)
        text = text.replace("$$", " ").replace("$", " ")
        text = _MARKDOWN_FORMATTING_RE.sub(" ", text)
        text = _MULTISPACE_RE.sub(" ", text)
        return text.strip()

    def _count_words(self, plain_text: str) -> int:
        if not plain_text:
            return 0
        return len([token for token in plain_text.split(" ") if token])
