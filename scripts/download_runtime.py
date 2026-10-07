"""Resumable ranged download of the official pinned Ollama Windows archive."""
from __future__ import annotations

import hashlib
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
URL = "https://github.com/ollama/ollama/releases/download/v0.40.0/ollama-windows-amd64.zip"
SIZE = 1468064949
SHA = "3623e256762ca89bd6fa99b0cc4106401919ce9df926411673e632e3ea287bb5"
CHUNK = 64 * 1024**2


def main():
    target = ROOT / "artifacts" / "ollama-windows-amd64.zip"
    parts = ROOT / "artifacts" / "runtime-parts"
    parts.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size <= SIZE:
        with target.open("rb") as source:
            for index, offset in enumerate(range(0, target.stat().st_size, CHUNK)):
                count = min(CHUNK, target.stat().st_size - offset)
                part = parts / f"{index:03}.part"
                if not part.exists() or part.stat().st_size < count:
                    source.seek(offset)
                    part.write_bytes(source.read(count))

    def download(index):
        start = index * CHUNK
        end = min(SIZE, start + CHUNK) - 1
        part = parts / f"{index:03}.part"
        expected = end - start + 1
        for attempt in range(4):
            present = part.stat().st_size if part.exists() else 0
            if present == expected:
                return
            if present > expected:
                raise RuntimeError("Invalid partial archive size")
            try:
                with httpx.Client(follow_redirects=True, trust_env=False, timeout=httpx.Timeout(60, connect=15)) as client:
                    with client.stream("GET", URL, headers={"Range": f"bytes={start + present}-{end}", "Accept-Encoding": "identity"}) as response:
                        response.raise_for_status()
                        if response.status_code != 206 or not response.headers.get("content-range", "").startswith(f"bytes {start + present}-"):
                            raise RuntimeError("Release server did not honor the requested range")
                        with part.open("ab") as output:
                            for data in response.iter_bytes(1024 * 1024):
                                if output.tell() + len(data) > expected:
                                    raise RuntimeError("Release range exceeded expected size")
                                output.write(data)
                if part.stat().st_size != expected:
                    raise RuntimeError("Release range was incomplete")
                print(f"Verified transfer length for range {index}", flush=True)
                return
            except (httpx.HTTPError, OSError):
                if attempt == 3:
                    raise
                time.sleep(2**attempt)

    with ThreadPoolExecutor(max_workers=6) as executor:
        list(executor.map(download, range((SIZE + CHUNK - 1) // CHUNK)))
    temporary = target.with_suffix(".complete")
    digest = hashlib.sha256()
    with temporary.open("wb") as output:
        for index in range((SIZE + CHUNK - 1) // CHUNK):
            with (parts / f"{index:03}.part").open("rb") as part:
                for data in iter(lambda: part.read(1024 * 1024), b""):
                    output.write(data)
                    digest.update(data)
    if digest.hexdigest() != SHA:
        raise RuntimeError("Official runtime archive SHA-256 mismatch; archive not installed")
    os.replace(temporary, target)
    for part in parts.glob("*.part"):
        if not part.resolve().is_relative_to(parts.resolve()):
            raise RuntimeError("Unsafe cache path")
        part.unlink()
    print("Official Ollama runtime download hash verified", flush=True)


if __name__ == "__main__":
    main()
