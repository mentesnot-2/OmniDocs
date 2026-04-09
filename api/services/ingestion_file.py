from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import UploadFile


class FileTooLargeError(ValueError):
    """Raised when an uploaded file exceeds the configured size limit."""


def write_temp_file(filename: str, content: bytes) -> Path:
    suffix = Path(filename).suffix
    tmp = NamedTemporaryFile(suffix=suffix, delete=False)
    tmp.write(content)
    tmp.flush()
    tmp.close()
    return Path(tmp.name)


async def write_upload_to_temp_file(
    upload_file: UploadFile,
    filename: str,
    *,
    max_bytes: int,
    chunk_size: int = 1024 * 1024,
) -> tuple[Path, int]:
    """Stream an uploaded file to disk while enforcing a hard size cap."""
    suffix = Path(filename).suffix
    tmp = NamedTemporaryFile(suffix=suffix, delete=False)
    temp_path = Path(tmp.name)
    total_bytes = 0

    try:
        while True:
            chunk = await upload_file.read(chunk_size)
            if not chunk:
                break

            total_bytes += len(chunk)
            if total_bytes > max_bytes:
                raise FileTooLargeError()

            tmp.write(chunk)

        tmp.flush()
        return temp_path, total_bytes
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
    finally:
        tmp.close()
