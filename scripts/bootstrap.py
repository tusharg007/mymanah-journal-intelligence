"""Explicit network-enabled download, checksum verification and local Ollama import."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def snapshot(repo: str, revision: str, target: Path, weight: str | None = None) -> dict:
    info = HfApi().model_info(repo, revision=revision, files_metadata=True)
    if info.sha != revision:
        raise RuntimeError("Hub did not resolve the locked revision")
    allowed = {"config.json", "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json",
               "added_tokens.json", "vocab.json", "merges.txt", "spm.model", "sentencepiece.bpe.model",
               "modules.json", "sentence_bert_config.json", "1_Pooling/config.json", "README.md"}
    if weight:
        allowed.add(weight)
    records = {}
    for sibling in info.siblings:
        name = sibling.rfilename
        if name not in allowed:
            continue
        file = Path(hf_hub_download(repo, name, revision=revision, local_dir=target))
        digest = sha256(file)
        if sibling.lfs and digest != sibling.lfs.sha256:
            raise RuntimeError(f"Checksum mismatch: {repo}/{name}")
        if not sibling.lfs and sibling.blob_id:
            content = file.read_bytes()
            git_hash = hashlib.sha1(f"blob {len(content)}\0".encode() + content).hexdigest()
            if git_hash != sibling.blob_id:
                raise RuntimeError(f"Git blob mismatch: {repo}/{name}")
        records[name] = digest
    return {"repo": repo, "revision": revision, "files": records}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", choices=["qwen4b", "qwen1b"], default="qwen4b")
    parser.add_argument("--all-generators", action="store_true")
    parser.add_argument("--skip-import", action="store_true")
    parser.add_argument("--model-dir", type=Path, default=ROOT / "models")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "model_manifest.json").read_text())
    directory = args.model_dir.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    lock_path = directory / "artifacts.lock.json"
    lock = json.loads(lock_path.read_text()) if lock_path.exists() else {}

    def checkpoint():
        temporary = lock_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(lock, indent=2), encoding="utf-8")
        os.replace(temporary, lock_path)

    for role in ("sentiment", "nli", "embedding"):
        spec = manifest[role]
        print(f"Downloading/verifying {role}: {spec['repo']}", flush=True)
        record = snapshot(spec["repo"], spec["revision"], directory / role, spec["weight"])
        if record["files"].get(spec["weight"]) != spec["sha256"]:
            raise RuntimeError(f"Locked weight mismatch for {role}")
        lock[role] = record
        checkpoint()
    names = list(manifest["generators"]) if args.all_generators else [args.generator]
    for name in names:
        spec = manifest["generators"][name]
        target = directory / name
        print(f"Downloading/verifying {name}", flush=True)
        file = Path(hf_hub_download(spec["repo"], spec["file"], revision=spec["revision"], local_dir=target))
        if sha256(file) != spec["sha256"]:
            raise RuntimeError(f"Locked GGUF mismatch for {name}")
        lock[name] = {"repo": spec["repo"], "revision": spec["revision"], "files": {spec["file"]: spec["sha256"]}}
        lock[name + "_tokenizer"] = snapshot(
            spec["tokenizer_repo"], spec["tokenizer_revision"], target / "tokenizer"
        )
        checkpoint()
        modelfile = target / "Modelfile"
        modelfile.write_text(f'FROM "{file.resolve().as_posix()}"\nPARAMETER num_ctx 4096\nPARAMETER temperature 0\n', encoding="utf-8")
        (target / "Modelfile.container").write_text(
            f'FROM /models/{name}/{spec["file"]}\nPARAMETER num_ctx 4096\nPARAMETER temperature 0\n', encoding="utf-8"
        )
        if not args.skip_import:
            subprocess.run(["ollama", "create", spec["ollama_model"], "-f", str(modelfile)], check=True)
    temporary = lock_path.with_suffix(".tmp")
    temporary.write_text(json.dumps(lock, indent=2), encoding="utf-8")
    os.replace(temporary, lock_path)
    print("Bootstrap complete. Artifacts are hash-checked; runtime does not download models.", flush=True)


if __name__ == "__main__":
    main()
