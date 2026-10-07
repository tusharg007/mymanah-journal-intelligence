from __future__ import annotations

import json
import shutil

import httpx

from mymanah.config import Settings
from mymanah.models import Models


def main():
    settings = Settings.from_env()
    model = Models(settings)
    checks = {"pythonEnvironment": True, "ollamaExecutable": bool(shutil.which("ollama")),
              "loopback": settings.host in {"127.0.0.1", "::1"}, "authEnabled": settings.auth_enabled}
    try:
        model.verify_files()
        checks["artifactChecksums"] = True
    except Exception as exc:
        checks["artifactChecksums"] = False
        checks["artifactFailure"] = getattr(exc, "code", type(exc).__name__)
    try:
        response = httpx.get(settings.ollama_url + "/api/version", timeout=3, trust_env=False)
        response.raise_for_status()
        checks["ollamaRuntime"] = response.json()
    except httpx.HTTPError:
        checks["ollamaRuntime"] = False
    print(json.dumps(checks, indent=2))
    if not checks["artifactChecksums"] or not checks["ollamaRuntime"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
