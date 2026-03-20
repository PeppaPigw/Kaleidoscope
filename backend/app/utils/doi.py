"""DOI normalization and validation utilities."""

import re


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
    """
    if not text:
        return None

    text = text.strip()

    # New-style: 2403.12345 or 2403.12345v2
    new_match = re.search(r"(\d{4}\.\d{4,5})(v\d+)?", text)
    if new_match:
        return new_match.group(0)

    # Old-style: cond-mat/0001234 or hep-th/9901001
    old_match = re.search(r"([a-z-]+/\d{7})(v\d+)?", text)
    if old_match:
        return old_match.group(0)

    return None


def extract_pmid(text: str) -> str | None:
    """Extract PubMed ID from a string."""
    if not text:
        return None

    match = re.search(r"(?:PMID:?\s*)?(\d{6,9})", text.strip())
    return match.group(1) if match else None
