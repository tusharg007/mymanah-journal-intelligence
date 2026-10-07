# Dependency Audit and Exposure Review

The raw pre-update and current `pip-audit` results are retained as JSON. This is a
point-in-time dependency review, not a guarantee against all vulnerabilities.
The audit service could not audit the CPU-specific Torch version because it is
distributed through the official PyTorch index rather than PyPI; this is an
explicit coverage gap, not a clean Torch audit.

Security fixes installed and hash-locked: Transformers 5.19.0, IDNA 3.20,
setuptools 84.0.0, Hugging Face Hub 1.33.0, and the matching tokenizer package.
No hosted-provider extras are installed. CPU Torch is explicitly pinned.

The post-update audit reports five advisory records in Chroma 1.5.9, including
one duplicate record, with no fix versions reported by the audit service.
These concern the Chroma HTTP server's collection endpoints, remote-code model
configuration, and server RBAC/tenant authorization. This application runs an
embedded PersistentClient, does not expose a Chroma server/collection-config API,
passes explicit locally computed embeddings with embedding_function=None, and
authorizes canonical document ownership in its own SQLite-backed API.

Those affected server paths are not exposed by the shipped profile. This is a
scoped mitigation, not an assertion that Chroma has no vulnerabilities. Do not
expose a Chroma HTTP service or accept user-selected model repositories without
revisiting these advisories. Keep OS/filesystem access to local model and data
directories restricted. Third-party PDF parsing remains an untrusted-input risk,
bounded by a subprocess, file/page/text limits, deadlines, and controlled errors.

Ollama cloud features are explicitly disabled for the native start profile.
Inference uses hash-checked local artifacts, offline Hugging Face settings, and
an HTTP client restricted to the loopback Ollama address.
