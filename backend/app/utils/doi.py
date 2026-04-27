"""DOI, arXiv ID, and PMID normalization and validation utilities."""

import re
from urllib.parse import urlparse

_DOI_REGEX = re.compile(r"10\.\d{4,9}/[^\s]+")
_DOI_URL_PREFIXES = [
    "https://doi.org/",
    "http://doi.org/",
    "https://dx.doi.org/",
    "http://dx.doi.org/",
]


def normalize_doi(doi: str) -> str | None:
    """
    Normalize a DOI to its canonical form (lowercase, no URL prefix).

    Examples:
        "https://doi.org/10.1038/nature12373" → "10.1038/nature12373"
        "10.1038/NATURE12373" → "10.1038/nature12373"
    """
    if not doi:
        return None

    doi = doi.strip()

    # Strip URL prefix
    for prefix in _DOI_URL_PREFIXES:
        if doi.lower().startswith(prefix.lower()):
            doi = doi[len(prefix) :]
            break

    # Validate structure
    if not _DOI_REGEX.match(doi):
        return None

    return doi.lower()


def is_valid_doi(doi: str) -> bool:
    """Check if a string is a valid DOI."""
    return normalize_doi(doi) is not None


def doi_to_url(doi: str) -> str:
    """Convert a DOI to its canonical URL."""
    normalized = normalize_doi(doi)
    if normalized is None:
        raise ValueError(f"Invalid DOI: {doi}")
    return f"https://doi.org/{normalized}"


def extract_arxiv_id(text: str) -> str | None:
    """
    Extract arXiv ID from a string (URL or plain ID).

    Handles both old-style (hep-th/9901001) and new-style (2403.12345) formats.
    Always returns the ID without `arXiv:` prefix.
    """
    if not text:
        return None

    text = text.strip()
    # Strip arXiv: prefix
    if text.lower().startswith("arxiv:"):
        text = text[6:]

    # New-style: 2403.12345 or 2403.12345v2
    new_match = re.search(r"(\d{4}\.\d{4,5})(v\d+)?", text)
    if new_match:
        return new_match.group(0)

    # Old-style: cond-mat/0001234 or hep-th/9901001
    old_match = re.search(r"([a-z-]+/\d{7})(v\d+)?", text)
    if old_match:
        return old_match.group(0)

    return None


def normalize_arxiv_id(arxiv_id: str) -> str:
    """
    Normalize an arXiv ID: strip `arXiv:` prefix and whitespace.

    Use this everywhere arXiv IDs are stored or compared to prevent
    duplication between "arXiv:2403.12345" and "2403.12345".
    """
    if not arxiv_id:
        return arxiv_id
    arxiv_id = arxiv_id.strip()
    if arxiv_id.lower().startswith("arxiv:"):
        arxiv_id = arxiv_id[6:]
    return arxiv_id


def extract_pmid(text: str) -> str | None:
    """Extract PubMed ID from a string."""
    if not text:
        return None

    match = re.search(r"(?:PMID:?\s*)?(\d{6,9})", text.strip())
    return match.group(1) if match else None


def extract_doi_from_url(url: str) -> str | None:
    """
    Extract DOI from a publisher article URL.

    Handles common publisher URL patterns:
    - doi.org/10.xxx/yyy
    - nature.com/articles/s41586-024-xxx → 10.1038/s41586-024-xxx
    - sciencedirect.com/science/article/pii/S... → needs API lookup (returns None)
    - onlinelibrary.wiley.com/doi/10.xxx/yyy
    - link.springer.com/article/10.xxx/yyy
    - iopscience.iop.org/article/10.xxx/yyy
    - journals.aps.org/prl/abstract/10.xxx/yyy
    - pnas.org/doi/10.xxx/yyy
    - science.org/doi/10.xxx/yyy
    - ieeexplore.ieee.org/document/xxx (no DOI extractable → None)
    """
    if not url:
        return None

    # First try: direct DOI extraction from URL (works for most)
    doi_match = _DOI_REGEX.search(url)
    if doi_match:
        doi = doi_match.group(0)
        # Clean trailing punctuation
        doi = doi.rstrip(".,;:)]'\"")
        return normalize_doi(doi)

    # Nature articles: nature.com/articles/{suffix}
    parsed = urlparse(url)
    if "nature.com" in parsed.netloc:
        parts = parsed.path.strip("/").split("/")
        if "articles" in parts:
            idx = parts.index("articles")
            if idx + 1 < len(parts):
                suffix = parts[idx + 1]
                # Nature DOIs are 10.1038/{suffix}
                candidate = f"10.1038/{suffix}"
                return normalize_doi(candidate)

    return None
