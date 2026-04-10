"""
TXT and Markdown text extraction.
"""
from pathlib import Path
from parsers.base import ParsedDocument, normalize_source_file

def parse_txt(file_path:Path) -> ParsedDocument:
    """
    Extract text from TXT or Markdown file.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8',errors="replace") as f:
        content = f.read()
    ext = file_path.suffix.lower()
    format_type = "markdown" if ext == ".md" else "txt"

    return ParsedDocument(
        content=content,
        source_file=normalize_source_file(file_path),
        metadata={
            "format":format_type,
        }
    )