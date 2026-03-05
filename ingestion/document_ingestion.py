"""
Document ingestion pipeline.
Detects file type routes to appropriate parsers.
"""

from pathlib import Path
from typing import Optional
from parsers import (
    ParsedDocument,
    parse_pdf,
    parse_docx,
    parse_txt,
    parse_csv,
    parse_xlsx,
    parse_html,
)

PARSER_MAP = {
    ".pdf": parse_pdf,
    ".docx": parse_docx,
    ".txt": parse_txt,
    ".md": parse_txt,
    ".markdown": parse_txt,
    ".csv": parse_csv,
    ".xlsx": parse_xlsx,
    ".html": parse_html,
    ".htm": parse_html,
}

def ingest_document(file_path:Path) -> ParsedDocument:
    """Ingest a document by detecting its type and parsing it.
    Args:
        file_path: Path to the document to ingest.
    Returns:
        The parsed document if successful, None if unsupported format.
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: if file type is unsupported.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    ext = file_path.suffix.lower()

    if ext not in PARSER_MAP:
        raise ValueError(
            f"Unsupported file type: {ext}"
            f"Supported types: {', '.join(PARSER_MAP.keys())}"
        )
    parser = PARSER_MAP[ext]

    try:
        parsed = parser(file_path)
        return parsed
    except Exception as e:
        raise RuntimeError(f"failed to parse {file_path}: {e}") from e

def get_supported_extensions() -> list[str]:
    """Get all supported file extensions."""
    return list(PARSER_MAP.keys())