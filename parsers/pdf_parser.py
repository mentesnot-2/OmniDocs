"""
PDF text extraction using pypdf.

"""

from pathlib import Path
from parsers.base import ParsedDocument

def parse_pdf(file_path:Path) -> ParsedDocument:
    """
    Extract text from PDF file.
    Returns a ParsedDocument with content and per-page metadata.

    """
    from pypdf import PdfReader

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")
    reader = PdfReader(file_path)
    pages_text = []
    
    for i,page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages_text.append(text)
    full_text = "\n\n".join(pages_text)
    metadata = {
        "page_count": len(reader.pages),
        "format":"pdf",
    }
    return ParsedDocument(
        content=full_text,
        source_file=str(file_path),
        metadata=metadata,
    )