import asyncio

from mymanah.body_limit import BodyLimitMiddleware


def test_chunked_oversize_is_rejected_before_parsing():
    async def run():
        messages = iter([{"type": "http.request", "body": b"x" * 20000, "more_body": True},
                         {"type": "http.request", "body": b"x" * 20000, "more_body": False}])
        output = []
        called = False

        async def receive():
            return next(messages)

        async def send(message):
            output.append(message)

        async def inner(scope, receive, send):
            nonlocal called
            called = True

        middleware = BodyLimitMiddleware(inner)
        await middleware({"type": "http", "method": "POST", "path": "/analyze-journal"}, receive, send)
        assert not called
        assert output[0]["status"] == 413
    asyncio.run(run())


def test_upload_disconnect_is_broadcast_after_body_replay():
    async def run():
        source = asyncio.Queue()
        await source.put({"type": "http.request", "body": b"pdf", "more_body": False})

        async def receive():
            return await source.get()

        async def inner(scope, replay, send):
            assert (await replay())["body"] == b"pdf"
            await source.put({"type": "http.disconnect"})
            await asyncio.wait_for(scope["state"]["client_disconnected"].wait(), 1)
            assert (await replay())["type"] == "http.disconnect"

        async def send(message):
            pass

        await BodyLimitMiddleware(inner)({"type": "http", "method": "POST", "path": "/documents"}, receive, send)
    asyncio.run(run())


def test_body_replay_preserves_all_bytes():
    async def run():
        source = iter([{"type": "http.request", "body": b"hello", "more_body": True},
                       {"type": "http.request", "body": b" world", "more_body": False}])
        received = []

        async def receive():
            return next(source)

        async def inner(scope, replay, send):
            received.extend([(await replay())["body"], (await replay())["body"]])

        async def send(message):
            pass

        await BodyLimitMiddleware(inner)({"type": "http", "method": "POST", "path": "/analyze-journal"}, receive, send)
        assert b"".join(received) == b"hello world"
    asyncio.run(run())
