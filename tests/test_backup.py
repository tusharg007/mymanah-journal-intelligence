import socket
import sqlite3
import zipfile
from dataclasses import replace

import pytest

from mymanah.config import Settings
from scripts.backup import backup, require_stopped, restore


def test_backup_restore_and_temporary_exclusion(tmp_path):
    source = tmp_path / "data"
    source.mkdir()
    with sqlite3.connect(source / "metadata.sqlite3") as db:
        db.execute("CREATE TABLE evidence (value TEXT)")
        db.execute("INSERT INTO evidence VALUES ('preserved')")
    (source / "raw.pdf").write_bytes(b"pdf-fixture")
    (source / "temporary").mkdir()
    (source / "temporary" / "upload.part").write_bytes(b"incomplete")
    archive = tmp_path / "snapshot.zip"
    backup(source, archive)
    destination = tmp_path / "restored"
    restore(archive, destination)
    assert (destination / "raw.pdf").read_bytes() == b"pdf-fixture"
    assert not (destination / "temporary").exists()
    with sqlite3.connect(destination / "metadata.sqlite3") as db:
        assert db.execute("SELECT value FROM evidence").fetchone() == ("preserved",)
    with pytest.raises(RuntimeError, match="empty"):
        restore(archive, destination)
    with pytest.raises(RuntimeError, match="outside"):
        backup(source, source / "recursive.zip")


@pytest.mark.parametrize("name", ["../escape", "/absolute", "..\\escape", "file:stream"])
def test_restore_rejects_unsafe_paths_before_extracting(tmp_path, name):
    archive = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("harmless.txt", "must not extract")
        entry = zipfile.ZipInfo("unsafe-entry")
        entry.filename = name
        handle.writestr(entry, "unsafe")
    destination = tmp_path / "restored"
    with pytest.raises(RuntimeError, match="Unsafe"):
        restore(archive, destination)
    assert list(destination.iterdir()) == []


def test_backup_requires_quiesced_api():
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen()
        settings = replace(Settings(), port=server.getsockname()[1])
        with pytest.raises(RuntimeError, match="Stop the API"):
            require_stopped(settings)
