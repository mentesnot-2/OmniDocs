from pathlib import Path

import pytest

from api.services.storage_backend import LocalStorageBackend


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
