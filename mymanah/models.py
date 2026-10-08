from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import threading
import time
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from .config import ROOT, Settings
from .errors import ServiceError
from .schemas import SummaryDraft
from .text import windows

T = TypeVar("T", bound=BaseModel)


class Models:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.manifest = json.loads((ROOT / "model_manifest.json").read_text())
        self.generator = self.manifest["generators"][settings.generator]
        self.ready = False
        self.failure = "MODELS_NOT_LOADED"
        self.cpu_lock = threading.RLock()
        self.http = httpx.AsyncClient(base_url=settings.ollama_url, trust_env=False,
                                     timeout=httpx.Timeout(40, connect=3), follow_redirects=False)

    def verify_files(self) -> None:
        lock_file = self.settings.model_dir / "artifacts.lock.json"
        if not lock_file.exists():
            raise ServiceError("BOOTSTRAP_REQUIRED", "Run the explicit model bootstrap first")
        lock = json.loads(lock_file.read_text())
        roles = ["sentiment", "nli", "embedding", self.settings.generator, self.settings.generator + "_tokenizer"]
        for role in roles:
            record = lock.get(role)
            if not record or not record.get("files"):
                raise ServiceError("ARTIFACT_MISSING", "Required model artifacts are missing")
            if role.endswith("_tokenizer"):
                directory = self.settings.model_dir / self.settings.generator / "tokenizer"
                expected_revision = self.generator["tokenizer_revision"]
            else:
                directory = self.settings.model_dir / role
                spec = self.generator if role == self.settings.generator else self.manifest[role]
                expected_revision = spec["revision"]
                weight = spec.get("weight", spec.get("file"))
                if record["files"].get(weight) != spec["sha256"]:
                    raise ServiceError("ARTIFACT_MISMATCH", "Weight hash does not match the approved manifest")
            if record["revision"] != expected_revision:
                raise ServiceError("ARTIFACT_MISMATCH", "Model revision does not match the manifest")
            for name, expected in record["files"].items():
                file = directory / name
                if not file.is_file():
                    raise ServiceError("ARTIFACT_MISSING", "A required artifact is missing")
                digest = hashlib.sha256()
                with file.open("rb") as handle:
                    for block in iter(lambda: handle.read(1024 * 1024), b""):
                        digest.update(block)
                if digest.hexdigest() != expected:
                    raise ServiceError("ARTIFACT_CORRUPT", "A local model artifact failed checksum verification")

    def load_cpu(self) -> None:
        self.verify_files()
        os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1")
        import torch
        from sentence_transformers import SentenceTransformer
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self.torch = torch
        torch.set_num_threads(self.settings.torch_threads)
        self.sent_tokenizer = AutoTokenizer.from_pretrained(self.settings.model_dir / "sentiment", local_files_only=True)
        self.sentiment = AutoModelForSequenceClassification.from_pretrained(
            self.settings.model_dir / "sentiment", local_files_only=True
        ).eval()
        self.nli_tokenizer = AutoTokenizer.from_pretrained(self.settings.model_dir / "nli", local_files_only=True)
        self.nli = AutoModelForSequenceClassification.from_pretrained(
            self.settings.model_dir / "nli", local_files_only=True, dtype=torch.float32
        ).eval()
        labels = {int(i): str(v).lower() for i, v in self.nli.config.id2label.items()}
        self.entailment = next(i for i, label in labels.items() if label == "entailment")
        self.sent_labels = {int(i): str(v).lower() for i, v in self.sentiment.config.id2label.items()}
        if set(self.sent_labels.values()) != {"negative", "neutral", "positive"}:
            raise ServiceError("MODEL_LABELS_INVALID", "Sentiment label mapping is incompatible")
        self.embedding = SentenceTransformer(str(self.settings.model_dir / "embedding"), device="cpu", local_files_only=True)
        self.gen_tokenizer = AutoTokenizer.from_pretrained(
            self.settings.model_dir / self.settings.generator / "tokenizer", local_files_only=True
        )
        self.sentiment_scores("The project is complete.")
        self.support([("The project is complete.", "The project has finished.")])
        self.embed(["warmup"], query=True)

    async def load(self) -> None:
        try:
            await asyncio.to_thread(self.load_cpu)
            response = await self.http.post("/api/show", json={"model": self.generator["ollama_model"]})
            response.raise_for_status()
            if self.generator["sha256"] not in response.json().get("modelfile", ""):
                raise ServiceError("OLLAMA_ARTIFACT_MISMATCH", "Ollama model does not match the locked GGUF")
            # Empty prompts load weights but do not initialize the first decoding graph.
            response = await self.http.post("/api/generate", json={"model": self.generator["ollama_model"],
                                           "prompt": "Return a JSON summary of: The project is complete.",
                                           "format": SummaryDraft.model_json_schema(),
                                           "options": {"num_predict": 1, "num_ctx": 4096, "temperature": 0},
                                           "stream": False, "keep_alive": "30m"}, timeout=120)
            response.raise_for_status()
            self.ready, self.failure = True, ""
        except Exception as exc:
            logging.getLogger(__name__).exception("Local model initialization failed")
            self.failure = exc.code if isinstance(exc, ServiceError) else type(exc).__name__
            self.ready = False

    def require(self) -> None:
        if not self.ready:
            raise ServiceError("MODELS_UNAVAILABLE", "Required local models are not ready; check /health/ready")

    def token_count(self, text: str) -> int:
        return len(self.gen_tokenizer.encode(text, add_special_tokens=False))

    @staticmethod
    def check_deadline(deadline: float | None) -> None:
        if deadline is not None and time.monotonic() >= deadline:
            raise ServiceError("INFERENCE_TIMEOUT", "Inference deadline exhausted", 504)

    def sentiment_scores(self, text: str, deadline: float | None = None) -> dict[str, float]:
        with self.cpu_lock, self.torch.inference_mode():
            self.check_deadline(deadline)
            pieces = windows(text, self.sent_tokenizer)
            inputs = self.sent_tokenizer([p.text for p in pieces], padding=True, truncation=False, return_tensors="pt")
            if inputs["input_ids"].shape[1] > 512:
                raise ServiceError("TOKEN_LIMIT", "Sentiment window exceeds model capacity", 413)
            probs = self.sentiment(**inputs).logits.softmax(-1).cpu().numpy()
            total = sum(p.weight for p in pieces)
            return {label: float(sum(probs[j, i] * p.weight for j, p in enumerate(pieces)) / total)
                    for i, label in self.sent_labels.items()}

    def support(self, pairs: list[tuple[str, str]], deadline: float | None = None) -> list[float]:
        results = []
        with self.cpu_lock, self.torch.inference_mode():
            start = 0
            while start < len(pairs):
                self.check_deadline(deadline)
                batch = pairs[start:start + 8]
                inputs = self.nli_tokenizer([p for p, _ in batch], [h for _, h in batch], padding=True,
                                            truncation=False, return_tensors="pt")
                if inputs["input_ids"].shape[1] > 512:
                    raise ServiceError("TOKEN_LIMIT", "Evidence pair exceeds NLI capacity", 413)
                # Bound long-window attention memory while retaining eight-row short batches.
                batch_size = max(1, min(len(batch), 1024 // inputs["input_ids"].shape[1]))
                if batch_size < len(batch):
                    inputs = {key: value[:batch_size] for key, value in inputs.items()}
                logits = self.nli(**inputs).logits
                results.extend(logits.softmax(-1)[:, self.entailment].cpu().tolist())
                start += batch_size
        return results

    def embed(self, texts: list[str], query: bool = False) -> list[list[float]]:
        prefix = "query: " if query else "passage: "
        with self.cpu_lock:
            encoded = self.embedding.encode([prefix + t for t in texts], batch_size=16,
                                             normalize_embeddings=True, show_progress_bar=False)
        return encoded.tolist()

    async def generate(self, system: str, prompt: str, schema: type[T], tokens: int = 256,
                       deadline: float | None = None, source_quotes: list[str] | None = None) -> T:
        remaining = min(40.0, deadline - time.monotonic()) if deadline else 40.0
        if remaining <= 0:
            raise ServiceError("INFERENCE_TIMEOUT", "Inference deadline exhausted", 504)
        output_schema = schema.model_json_schema()
        constrained_schema = schema.model_json_schema()
        if source_quotes:
            constrained_schema["$defs"]["SummarySentence"]["properties"]["quote"]["enum"] = source_quotes
        try:
            async with asyncio.timeout(remaining):
                response = await self.http.post("/api/generate", json={
                    "model": self.generator["ollama_model"], "system": system,
                    "prompt": json.dumps({"output_schema": output_schema, "input": json.loads(prompt)}),
                    "format": constrained_schema, "stream": False, "keep_alive": "30m",
                    "options": {"temperature": 0, "seed": 42, "num_ctx": 4096, "num_predict": tokens},
                })
            response.raise_for_status()
            payload = response.json()
            if not payload.get("done") or payload.get("done_reason") == "length":
                raise ServiceError("GENERATION_INCOMPLETE", "Local generation did not complete")
            return schema.model_validate_json(payload["response"])
        except TimeoutError as exc:
            raise ServiceError("INFERENCE_TIMEOUT", "Inference deadline exhausted", 504) from exc
        except (httpx.HTTPError, KeyError, ValueError, ValidationError) as exc:
            raise ServiceError("GENERATION_FAILED", "Local generation failed or returned invalid structured output") from exc

    async def close(self) -> None:
        await self.http.aclose()
