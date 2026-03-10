"""PowerPoint (.pptx) parser. """

from pathlib import Path
from parsers.base import ParsedDocument


def parse_pptx(file_path:Path) -> ParsedDocument:

    from pptx import Presentation

    prs = Presentation(file_path)
    texts = []
    for i, slide in enumerate(prs.slides):
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                texts.append(f"[Slide {i+1}] {shape.text.strip()}")
    content = "\n\n".join(texts) if texts else ""

    return ParsedDocument(
        content=content,
        metadata={
            "source_file":file_path.name,
            "format":"pptx",
            "slide_count":len(prs.slides),
        }
    )