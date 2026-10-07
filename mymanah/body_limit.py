from __future__ import annotations

import asyncio
import json
import time
import uuid


class BodyLimitMiddleware:
    """Bound multipart/JSON before parsers allocate or spool unbounded request bodies."""

    def __init__(self, app):
        self.app = app
        self.slots = asyncio.Semaphore(3)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] not in {"POST", "PUT", "PATCH"}:
            return await self.app(scope, receive, send)
        state = scope.setdefault("state", {})
        state["started"] = time.monotonic()
        state["request_id"] = uuid.uuid4().hex
        limit = 11 * 1024**2 if scope["path"] == "/documents" else 32 * 1024
        messages, size = [], 0

        async def reject(code, message, status):
            body = json.dumps({"error": {"code": code, "message": message, "requestId": state["request_id"]}}).encode()
            await send({"type": "http.response.start", "status": status,
                        "headers": [(b"content-type", b"application/json"), (b"cache-control", b"no-store")]})
            await send({"type": "http.response.body", "body": body})

        try:
            async with asyncio.timeout(60 if scope["path"] == "/documents" else 30):
                async with self.slots:
                    while True:
                        message = await receive()
                        if message["type"] == "http.disconnect":
                            return
                        size += len(message.get("body", b""))
                        if size > limit:
                            return await reject("BODY_TOO_LARGE", "Request body exceeds the limit", 413)
                        messages.append(message)
                        if not message.get("more_body", False):
                            break
        except TimeoutError:
            return await reject("BODY_TIMEOUT", "Request body upload timed out", 504)
        position = 0
        disconnected = asyncio.Event() if scope["path"] == "/documents" else None
        if disconnected:
            state["client_disconnected"] = disconnected

        async def watch_disconnect():
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    disconnected.set()
                    return

        async def replay():
            nonlocal position
            if position < len(messages):
                message = messages[position]
                position += 1
                return message
            if disconnected:
                await disconnected.wait()
                return {"type": "http.disconnect"}
            return await receive()

        watcher = asyncio.create_task(watch_disconnect()) if disconnected else None
        try:
            await self.app(scope, replay, send)
        finally:
            if watcher:
                watcher.cancel()
                await asyncio.gather(watcher, return_exceptions=True)
