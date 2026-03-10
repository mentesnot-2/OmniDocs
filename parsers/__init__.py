"""Document parsers for multiple formats."""
from parsers.base import ParsedDocument
from parsers.pdf_parser import parse_pdf
from parsers.docx_parser import parse_docx
from parsers.txt_parser import parse_txt
from parsers.csv_parser import parse_csv
from parsers.xlsx_parser import parse_xlsx
from parsers.html_parser import parse_html
from parsers.pptx_parser import parse_pptx

__all__ = [
    "ParsedDocument",
    "parse_pdf",
    "parse_docx",
    "parse_txt",
    "parse_csv",
    "parse_xlsx",
    "parse_html",
    "parse_pptx",
]