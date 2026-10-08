"""Recheck omitted policy conditions with fresh real-model document ingestion."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from io import BytesIO

from pypdf import PdfWriter

from scripts.reviewer_protocol import FACTS, FIXTURES, ROOT, Run


def main():
    run = Run()
    report = {"scope": "Post-correction targeted policy-condition regression; AI-assisted self-test pack with predicted expectations", "cases": []}
    writer = PdfWriter(clone_from=BytesIO((FIXTURES / "Employee_Handbook_Test.pdf").read_bytes()))
    writer.add_metadata({"/CreationDate": datetime.now(timezone.utc).isoformat()})
    data = BytesIO()
    writer.write(data)
    try:
        upload = run.upload("Employee_Handbook_Test.pdf", data.getvalue())
        report["upload"] = upload
        assert upload["status_code"] == 201 and upload["body"]["status"] == "READY", upload
        run.handbook = upload["body"]["document"]["id"]
        for case_id in ("R2", "R8", "R18", "R12", "R14", "R19", "R17"):
            case = run.cases[case_id]
            actual = run.ask(case["Question"])
            body = actual["body"]
            checks = {"http_200": actual["status_code"] == 200,
                      "predicted_status": body.get("status") == case["Status"],
                      "key_facts": all(fact in body.get("answer", "").lower() for fact in FACTS.get(case_id, [])),
                      "quotes_and_document": run.quote_checks(body, run.handbook, "Employee_Handbook_Test.pdf")}
            if case["Page"].isdigit():
                checks["predicted_page"] = any(c["page"] == int(case["Page"]) for c in body.get("citations", []))
            row = {"id": case_id, "question": case["Question"], "predicted_expectation": {k: case[k] for k in ("Status", "Answer must contain", "Page")}, "actual": actual, "checks": checks}
            report["cases"].append(row)
            (ROOT / "reports/policy-condition-regression.json").write_text(json.dumps(report, indent=2), encoding="utf8")
            print(json.dumps(row), flush=True)
    finally:
        if run.handbook:
            run.client.delete(f"/documents/{run.handbook}")
        run.client.close()


if __name__ == "__main__":
    main()
