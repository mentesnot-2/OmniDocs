from pathlib import Path

import pytest

from api.services.storage_backend import (
    LocalStorageBackend,
    S3StorageBackend,
    build_version_storage_key,
)


@pytest.fixture()
def local_storage(tmp_path, monkeypatch):
    import api.services.storage_backend as storage_module

    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(storage_module, "UPLOAD_DIR", upload_dir)
    return LocalStorageBackend()


def test_local_storage_list_delete_usage(local_storage):
    user_id = 42
    local_storage.save_file(user_id, "demo.txt", b"hello world")

    files = local_storage.list_files(user_id)
    assert len(files) == 1
    assert files[0]["filename"] == "demo.txt"
    assert local_storage.get_usage_bytes(user_id) > 0

    local_storage.delete_file(user_id, "demo.txt")
    assert local_storage.file_exists(user_id, "demo.txt") is False
    assert local_storage.list_files(user_id) == []


def test_local_storage_versioned_keys(local_storage):
    key_v1 = build_version_storage_key(7, 10, 1, "report.txt")
    key_v2 = build_version_storage_key(7, 10, 2, "report.txt")
    assert key_v1 != key_v2

    local_storage.save_fileobj_by_key(key_v1, _bytes_io(b"version one"))
    local_storage.save_fileobj_by_key(key_v2, _bytes_io(b"version two"))

    assert local_storage.get_bytes_by_key(key_v1) == b"version one"
    assert local_storage.get_bytes_by_key(key_v2) == b"version two"
    local_storage.delete_keys([key_v1, key_v2])
    assert local_storage.key_exists(key_v1) is False


def test_s3_storage_backend_with_moto(monkeypatch):
    pytest.importorskip("moto")
    from moto import mock_aws

    import api.services.storage_backend as storage_module

    monkeypatch.setattr(storage_module, "S3_BUCKET_NAME", "omnidocs-test")
    monkeypatch.setattr(storage_module, "S3_REGION", "us-east-1")
    monkeypatch.setattr(storage_module, "STORAGE_BACKEND", "s3")

    with mock_aws():
        backend = S3StorageBackend()
        key = build_version_storage_key(1, 2, 1, "notes.txt")
        backend.save_fileobj_by_key(key, _bytes_io(b"s3 content"))
        assert backend.key_exists(key)
        assert backend.get_bytes_by_key(key) == b"s3 content"
        backend.delete_by_key(key)
        assert backend.key_exists(key) is False


def _bytes_io(content: bytes):
    import io

    return io.BytesIO(content)
