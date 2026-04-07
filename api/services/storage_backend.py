from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional
import io

import boto3

from config import (
    STORAGE_BACKEND,
    UPLOAD_DIR,
    S3_BUCKET_NAME,
    S3_REGION,
    S3_ACCESS_KEY_ID,
    S3_SECRET_ACCESS_KEY,
    S3_ENDPOINT_URL,
    S3_KEY_PREFIX,
)


class StorageBackend(ABC):

    @abstractmethod
    def save_file(self, user_id:int,filename:str, content:bytes) -> str:
        """Save file and return storage key/refernce."""
        raise NotImplementedError

    @abstractmethod
    def delete_file(self, user_id:int, filename:str) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_files(self, user_id:int) -> list[dict[str,Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_file_bytes(self, user_id:int, filename: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def get_local_path(self, user_id:int) -> Path | None:
        """
        Return a local file path if available.
        Local backend can return a real path.
        Remote backend can return None.
        """
        raise NotImplementedError