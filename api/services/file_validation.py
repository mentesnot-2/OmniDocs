from __future__ import annotations

import io
from pathlib import Path
from zipfile import BadZipFile, ZipFile

import filetype
from fastapi import HTTPException, status


# Known signature-based expectations

ALLOWED_SIGNATURES = {
    ".pdf": {"application/pdf"},
    ".docx": {"application/zip"},
    ".xlsx": {"application/zip"},
    ".pptx": {"application/zip"},
}


# Extensions that text-like and need fallback handling
TEXT_LIKE_EXTENSIONS = {".txt", ".md", ".csv", ".html", ".htm"}


# Basic OOXML structure checks

OOXML_REQUIRED_MEMBERS = {
    ".docs": {"[Content_Types].xml", "word/document.xml"},
    ".xlsx": {"[Content_Types].xml", "xl/workbook.xml"},
    ".pptx": {"[Content_Types].xml", "ppt/presentation.xml"},
}


# Optional simple zip-bomb guardrail
MAX_ARCHIVE_MEMBERS = 500
MAX_ARCHIVE_UNCOMPRESSED_BYTES = 100 * 1024 * 1024 # 100MB
MAX_COMPRESSION_RATIO = 100



def _detect_mime(content: bytes) -> str | None:
    kind = filetype.guess(content)
    if not kind:
        return None
    return kind.mime

def _looks_like_text(content: bytes) -> bool:
    """
    Best-effort check for text-like file.
    Reject obvious binary payloads while allowing UTF-8 text.
    """

    sample = content[:4096]
    if b"\x00" in sample:
        return False
    try:
        sample.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False

def _validate_ooxml_archive(ext: str, content: bytes) -> None:
    required = OOXML_REQUIRED_MEMBERS.get(ext)

    if not required:
        return 
    

    try:
        with ZipFile(io.BytesIO(content),"r") as zf:
            names = set(zf.namelist())

            missing = required - names

            if missing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Uploaded file content does not match the claimed Office format.",
                )

            infos = zf.infolist()

            if len(infos) > MAX_ARCHIVE_MEMBERS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Archive structure is too large to process safely."
                )
            
            total_uncompressed = 0
            total_compressed = 0

            for info in infos:
                total_uncompressed+=int(info.file_size or 0)
                total_compressed+=int(info.file_size or 0)

            
            if total_compressed > 0:
                ratio = total_uncompressed / total_compressed

                if ratio > MAX_COMPRESSION_RATIO:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Archive compression ratio is unsafe.",
                    )

    except BadZipFile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded Office file is not a valid archive."
        )


def validate_uploaded_file_content(filename:str, content:bytes) -> None:
    """
    Validate uploaded file content beyond extension-only checks.
    Defense layers:
        1. signature / MIME check for binary formats
        2. text-like fallback for text/html/csv/markdown
        3. OOXML internal archive structure validation
    """


    ext = Path(filename).suffix.lower()
    
    detected_mime = _detect_mime(content)

    if ext in ALLOWED_SIGNATURES:
        allowed_mimes = ALLOWED_SIGNATURES[ext]
        if detected_mime not in allowed_mimes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file content does not match its extension."
            )
    elif ext in TEXT_LIKE_EXTENSIONS:
        if not _looks_like_text(content):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file content is not a valid text-based document."
            )

    _validate_ooxml_archive(ext, content)

    