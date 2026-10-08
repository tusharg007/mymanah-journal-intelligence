"""Run reviewer HTTP, PDF, ownership and restart cases using actual local models."""
from __future__ import annotations

import concurrent.futures
import hashlib
import json
import os
import secrets
import subprocess
import sys
import time
from collections import deque
from pathlib import Path

import httpx
import psutil
from pypdf import PdfReader, PdfWriter

from mymanah.schemas import JournalResponse
from mymanah.text import sentence_count

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "artifacts/reviewer-pack"
FIXTURES = ROOT / "evals/fixtures/reviewer"
URL = "http://127.0.0.1:8000"
REPORT = ROOT / "reports/reviewer-protocol.json"
FACTS = {
    "R1": ["24"], "R2": ["5", "31", "march"], "R3": ["10", "3", "certificate"],
    "R4": ["26"], "R5": ["60"], "R6": ["3", "month"], "R7": ["15"],
    "R8": ["2", "week", "approv"], "R9": ["9:00", "18:00", "monday", "friday"],
    "R10": ["30", "500", "receipt"], "R11": ["24", "3", "month"], "R12": ["10"],
    "R17": ["24"], "R18": ["15", "director"], "R19": ["last working day"],
}


class Run:
    def __init__(self):
        WORK.mkdir(parents=True, exist_ok=True)
        self.pack = json.loads((ROOT / "evals/reviewer-test-pack.json").read_text(encoding="utf-8"))
        self.cases = {row["id"]: row for row in self.pack["cases"]}
        self.report = {"source_sha256": self.pack["source_sha256"], "fixtures": self.pack["fixtures"], "cases": []}
        self.client = httpx.Client(base_url=URL, timeout=75, trust_env=False)
        self.history = {"interactive": deque(), "upload": deque()}
        self.replaced_server = False
        self.headers = {}
        self.handbook = ""
        self.created = set()

    def record(self, case_id, observations, checks, note="", conflict=False):
        row = {"id": case_id, "expected": self.cases[case_id], "observations": observations,
               "checks": checks, "outcome": "PASS" if all(checks.values()) else "EXPECTATION_CONFLICT" if conflict else "MISMATCH"}
        if note:
            row["note"] = note
        self.report["cases"].append(row)
        REPORT.write_text(json.dumps(self.report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{case_id}: {row['outcome']} {checks}", flush=True)

    def pace(self, kind, count=1):
        history = self.history[kind]
        limit = 2 if kind == "upload" else 10
        while True:
            now = time.monotonic()
            while history and now - history[0] >= 60.2:
                history.popleft()
            if len(history) + count <= limit:
                history.extend([now] * count)
                return
            time.sleep(min(1, max(.01, 60.2 - (now - history[0]))))

    def request(self, method, path, *, kind=None, **kwargs):
        if kind:
            self.pace(kind)
        started = time.monotonic()
        response = self.client.request(method, path, headers=kwargs.pop("headers", self.headers), **kwargs)
        elapsed = round(time.monotonic() - started, 3)
        try:
            body = response.json()
        except ValueError:
            body = {"bytes": len(response.content), "sha256": hashlib.sha256(response.content).hexdigest()}
        return {"status_code": response.status_code, "seconds": elapsed, "body": body}

    def upload(self, name, data=None):
        payload = data if data is not None else (FIXTURES / name).read_bytes()
        row = self.request("POST", "/documents", kind="upload", files={"file": (name, payload, "application/pdf")})
        if row["status_code"] in {200, 201}:
            self.created.add(row["body"]["document"]["id"])
        return row

    def ask(self, question, document_id=None):
        return self.request("POST", f"/documents/{document_id or self.handbook}/questions",
                            kind="interactive", json={"question": question})

    def quote_checks(self, result, document_id, filename):
        pages = [" ".join(page.extract_text().split()) for page in PdfReader(FIXTURES / filename).pages]
        citations = result.get("citations", [])
        return all(c["document_id"] == document_id and c["filename"] == filename
                   and 1 <= c["page"] <= len(pages) and c["chunk_id"]
                   and " ".join(c["quote"].split()) in pages[c["page"] - 1] for c in citations)

    @staticmethod
    def contract(row):
        if row["status_code"] != 200:
            return False
        body = row["body"]
        try:
            JournalResponse.model_validate(body)
            return set(body) == set(JournalResponse.model_fields) and 2 <= sentence_count(body["summary"]) <= 3
        except ValueError:
            return False

    def stop_api(self):
        listeners = [c for c in psutil.net_connections(kind="tcp") if c.status == psutil.CONN_LISTEN
                     and c.laddr.port == 8000 and c.pid]
        for pid in {c.pid for c in listeners}:
            process = psutil.Process(pid)
            assert Path(process.cwd()).resolve() == ROOT
            assert any(arg.replace("\\", "/").endswith("scripts/start.py") for arg in process.cmdline())
            parent = process.parent()
            if parent and any(arg.replace("\\", "/").endswith("scripts/start.py") for arg in parent.cmdline()):
                assert Path(parent.cwd()).resolve() == ROOT
                process = parent
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], check=True, capture_output=True)
        time.sleep(1)

    def restart(self, keys=None, cold_case=False):
        self.stop_api()
        self.replaced_server = True
        env = os.environ.copy()
        for variable in ("API_KEYS", "DATA_DIR", "PORT", "HOST"):
            env.pop(variable, None)
        temp = ROOT / "tmp/reviewer-runtime"
        temp.mkdir(parents=True, exist_ok=True)
        env.update(HOST="127.0.0.1", PORT="8000", TEMP=str(temp), TMP=str(temp))
        if keys:
            env["API_KEYS"] = ",".join(f"{name}:{key}" for name, key in keys.items())
        with (WORK / "api-stdout.log").open("ab") as stdout, (WORK / "api-stderr.log").open("ab") as stderr:
            process = subprocess.Popen([sys.executable, "scripts/start.py"], cwd=ROOT, env=env,
                                       stdout=stdout, stderr=stderr, creationflags=subprocess.CREATE_NO_WINDOW)
        self.history = {"interactive": deque(), "upload": deque()}
        start = time.monotonic()
        observed_cold = False
        while time.monotonic() - start < 200:
            if process.poll() is not None:
                raise RuntimeError("API startup process exited; see private test logs")
            try:
                live = self.client.get("/health/live", timeout=2)
                if live.status_code == 200:
                    if cold_case and not observed_cold:
                        row = self.request("POST", "/analyze-journal", json={"text": "I feel fine today."})
                        self.record("C14", row, {"cold_503": row["status_code"] == 503, "fails_fast": row["seconds"] < 5})
                        observed_cold = True
                    if self.client.get("/health/ready", timeout=3).status_code == 200:
                        return
            except httpx.TransportError:
                pass
            time.sleep(.3)
        raise RuntimeError("API did not become ready within 200 seconds")

    def run(self):
        assert self.client.get("/health/ready").status_code == 200
        original_ids = {d["id"] for d in self.client.get("/documents").json()["documents"]}
        row = self.request("POST", "/analyze-journal", kind="interactive", json={"text": "I feel fine today."})
        self.record("C1", row, {"six_field_contract": self.contract(row)})
        for case_id, payload in [("C2", {"text": ""}), ("C3", {"text": "   "}), ("C4", {}),
                                 ("C5", {"text": "hello", "userId": "1"}), ("C6", {"text": 123})]:
            row = self.request("POST", "/analyze-journal", json=payload)
            self.record(case_id, row, {"validation_422": row["status_code"] == 422})
        row = self.request("POST", "/analyze-journal", content=b"{text:", headers={"Content-Type": "application/json"})
        self.record("C7", row, {"client_error": 400 <= row["status_code"] < 500})
        for case_id in ("C8", "C9"):
            payload = json.loads(self.cases[case_id]["Request"])
            row = self.request("POST", "/analyze-journal", kind="interactive", json=payload)
            self.record(case_id, row, {"expected_status": row["status_code"] == 422 if case_id == "C8" else row["status_code"] == 200 or 400 <= row["status_code"] < 500})
        for case_id, size, suffix in (("C10", 8000, "x"), ("C11", 8001, "xx")):
            supplied = "I felt calm today. " * 421 + suffix
            actual_boundary = ("I felt calm today. " * 445)[:size]
            supplied_result = self.request("POST", "/analyze-journal", kind="interactive", json={"text": supplied})
            boundary_result = self.request("POST", "/analyze-journal", kind="interactive", json={"text": actual_boundary})
            self.record(case_id, {"supplied_recipe_characters": len(supplied), "supplied_recipe": supplied_result,
                                 "actual_boundary_characters": len(actual_boundary), "actual_boundary": boundary_result},
                        {"expected_status": boundary_result["status_code"] == 200 if case_id == "C10" else 400 <= boundary_result["status_code"] < 500},
                        "The supplied commands correctly yield 8000/8001 characters. The API also enforces an independent 2000-token bound, which rejects the 8000-character repeated input.", conflict=case_id == "C10")
        row = self.request("POST", "/analyze-journal", json={"text": "a" * 40000})
        self.record("C12", row, {"body_rejected": 400 <= row["status_code"] < 500})
        row = self.request("GET", "/analyze-journal")
        self.record("C13", row, {"method_405": row["status_code"] == 405})

        uploaded = self.upload("Employee_Handbook_Test.pdf")
        assert uploaded["status_code"] in {200, 201}, uploaded
        self.handbook = uploaded["body"]["document"]["id"]
        immediate = self.ask("What is the annual leave allowance?")
        self.record("D1", {"upload": uploaded, "immediate_question": immediate},
                    {"new_201": uploaded["status_code"] == 201, "ready": uploaded["body"].get("status") == "READY",
                     "immediate_answer": immediate["status_code"] == 200 and immediate["body"].get("status") == "ANSWERED"})
        duplicate = self.upload("Employee_Handbook_Test.pdf")
        self.record("D2", duplicate, {"duplicate_200": duplicate["status_code"] == 200, "same_id": duplicate["body"].get("document", {}).get("id") == self.handbook})
        metadata = self.request("GET", f"/documents/{self.handbook}")
        listed = self.client.get("/documents").json()["documents"]
        self.record("D3", metadata, {"metadata_200": metadata["status_code"] == 200,
                                     "three_pages": metadata["body"].get("pages") == 3,
                                     "listed": any(d["id"] == self.handbook for d in listed)})
        source = self.request("GET", f"/documents/{self.handbook}/file")
        self.record("D4", source, {"source_200": source["status_code"] == 200,
                                   "original_bytes": source["body"].get("sha256") == self.pack["fixtures"]["Employee_Handbook_Test.pdf"]["sha256"]})

        for number in range(20):
            case_id = f"R{number}"
            row = immediate if case_id == "R1" else self.ask(self.cases[case_id]["Question"])
            body = row["body"]
            expected_status = self.cases[case_id]["Status"]
            expected_pages = {int(p) for p in self.cases[case_id]["Page"].split() if p.isdigit()}
            actual_pages = {c["page"] for c in body.get("citations", [])}
            answer = body.get("answer", "").lower()
            checks = {"http_200": row["status_code"] == 200, "status": body.get("status") == expected_status,
                      "expected_pages": expected_pages.issubset(actual_pages),
                      "exact_authorized_quotes": self.quote_checks(body, self.handbook, "Employee_Handbook_Test.pdf"),
                      "key_facts": all(value in answer for value in FACTS.get(case_id, []))}
            if case_id == "R0":
                checks["key_facts"] = "24" in answer and any(n in answer for n in ("5", "10", "26", "15"))
            if expected_status == "INSUFFICIENT_EVIDENCE":
                checks["no_citations"] = body.get("citations") == []
            self.record(case_id, row, checks, "Key-fact matching supplements the retained full answer and exact page quotes; inspect semantic qualifications separately.")
        row = self.request("POST", f"/documents/{self.handbook}/questions", json={"question": ""})
        self.record("R20", row, {"empty_rejected": row["status_code"] == 422})
        row = self.ask("What is the annual leave allowance?", "00000000-0000-0000-0000-000000000000")
        self.record("R21", row, {"unknown_404": row["status_code"] == 404})

        travel = self.upload("Travel_Policy_Other_Doc.pdf")
        assert travel["status_code"] in {200, 201}
        travel_id = travel["body"]["document"]["id"]
        for case_id, doc_id, question in (("I1", travel_id, "What is the hotel limit per night?"),
                                          ("I2", self.handbook, "What is the hotel limit per night?"),
                                          ("I3", travel_id, "How many days of annual leave do I get?")):
            row = self.ask(question, doc_id)
            body = row["body"]
            checks = {"http_200": row["status_code"] == 200}
            if case_id == "I1":
                checks.update(answered=body.get("status") == "ANSWERED", correct_value="150" in body.get("answer", ""),
                              source=self.quote_checks(body, travel_id, "Travel_Policy_Other_Doc.pdf") and bool(body.get("citations")))
            else:
                checks.update(abstention=body.get("status") == "INSUFFICIENT_EVIDENCE", no_citations=body.get("citations") == [])
            self.record(case_id, row, checks)

        writer = PdfWriter()
        for _ in range(40):
            for page in PdfReader(FIXTURES / "Employee_Handbook_Test.pdf").pages:
                writer.add_page(page)
        writer.write(str(WORK / "too_many_pages.pdf"))
        for case_id, name, data, code in (("D5", "fake.pdf", b"hello", "INVALID_PDF_SIGNATURE"),
                                         ("D6", "Scanned_Image_Only_Test.pdf", None, "NO_USABLE_TEXT"),
                                         ("D7", "Encrypted_Test.pdf", None, "PDF_ENCRYPTED"),
                                         ("D8", "too_many_pages.pdf", (WORK / "too_many_pages.pdf").read_bytes(), "PDF_PAGE_LIMIT")):
            row = self.upload(name, data)
            self.record(case_id, row, {"client_error": 400 <= row["status_code"] < 500,
                                      "explicit_error": bool(row["body"].get("error", {}).get("message")),
                                      "not_ready": row["body"].get("status") != "READY"}, f"Expected explicit rejection category: {code}.")

        self.restart(cold_case=True)
        row = self.ask("What is the annual leave allowance?")
        self.record("I5", row, {"http_200": row["status_code"] == 200, "persisted_answer": row["body"].get("status") == "ANSWERED" and "24" in row["body"].get("answer", "")}, "API process restarted; no re-upload or re-embedding request was made.")
        deleted = self.request("DELETE", f"/documents/{self.handbook}")
        after = self.ask("What is the annual leave allowance?")
        listed = self.client.get("/documents").json()["documents"]
        self.record("I6", {"delete": deleted, "question": after},
                    {"deleted": 200 <= deleted["status_code"] < 300, "question_404": after["status_code"] == 404,
                     "not_listed": not any(d["id"] == self.handbook for d in listed)})
        # Remove only records created by these upload checks; preserve the original library.
        for document in listed:
            if document["id"] not in original_ids and document["filename"] in {
                "Employee_Handbook_Test.pdf", "Travel_Policy_Other_Doc.pdf", "Scanned_Image_Only_Test.pdf",
                "Encrypted_Test.pdf", "too_many_pages.pdf", "fake.pdf"
            }:
                self.client.delete(f"/documents/{document['id']}")

        for case_id, overrides in (("A4", {"API_KEYS": "badvalue"}), ("A5", {"HOST": "0.0.0.0"})):
            env = os.environ.copy()
            env.pop("API_KEYS", None)
            env.update(overrides)
            completed = subprocess.run([sys.executable, "scripts/start.py"], cwd=ROOT, env=env,
                                       capture_output=True, text=True, timeout=40, creationflags=subprocess.CREATE_NO_WINDOW)
            error = completed.stderr.strip().splitlines()[-1]
            self.record(case_id, {"exit_code": completed.returncode, "error": error},
                        {"startup_rejected": completed.returncode != 0, "clear_configuration_error": "ValueError:" in error})
        keys = {name: secrets.token_urlsafe(32) for name in ("alice", "bob")}
        self.restart(keys=keys)
        for case_id, headers in (("A1", {}), ("A2", {"Authorization": "Bearer wrong-key"}),
                                 ("A3", {"Authorization": "Bearer " + keys["alice"]})):
            row = self.request("POST", "/analyze-journal", headers=headers, json={"text": "I feel fine today."})
            self.record(case_id, row, {"expected_status": row["status_code"] == (200 if case_id == "A3" else 401),
                                      "contract_if_authorized": self.contract(row) if case_id == "A3" else True})
        self.headers = {"Authorization": "Bearer " + keys["alice"]}
        alice_doc = self.upload("Employee_Handbook_Test.pdf")["body"]["document"]["id"]
        bob = {"Authorization": "Bearer " + keys["bob"]}
        metadata = self.request("GET", f"/documents/{alice_doc}", headers=bob)
        library = self.request("GET", "/documents", headers=bob)
        question = self.request("POST", f"/documents/{alice_doc}/questions", headers=bob, json={"question": "What is the annual leave allowance?"})
        self.record("I4", {"metadata": metadata, "library": library, "question": question},
                    {"metadata_404": metadata["status_code"] == 404, "empty_library": library["body"].get("documents") == [], "question_404": question["status_code"] == 404})
        self.client.delete(f"/documents/{alice_doc}", headers=self.headers)
        self.pace("interactive", 5)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            rows = list(pool.map(lambda _: self.request("POST", "/analyze-journal", json={"text": "I feel stressed about work today."}), range(5)))
        statuses = [row["status_code"] for row in rows]
        self.record("A6", rows, {"three_successes": statuses.count(200) == 3,
                                 "two_capacity_rejections": sum(row["body"].get("error", {}).get("code") == "QUEUE_FULL" for row in rows) == 2,
                                 "bounded_wait": all(row["seconds"] < 35 for row in rows)},
                    "Admission reserves one active plus two queued requests. Their request deadlines include queue time, so admission does not guarantee three HTTP 200 responses.", conflict=True)
        time.sleep(5)
        assert len(self.report["cases"]) == 56


def main():
    run = Run()
    try:
        run.run()
    finally:
        if run.replaced_server:
            run.headers = {}
            run.restart()
            print("Restored credential-free loopback API with the original data directory.", flush=True)
        run.client.close()


if __name__ == "__main__":
    main()
