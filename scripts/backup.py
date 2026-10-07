"""Quiesced local backup/restore with archive path validation."""
from __future__ import annotations

import argparse
import socket
import sqlite3
import zipfile
from pathlib import Path

from mymanah.config import Settings


def require_stopped(settings: Settings) -> None:
    with socket.socket() as probe:
        probe.settimeout(1)
        if probe.connect_ex(("127.0.0.1", settings.port)) == 0:
            raise RuntimeError("Stop the API before backup/restore; Chroma and SQLite must be quiesced")


def backup(source: Path, target: Path) -> None:
    if target.resolve().is_relative_to(source.resolve()):
        raise RuntimeError("Place backup archives outside the data directory")
    if not (source / "metadata.sqlite3").is_file():
        raise RuntimeError("Application data is missing")
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for file in source.rglob("*"):
            if file.is_symlink():
                raise RuntimeError("Symlinks are not allowed in application backups")
            if file.is_file() and "temporary" not in file.relative_to(source).parts:
                archive.write(file, file.relative_to(source).as_posix())


def restore(archive_path: Path, destination: Path) -> None:
    if destination.exists() and any(destination.iterdir()):
        raise RuntimeError("Restore only into an empty directory")
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    with zipfile.ZipFile(archive_path) as archive:
        if sum(member.file_size for member in archive.infolist()) > 2 * 1024**3:
            raise RuntimeError("Backup exceeds the supported restore size")
        if archive.testzip():
            raise RuntimeError("Backup archive failed integrity verification")
        for member in archive.infolist():
            target = (root / member.filename).resolve()
            if not target.is_relative_to(root) or "\\" in member.filename or ":" in member.filename or member.filename.startswith("/"):
                raise RuntimeError("Unsafe backup entry")
            if (member.external_attr >> 16) & 0o170000 == 0o120000:
                raise RuntimeError("Backup symlinks are prohibited")
        archive.extractall(root)
    database = root / "metadata.sqlite3"
    if not database.is_file():
        raise RuntimeError("Backup metadata database is missing")
    with sqlite3.connect(database) as db:
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("Restored database failed integrity verification")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["backup", "restore"])
    parser.add_argument("archive", type=Path)
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()
    settings = Settings.from_env()
    require_stopped(settings)
    if args.action == "backup":
        backup(settings.data_dir, args.archive)
    else:
        restore(args.archive, args.destination or settings.data_dir)
    print("Completed. After restore, start the API and run a real document question to verify index reuse.")
