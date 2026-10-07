"""Linux container startup smoke without mounted model weights or network access."""
from __future__ import annotations

import asyncio
import os

import chromadb
import httpx
import pypdf
import sentence_transformers
import torch
import transformers

from mymanah.api import create_app
from mymanah.config import ROOT


async def main():
    assert os.getuid() == 10001
    assert (ROOT / "model_manifest.json").is_file()
    assert (ROOT / "web/dist/index.html").is_file()
    (ROOT / "data/smoke").write_text("packaging check")
    app = create_app()
    async with app.router.lifespan_context(app):
        for _ in range(50):
            if app.state.models.failure != "MODELS_NOT_LOADED":
                break
            await asyncio.sleep(.1)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://127.0.0.1:8000") as client:
            assert (await client.get("/health/live")).status_code == 200
            ready = await client.get("/health/ready")
            assert ready.status_code == 503 and ready.json()["failure"] == "BOOTSTRAP_REQUIRED", ready.text
            assert (await client.get("/")).status_code == 200
    print("Linux non-root startup, manifest/static paths and missing-model fail-closed readiness passed.")
    print("Real dependency imports:", *(module.__name__ for module in
                                         (torch, transformers, sentence_transformers, chromadb, pypdf)))


if __name__ == "__main__":
    asyncio.run(main())
