"""Document parsers for multiple formats."""
from parsers.base import ParsedDocument
from parsers.pdf_parser import parse_pdf
from parsers.docx_parser import parse_docx
from parsers.txt_parser import parse_txt

__all__ = ["ParsedDocument", "parse_pdf", "parse_docx", "parse_txt"]