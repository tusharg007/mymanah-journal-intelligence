from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    host: str = "127.0.0.1"
    port: int = 8000
    data_dir: Path = ROOT / "data"
    model_dir: Path = ROOT / "models"
    ollama_url: str = "http://127.0.0.1:11434"
    generator: str = "qwen4b"
    torch_threads: int = 4
    global_disk_bytes: int = 2048 * 1024 * 1024
    keys: dict[str, str] = field(default_factory=dict, repr=False)

    @property
    def auth_enabled(self) -> bool:
        return bool(self.keys)

    @classmethod
    def from_env(cls) -> Settings:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env", override=False)
        keys: dict[str, str] = {}
        if "API_KEYS" in os.environ:
            value = os.environ["API_KEYS"]
            if not value.strip():
                raise ValueError("API_KEYS must be unset or contain named random keys")
            for item in value.split(","):
                name, sep, key = item.partition(":")
                if not sep or not name.isidentifier() or len(key) < 32 or name in keys:
                    raise ValueError("Invalid API_KEYS configuration")
                if not all(c.isalnum() or c in "_-" for c in key):
                    raise ValueError("API keys must use URL-safe characters")
                digest = hashlib.sha256(key.encode()).hexdigest()
                if digest in keys.values():
                    raise ValueError("API keys must be unique")
                keys[name] = digest
        host = os.getenv("HOST", "127.0.0.1")
        if not keys and host not in {"127.0.0.1", "::1"}:
            raise ValueError("Open mode may bind only to loopback; configure API_KEYS for remote binding")
        url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
        parsed = urlparse(url)
        if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "::1", "localhost"}:
            raise ValueError("OLLAMA_URL must reference the local loopback runtime")
        if parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
            raise ValueError("Invalid local Ollama URL")
        generator = os.getenv("GENERATOR", "qwen4b")
        if generator not in {"qwen4b", "qwen1b"}:
            raise ValueError("GENERATOR must select a locked local artifact")
        return cls(
            host=host, port=int(os.getenv("PORT", "8000")),
            data_dir=Path(os.getenv("DATA_DIR", str(ROOT / "data"))).resolve(),
            model_dir=Path(os.getenv("MODEL_DIR", str(ROOT / "models"))).resolve(),
            ollama_url=url, generator=generator, keys=keys,
            torch_threads=max(1, min(8, int(os.getenv("TORCH_THREADS", "4")))),
            global_disk_bytes=int(os.getenv("GLOBAL_DISK_MIB", "2048")) * 1024 * 1024,
        )
