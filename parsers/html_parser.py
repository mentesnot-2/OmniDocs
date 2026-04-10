"""
HTML text extraction using BeautifulSoup.

"""
from pathlib import Path
from parsers.base import ParsedDocument, normalize_source_file


def parse_html(file_path:Path) -> ParsedDocument:
    """Extract text from HTML file."""

    from bs4 import BeautifulSoup
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"HTML not found: {file_path}")
    
    with open(file_path,'r',encoding="utf-8",errors="replace") as f:
        soup = BeautifulSoup(f,features="html.parser")
    
    # Remove script/style
    for tag in soup(["script","style"]):
        tag.decompose()
    text = soup.get_text(separator="\n",strip=True)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    full_text = "\n".join(lines)

    return ParsedDocument(
        content=full_text,
        source_file=normalize_source_file(file_path),
        metadata={
            "format":"html",
        }
    )
    