"""Document parsers for multiple formats."""
from parsers.base import ParsedDocument
from parsers.pdf_parser import parse_pdf

__all__ = ["ParsedDocument", "parse_pdf"]