"""Real API smoke run with non-loopback Python socket connections prohibited."""
from __future__ import annotations

import asyncio
import ipaddress
import json
import socket
import sys
import time
from dataclasses import replace

import httpx

from mymanah.api import create_app
from mymanah.config import ROOT, Settings
from tests.pdf_helpers import make_pdf


async def main():
    blocked = []

    def network_guard(event, args):
        if event != "socket.connect":
            return
        address = args[1]
        if not isinstance(address, tuple):
            return
        host = address[0]
        try:
            local = ipaddress.ip_address(host).is_loopback
        except ValueError:
            local = host == "localhost"
        if not local:
            blocked.append(str(host))
            raise PermissionError("Offline smoke prohibits non-loopback socket connections")

    sys.addaudithook(network_guard)
    try:
        socket.create_connection(("203.0.113.1", 443), timeout=1)
    except PermissionError:
        pass
    else:
        raise RuntimeError("External-network guard did not work")
    directory = ROOT / "tmp" / ("offline-" + str(time.time_ns()))
    settings = replace(Settings.from_env(), data_dir=directory, keys={})
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        started = time.monotonic()
        while not app.state.models.ready and time.monotonic() - started < 160:
            await asyncio.sleep(.5)
        app.state.models.require()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://127.0.0.1:8000", timeout=70) as client:
            journal = await client.post("/analyze-journal", json={"text": "Today I enjoyed lunch with my friend. I felt happy and relaxed afterward."})
            assert journal.status_code == 200, journal.text
            pdf = make_pdf(directory / "new-policy.pdf", ["Orchid staff receive 23 days of annual leave. Requests require the supervisor's approval."])
            with pdf.open("rb") as handle:
                upload = await client.post("/documents", files={"file": (pdf.name, handle, "application/pdf")})
            assert upload.status_code == 201 and upload.json()["status"] == "READY", upload.text
            doc = upload.json()["document"]["id"]
            answer = await client.post(f"/documents/{doc}/questions", json={"question": "How many days of annual leave do Orchid staff receive?"})
            assert answer.status_code == 200 and "23" in answer.json()["answer"], answer.text
            assert answer.json()["citations"], answer.text
            report = {"journal": journal.json(), "upload_status": upload.json()["status"], "answer": answer.json(),
                      "external_connections_blocked": blocked, "unexpected_external_attempts": blocked[1:],
                      "scope": "Python socket audit guard in the API/inference process; not an OS firewall. Local Ollama is allowed; PDF extraction subprocess is not audit-hook instrumented.",
                      "generator": settings.generator}
            (ROOT / "reports/offline-smoke.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
            assert len(blocked) == 1, "An application dependency attempted external access"
            print("Real journal and newly uploaded PDF passed with external Python socket connections blocked.")


if __name__ == "__main__":
    asyncio.run(main())
