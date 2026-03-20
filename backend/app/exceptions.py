"""Custom exception hierarchy for Kaleidoscope."""


class KaleidoscopeError(Exception):
    """Base exception for all Kaleidoscope errors."""


# --- Domain Errors ---


class PaperNotFoundError(KaleidoscopeError):
    """Paper does not exist in database."""

    def __init__(self, identifier: str, id_type: str = "id"):
        self.identifier = identifier
        self.id_type = id_type
        super().__init__(f"Paper not found: {id_type}={identifier}")


class DuplicatePaperError(KaleidoscopeError):
    """Paper already exists in database."""

    def __init__(self, doi: str, existing_id: str):
        self.doi = doi
        self.existing_id = existing_id
        super().__init__(f"Duplicate paper: DOI {doi} exists as {existing_id}")


# --- External API Errors ---


class ExternalAPIError(KaleidoscopeError):
    """External API call failed."""

    def __init__(self, service: str, status: int, message: str):
        self.service = service
        self.status = status
        super().__init__(f"{service} returned {status}: {message}")


class RateLimitError(ExternalAPIError):
    """API rate limit hit. Includes retry timing."""

    def __init__(self, service: str, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(service, 429, f"Rate limited. Retry after {retry_after}s")


# --- Processing Errors ---


class PDFAcquisitionError(KaleidoscopeError):
    """Failed to acquire PDF from any source."""

    def __init__(self, paper_id: str, attempted_sources: list[str]):
        self.paper_id = paper_id
        self.attempted_sources = attempted_sources
        super().__init__(
            f"PDF acquisition failed for {paper_id}. "
            f"Tried: {', '.join(attempted_sources)}"
        )


class ParsingError(KaleidoscopeError):
    """Document parsing failed (GROBID, PDF extraction, etc.)."""

    def __init__(self, paper_id: str, parser: str, reason: str):
        self.paper_id = paper_id
        self.parser = parser
        super().__init__(f"{parser} parsing failed for {paper_id}: {reason}")


# --- Storage Errors ---


class StorageError(KaleidoscopeError):
    """MinIO/S3 storage operation failed."""

    def __init__(self, operation: str, key: str, reason: str):
        self.operation = operation
        self.key = key
        super().__init__(f"Storage {operation} failed for {key}: {reason}")
