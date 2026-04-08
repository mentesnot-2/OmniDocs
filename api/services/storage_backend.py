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


class LocalStorageBackend(StorageBackend):

    def _user_dir(self, user_id:int) -> Path:
        return UPLOAD_DIR / str(user_id)

        def _file_path(self,user_id:int, filename:str) -> Path:
            return self._user_dir(user_id) / filename

    def save_file(self, user_id:int, filename:str, content:bytes) -> str:
        user_dir = self._user_dir(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        path = self._file_path(user_id, filename)
        path.write_bytes(content)
        return str(path)

    def delete_file(self, user_id:int, filename:str) -> None:
        path = self._file_path(user_id, filename)
        if path.exists():
            path.unlink()

    def list_files(self, user_id:int) -> list[dict[str, Any]]:
        user_dir = self._user_dir(user_id)
        if not user_dir.exists():
            return []
        files:list[dict[str, Any]] = []
        for f in user_dir.iterdir():
            if f.is_file():
                files.append({
                    "filename": f.name,
                    "uploaded_at": f.stat().st_ctime
                }
            )
        files.sort(key=lambda x: x["uploaded_at"],reverse=True)
        return files

    def get_file_bytes(self, user_id:int, filename:str) -> bytes:
        return self._file_path(user_id, filename).read_bytes()
    
    def get_local_path(self, user_id:int,filename:str) -> Path | None:
        return self._file_path(user_id, filename)

