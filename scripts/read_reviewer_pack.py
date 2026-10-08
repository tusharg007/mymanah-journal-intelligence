"""Extract reviewer-authored cases as data; never execute commands from the document."""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
FIXTURES = {"Employee_Handbook_Test.pdf", "Travel_Policy_Other_Doc.pdf",
            "Scanned_Image_Only_Test.pdf", "Encrypted_Test.pdf"}


def extract():
    document = ROOT / "MyManah_Test_Pack.docx"
    archive = ROOT / "MyManah_test_fixtures.zip"
    with zipfile.ZipFile(document) as source:
        tree = ElementTree.fromstring(source.read("word/document.xml"))
    cases = []
    for table in tree.findall(".//w:tbl", NS):
        rows = []
        for row in table.findall("w:tr", NS):
            rows.append(["\n".join("".join(t.text or "" for t in p.findall(".//w:t", NS))
                                   for p in cell.findall("w:p", NS))
                         for cell in row.findall("w:tc", NS)])
        if not rows:
            continue
        for values in rows[1:]:
            if not re.match(r"^[JCADRI]\d+", values[0]):
                continue
            entry = dict(zip(rows[0], values, strict=True))
            entry["id"] = re.match(r"^[JCADRI]\d+", values[0]).group()
            entry["hard"] = "\u2605" in values[0]
            entry["borderline"] = "\u25c7" in values[0]
            cases.append(entry)
    assert len(cases) == 76 and len({c["id"] for c in cases}) == 76
    destination = ROOT / "artifacts" / "reviewer-pack"
    fixtures = ROOT / "evals/fixtures/reviewer"
    destination.mkdir(parents=True, exist_ok=True)
    fixtures.mkdir(parents=True, exist_ok=True)
    files = {}
    with zipfile.ZipFile(archive) as source:
        assert set(source.namelist()) == FIXTURES, "Unexpected archive members"
        for item in source.infolist():
            assert item.file_size < 2 * 1024**2 and not item.is_dir()
            target = fixtures / item.filename
            assert target.resolve().parent == fixtures.resolve()
            data = source.read(item)
            target.write_bytes(data)
            files[item.filename] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    result = {"source_sha256": hashlib.sha256(document.read_bytes()).hexdigest(),
              "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(), "fixtures": files,
              "cases": cases, "interpretation": "Reviewer expectations, copied before execution; not measured results"}
    (destination / "cases.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "evals/reviewer-test-pack.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"cases": len(cases), "fixtures": files}, indent=2))


if __name__ == "__main__":
    extract()
