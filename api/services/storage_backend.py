from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from shutil import copyfileobj
from typing import Any, BinaryIO
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

    def save_file(self, user_id:int,filename:str, content:bytes) -> str:
        """Save bytes content and return a storage reference."""
        with io.BytesIO(content) as fileobj:
            return self.save_fileobj(user_id, filename, fileobj)

    @abstractmethod
    def save_fileobj(self, user_id:int, filename:str, fileobj: BinaryIO) -> str:
        """Save a binary file object and return a storage reference."""
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
    def get_local_path(self, user_id:int, filename:str) -> Path | None:
        """
        Return a local file path if available.
        Local backend can return a real path.
        Remote backend can return None.
        """
        raise NotImplementedError

    @abstractmethod
    def file_exists(self, user_id:int, filename:str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_usage_bytes(self, user_id:int) -> int:
        raise NotImplementedError


class LocalStorageBackend(StorageBackend):

    def _user_dir(self, user_id:int) -> Path:
        return UPLOAD_DIR / str(user_id)

    def _file_path(self, user_id:int, filename:str) -> Path:
        return self._user_dir(user_id) / filename

    def save_fileobj(self, user_id:int, filename:str, fileobj: BinaryIO) -> str:
        user_dir = self._user_dir(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        path = self._file_path(user_id, filename)
        if hasattr(fileobj, "seek"):
            fileobj.seek(0)
        with path.open("wb") as destination:
            copyfileobj(fileobj, destination)
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


    def file_exists(self, user_id:int, filename:str) -> bool:
        return self._file_path(user_id, filename).exists()

    def get_usage_bytes(self, user_id:int) -> int:
        user_dir = self._user_dir(user_id)
        if not user_dir.exists():
            return 0

        total= 0
        for path in user_dir.rglob("*"):
            if path.is_file():
                total += path.stat().st_size
        return total

class S3StorageBackend(StorageBackend):
    def __init__(self):
        self.bucket = S3_BUCKET_NAME
        self.client = boto3.client(
            "s3",
            region_name=S3_REGION,
            aws_access_key_id=S3_ACCESS_KEY_ID or None,
            aws_secret_access_key=S3_SECRET_ACCESS_KEY or None,
            endpoint_url=S3_ENDPOINT_URL or None,
        )
    
    def _key(self, user_id:int, filename:str) -> str:
        return f"{S3_KEY_PREFIX}/{user_id}/{filename}"

    def save_fileobj(self, user_id:int, filename:str, fileobj: BinaryIO) -> str:
        key = self._key(user_id, filename)
        if hasattr(fileobj, "seek"):
            fileobj.seek(0)
        self.client.upload_fileobj(
            fileobj,
            self.bucket,
            key,
        )
        return key

    def delete_file(self, user_id:int, filename:str) -> None:
        key = self._key(user_id, filename)
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def list_files(self, user_id:int) -> list[dict[str, Any]]:
        prefix = f"{S3_KEY_PREFIX}/{user_id}/"

        response = self.client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)

        contents = response.get("Contents", [])

        files:list[dict[str, Any]] = []
        for obj in contents:
            key = obj["Key"]
            if key.endswith("/"):
                continue
            files.append({
                "filename": key.split("/")[-1],
                "uploaded_at": obj["LastModified"].timestamp()
            })

        files.sort(key=lambda x: x["uploaded_at"],reverse=True)

        return files
    
    def get_file_bytes(self, user_id:int, filename: str) -> bytes:
        key = self._key(user_id, filename)
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()

    def get_local_path(self, user_id:int, filename:str) -> Path | None:
        return None
    
    def file_exists(self, user_id:int, filename:str) -> bool:
        key = self._key(user_id, filename)
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False
    def get_usage_bytes(self, user_id:int) -> int:
        prefix = f"{S3_KEY_PREFIX}/{user_id}/"
        total = 0
        continuation_token = None

        while True:
            params = {
                "Bucket": self.bucket,
                "Prefix":prefix,
            }
            if continuation_token:
                params["ContinuationToken"] = continuation_token
            
            response = self.client.list_objects_v2(**params)

            for obj in response.get("Contents", []):
                key = obj["Key"]
                if not key.endswith("/"):
                    total += int(obj.get("Size", 0))

            if not response.get("IsTruncated"):
                break
            continuation_token = response.get("NextContinuationToken")
        return total
 
def get_storage_backend() -> StorageBackend:
    if STORAGE_BACKEND == "local":
        return LocalStorageBackend()
    elif STORAGE_BACKEND == "s3":
        return S3StorageBackend()
    else:
        raise ValueError(f"Invalid storage backend: {STORAGE_BACKEND}")
