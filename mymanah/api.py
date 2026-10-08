from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .admission import Admission
from .body_limit import BodyLimitMiddleware
from .config import ROOT, Settings
from .documents import Documents
from .errors import ServiceError
from .journal import JournalService
from .models import Models
from .policy import POLICY_VERSION
from .rag import RAG
from .schemas import AnswerResponse, JournalRequest, JournalResponse, QuestionRequest
from .storage import Storage, public_document

logger = logging.getLogger("mymanah")


def create_app(settings: Settings | None = None, model_factory=Models, document_factory=Documents) -> FastAPI:
    settings = settings or Settings.from_env()
    tasks: set[asyncio.Task] = set()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        app.state.settings = settings
        app.state.storage = Storage(settings.data_dir / "metadata.sqlite3", settings.global_disk_bytes)
        app.state.models = model_factory(settings)
        app.state.documents = document_factory(settings, app.state.storage, app.state.models)
        await asyncio.to_thread(app.state.documents.recover)
        app.state.journal = JournalService(app.state.models)
        app.state.rag = RAG(app.state.documents, app.state.storage, app.state.models)
        app.state.admission = Admission()
        load = asyncio.create_task(app.state.models.load())
        yield
        if not load.done():
            await load
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        pending = [flight.task for flight in app.state.documents.flights.values() if flight.task]
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
        await app.state.models.close()

    app = FastAPI(title="MyManah Journal Intelligence", version="0.1.0", lifespan=lifespan)

    @app.middleware("http")
    async def metadata(request: Request, call_next):
        request.state.request_id = getattr(request.state, "request_id", uuid.uuid4().hex)
        request.state.started = getattr(request.state, "started", time.monotonic())
        size = request.headers.get("content-length")
        limit = 11 * 1024**2 if request.url.path == "/documents" else 32 * 1024
        if size:
            try:
                if int(size) < 0 or int(size) > limit:
                    return error(request, "BODY_TOO_LARGE", "Request body exceeds the limit", 413)
            except ValueError:
                return error(request, "INVALID_CONTENT_LENGTH", "Invalid content length", 400)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Analysis-Version"] = POLICY_VERSION
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        logger.info("request id=%s method=%s status=%s elapsed_ms=%.1f", request.state.request_id,
                    request.method, response.status_code, (time.monotonic() - request.state.started) * 1000)
        return response

    def error(request: Request, code: str, message: str, status: int, fields=None):
        content = {"error": {"code": code, "message": message, "requestId": getattr(request.state, "request_id", "")}}
        if fields:
            content["error"]["fields"] = fields
        return JSONResponse(content, status_code=status)

    @app.exception_handler(ServiceError)
    async def service_error(request: Request, exc: ServiceError):
        return error(request, exc.code, exc.message, exc.status)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        fields = [{"field": ".".join(str(x) for x in issue["loc"]), "code": issue["type"]} for issue in exc.errors()]
        return error(request, "INVALID_REQUEST", "Request failed validation", 422, fields)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        return error(request, "HTTP_ERROR", "Request could not be completed", exc.status_code)

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        logger.error("request_failed id=%s type=%s", getattr(request.state, "request_id", ""), type(exc).__name__)
        return error(request, "INTERNAL_ERROR", "The service could not complete this request", 503)

    def principal(request: Request) -> str:
        if not settings.auth_enabled:
            return "local"
        scheme, _, token = request.headers.get("authorization", "").partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise ServiceError("AUTH_REQUIRED", "A valid bearer API key is required", 401)
        digest = hashlib.sha256(token.encode()).hexdigest()
        selected = None
        for name, expected in settings.keys.items():
            if hmac.compare_digest(digest, expected):
                selected = name
        if selected is None:
            raise ServiceError("AUTH_INVALID", "A valid bearer API key is required", 401)
        return selected

    async def interactive(request: Request, owner: str, action, deadline: float):
        request.app.state.models.require()
        admission = request.app.state.admission
        admission.rate(owner, "interactive", 10)

        async def work():
            async with admission.enter(deadline=deadline):
                return await action()

        task = asyncio.create_task(work())
        tasks.add(task)

        def finished(done):
            tasks.discard(done)
            if not done.cancelled():
                done.exception()

        task.add_done_callback(finished)
        try:
            return await asyncio.wait_for(asyncio.shield(task), max(0.001, deadline - time.monotonic()))
        except TimeoutError as exc:
            # Shielding keeps capacity occupied until actual model execution stops.
            raise ServiceError("INFERENCE_TIMEOUT", "The request exceeded its inference deadline", 504) from exc

    @app.get("/health/live")
    async def live():
        return {"status": "alive"}

    ready_cache = {"checked": 0.0, "ok": False}

    @app.get("/health/ready")
    async def ready(request: Request):
        models = request.app.state.models
        available = models.ready
        if available and time.monotonic() - ready_cache["checked"] > 5:
            try:
                with request.app.state.storage.connect() as db:
                    db.execute("SELECT 1")
                if not settings.data_dir.is_dir():
                    raise OSError("Storage unavailable")
                response = await models.http.get("/api/version", timeout=2)
                response.raise_for_status()
                ready_cache.update(checked=time.monotonic(), ok=True)
            except Exception:
                ready_cache.update(checked=time.monotonic(), ok=False)
        available = available and ready_cache["ok"]
        status = {"status": "ready" if available else "not_ready", "authEnabled": settings.auth_enabled,
                  "language": "English", "failure": models.failure or None}
        return JSONResponse(status, status_code=200 if available else 503)

    @app.post("/analyze-journal", response_model=JournalResponse)
    async def analyze(body: JournalRequest, request: Request, owner: str = Depends(principal)):
        length = request.app.state.journal.validate(body.text)
        budget = 30 if length <= 256 else 60
        deadline = request.state.started + budget
        return await interactive(request, owner, lambda: request.app.state.journal.analyze(body.text, deadline), deadline)

    @app.post("/documents")
    async def upload(request: Request, file: UploadFile = File(...), owner: str = Depends(principal)):
        request.app.state.models.require()
        request.app.state.admission.rate(owner, "upload", 2)
        filename = (file.filename or "document.pdf").replace("\\", "/").split("/")[-1]
        filename = "".join(c for c in filename if c.isprintable())[:180]
        if not filename.lower().endswith(".pdf"):
            raise ServiceError("UNSUPPORTED_MEDIA", "Upload a PDF file", 415)
        directory = settings.data_dir / "temporary"
        directory.mkdir(exist_ok=True)
        path = directory / (uuid.uuid4().hex + ".upload")
        digest, size, signature = hashlib.sha256(), 0, b""
        handed_off = False
        try:
            with path.open("wb") as output:
                while data := await file.read(64 * 1024):
                    if not signature:
                        signature = data[:1024]
                    size += len(data)
                    if size > 10 * 1024**2:
                        raise ServiceError("PDF_TOO_LARGE", "PDF exceeds 10 MiB", 413)
                    digest.update(data)
                    output.write(data)
            if not signature.lstrip().startswith(b"%PDF-"):
                raise ServiceError("INVALID_PDF_SIGNATURE", "The file does not have a PDF signature", 415)
            handed_off = True
            ingestion = asyncio.create_task(request.app.state.documents.upload(
                path, owner, filename, digest.hexdigest(), request.state.started + 60
            ))
            disconnected = getattr(request.state, "client_disconnected", None)
            watcher = asyncio.create_task(disconnected.wait()) if disconnected else None
            try:
                if watcher:
                    done, _ = await asyncio.wait({ingestion, watcher}, return_when=asyncio.FIRST_COMPLETED)
                    if watcher in done and not ingestion.done():
                        ingestion.cancel()
                document, created = await ingestion
            finally:
                if not ingestion.done():
                    ingestion.cancel()
                if watcher:
                    watcher.cancel()
                    await asyncio.gather(watcher, return_exceptions=True)
                await asyncio.gather(ingestion, return_exceptions=True)
            return JSONResponse({"document": public_document(document), "status": "READY"}, status_code=201 if created else 200)
        finally:
            await file.close()
            # The ingest worker owns the file once admitted, including after timeout.
            if not handed_off:
                path.unlink(missing_ok=True)

    @app.get("/documents")
    async def list_documents(request: Request, owner: str = Depends(principal)):
        return {"documents": [public_document(d) for d in request.app.state.storage.list(owner)]}

    @app.get("/documents/{document_id}")
    async def get_document(document_id: str, request: Request, owner: str = Depends(principal)):
        return public_document(request.app.state.storage.get(document_id, owner))

    @app.get("/documents/{document_id}/file")
    async def pdf_file(document_id: str, request: Request, owner: str = Depends(principal)):
        document = request.app.state.storage.get(document_id, owner, ready=True)
        return FileResponse(settings.data_dir / "uploads" / (document["id"] + ".pdf"), media_type="application/pdf", filename=document["filename"], content_disposition_type="inline")

    @app.post("/documents/{document_id}/questions", response_model=AnswerResponse)
    async def question(document_id: str, body: QuestionRequest, request: Request, owner: str = Depends(principal)):
        # Resolve authorization before model admission to avoid information leakage.
        request.app.state.storage.get(document_id, owner, ready=True)
        deadline = request.state.started + 45
        return await interactive(request, owner,
                                 lambda: request.app.state.rag.answer(document_id, owner, body.question, deadline), deadline)

    @app.delete("/documents/{document_id}", status_code=204)
    async def delete_document(document_id: str, request: Request, owner: str = Depends(principal)):
        await asyncio.to_thread(request.app.state.documents.delete, document_id, owner)

    dist = ROOT / "web" / "dist"
    if dist.exists():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")
        if (dist / "pdfjs").exists():
            app.mount("/pdfjs", StaticFiles(directory=dist / "pdfjs"), name="pdfjs")

        @app.get("/", include_in_schema=False)
        async def index():
            return FileResponse(dist / "index.html")

    if settings.host in {"127.0.0.1", "::1"}:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "::1", "[::1]"], www_redirect=False)
    app.add_middleware(BodyLimitMiddleware)
    return app
