"""Recheck the long entry and immediate recovery after the timeout-handling fix."""
import json
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]


def main():
    cases = json.loads((ROOT / "reports/reviewer-journals.json").read_text(encoding="utf-8"))["cases"]
    long_entry = next(row["input"] for row in cases if row["id"] == "J20")
    rows = []
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=75, trust_env=False) as client:
        for name, text in (("J20_after_timeout_fix", long_entry),
                           ("unsupported_language_immediately_after_long_entry", "\u092e\u0948\u0902 \u0906\u091c \u0926\u0941\u0916\u0940 \u0939\u0942\u0901"),
                           ("short_entry_immediately_after_long_entry", "Today was an ordinary day. I went to work and came home.")):
            start = time.monotonic()
            response = client.post("/analyze-journal", json={"text": text})
            row = {"case": name, "status_code": response.status_code, "seconds": round(time.monotonic() - start, 3), "body": response.json()}
            rows.append(row)
            print(f"{name}: {response.status_code} {row['seconds']}s", flush=True)
    (ROOT / "reports/reviewer-timeout-recovery.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
