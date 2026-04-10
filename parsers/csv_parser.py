"""
CSV text extraction using Python's built-in csv module.
"""

import csv
from pathlib import Path
from parsers.base import ParsedDocument, normalize_source_file

def parse_csv(file_path:Path) -> ParsedDocument:
    """
    Extract content from CSV as readable test (rows as lines)
    """

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"CSV not found: {file_path}")
    
    rows = []

    with open(file_path, 'r', encoding='utf-8', errors="replace") as f:
        reader = csv.reader(f)
        for row in reader:
            if any(cell.strip() for cell in row):
                rows.append(" | ".join(cell.strip() for cell in row))
    full_text = "\n".join(rows)

    return ParsedDocument(
        content=full_text,
        source_file=normalize_source_file(file_path),
        metadata={
            "format":"csv",
            "row_count": len(rows),
        }
    )
