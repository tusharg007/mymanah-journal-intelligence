"""Compile current regression and the single unseen run from measured responses."""
from __future__ import annotations

import hashlib
import json
import math
import re
import statistics

from mymanah.config import ROOT
from mymanah.journal import JournalService
from mymanah.schemas import SummaryDraft


def block(value):
    return ["```json", json.dumps(value, ensure_ascii=False, indent=2), "```", ""]


def metrics(cases):
    samples = sorted(row["seconds"] for row in cases if row["http_status"] == 200)
    return {"valid_count": len(samples), "p50_seconds": statistics.median(samples),
            "p95_nearest_rank_seconds": samples[math.ceil(.95 * len(samples)) - 1],
            "minimum_seconds": samples[0], "maximum_seconds": samples[-1],
            "scope": "Warm sequential local requests; small development sample, not a production guarantee"}


def journal_report(data, unseen=False):
    cases = data["cases"]
    valid = [row for row in cases if row["http_status"] == 200]
    matching = sum(all(row.get("label_checks", {}).values()) for row in valid)
    generated = sum(any("path=generated" in line for line in row.get("inference_observations", [])) for row in valid)
    lines = ["# " + ("Unseen Ten-Entry Results" if unseen else "Journal Policy 4 Regression"), "",
             "Workflow: `POST /analyze-journal`, real pinned CPU classifiers and local Qwen3 4B GGUF generation.", "",
             "Expectations are user/candidate predictions rather than independent ground truth.",
             ("The ten inputs were run once, unchanged, without retries or tuning on these results. Implementation and input hashes are in the raw report."
              if unseen else "These 20 self-test inputs, four J1 regressions and the 512-word entry are development cases; original reports and the frozen held-out set are preserved."), "",
             f"Valid responses: {len(valid)}/{len(cases)}. Responses matching every specified label: {matching}/{len(cases)}.",
             f"Summary paths: {generated} generated, {len(valid) - generated} verified extractive fallbacks.",
             "The LLM runs first on every valid journal; up to one repair is allowed. A fallback is used only after two generation/verification failures and still passes evidence checks. Deadline errors remain errors.",
             "One-fact summaries append 'No further details are given.'; this is deterministic scope text, not an additional personal fact.",
             "Confidence is the normalized selected emotion score; a sentiment-driven happy override uses sentiment confidence. Neither score is calibrated or covers screening risk or summary correctness.", "",
             "| Case | HTTP | Sentiment | Emotion | Risk | Mood | Confidence | Seconds | Specified labels agree |",
             "| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- |"]
    for row in cases:
        actual = row.get("actual", {})
        lines.append(f"| {row['id']} | {row['http_status']} | {actual.get('sentiment', '-')} | {actual.get('emotion', '-')} | {actual.get('crisisRisk', '-')} | {actual.get('moodScore', '-')} | {actual.get('confidence', '-')} | {row['seconds']:.6f} | {all(row.get('label_checks', {}).values()) if row['http_status'] == 200 else 'service error'} |")
    lines += ["", "## Current Latency", ""]
    if unseen:
        lines += ["U6 returned anger/MEDIUM instead of sad/HIGH, with emotion confidence 0.8634.",
                  "U10 returned MEDIUM instead of HIGH, despite a 0.9988 sad-emotion score; its summary excluded the injected instruction.",
                  "These are preserved failures. High selected-emotion scores can be wrong and do not validate the independent risk policy.",
                  "U7/U8/U9 returned LOW/LOW/MEDIUM, avoiding the specified HIGH false positives. U7 still selected sad emotion for a recovery narrative, for which the user did not prescribe an emotion.", ""]
        lines += ["After this run a separate development check corrected missing terminal punctuation in the fallback presentation helper. No models, prompts, decision thresholds or confidence rules changed, and none of these inputs was rerun. The original raw implementation hashes remain attached to this assessment; the already punctuated recorded summaries are unaffected. The [source and formatting audit](policy4-formatting-audit.json) verifies the two-line difference and unchanged formatting of all ten saved summaries.", ""]
        lines += block(data["latency"])
    else:
        lines += ["Short self-test entries (J1-J19), excluding J20 and the 512-word journal:", ""] + block(metrics([row for row in cases if row["id"].startswith("J") and row["id"] != "J20"]))
        long = [row for row in cases if row["id"] in {"J20", "long01"}]
        lines += ["Separate long-entry measurements use independent `perf_counter_ns` intervals and input hashes:", ""]
        lines += block([{key: row[key] for key in ("id", "input_sha256", "elapsed_ns", "seconds", "http_status")} for row in long])
        lines += ["The policy-3 raw report saved both as 13.406 seconds, with no finer clock data. Those historical values cannot establish whether rounding coincidence caused the equality. The new measurements above are independent and are not copied from either prior case.", ""]
    for row in cases:
        lines += [f"## {row['id']}", "", "Request:", ""] + block({"text": row["text"]})
        lines += ["Predicted expectations:", ""] + block(row["expected"])
        lines += [f"Actual HTTP {row['http_status']}, {row['seconds']:.6f} seconds:", ""] + block(row.get("actual", row.get("transport_error")))
        lines += ["Specified-label checks:", ""] + block(row.get("label_checks", {}))
        if unseen:
            lines += ["Confidence check:", ""] + block(row.get("confidence_check", {}))
            if "injection_not_summarized" in row:
                lines += [f"Instruction excluded from summary: {row['injection_not_summarized']}.", ""]
        lines += ["Observed inference metadata (contains no journal text):", ""] + block(row.get("inference_observations", []))
    return "\n".join(lines)


def main():
    journals = json.loads((ROOT / "reports/journal-policy4-regression.json").read_text(encoding="utf8"))
    unseen = json.loads((ROOT / "reports/unseen-review-10.json").read_text(encoding="utf8"))
    changes = []
    for filename, original in unseen["implementation_sha256"].items():
        source = (ROOT / filename).read_bytes()
        current = hashlib.sha256(source).hexdigest()
        if current != original:
            assert filename == "mymanah\\journal.py" or filename == "mymanah/journal.py"
            before_boundary_fix = b"".join(line for line in source.splitlines(keepends=True)
                                          if not line.lstrip().startswith((b"sentences = [sentence if re.search", b"for sentence in sentences]")))
            assert hashlib.sha256(before_boundary_fix).hexdigest() == original
            changes.append({"file": filename, "assessment_sha256": original, "release_sha256": current,
                            "change": "Only two lines ensuring terminal punctuation in presentation_summary"})
    unchanged_summaries = {}
    for row in unseen["cases"]:
        if row["http_status"] == 200:
            summary = row["actual"]["summary"]
            sentences = re.findall(r"\S[\s\S]*?(?:[.!?](?=\s|$)|$)", summary)
            draft = SummaryDraft(sentences=[{"text": sentence, "quote": row["text"]} for sentence in sentences])
            unchanged_summaries[row["id"]] = JournalService.presentation_summary(draft, [row["text"]]) == summary
    assert all(unchanged_summaries.values())
    (ROOT / "reports/policy4-formatting-audit.json").write_text(json.dumps({
        "scope": "Source-byte comparison and formatting identity check; no inference reruns",
        "changes_since_unseen_assessment": changes, "other_implementation_files_identical": True,
        "assessment_summaries_unchanged_by_formatter": unchanged_summaries
    }, indent=2), encoding="utf8")
    for filename, data, flag in [("JOURNAL_POLICY4_REGRESSION.md", journals, False), ("UNSEEN_REVIEW_10.md", unseen, True)]:
        (ROOT / "reports" / filename).write_text(journal_report(data, flag), encoding="utf8")
    policy = json.loads((ROOT / "reports/policy4-condition-regression.json").read_text(encoding="utf8"))
    lines = ["# Policy 4 Document Regression", "", "Workflow: fresh `POST /documents` followed by `POST /documents/{id}/questions`.", "",
             "Seven targeted cases from the AI-assisted self-test pack with predicted expectations; this is not a new 76-case pass count.",
             "R14 checks topic absence before generation. R12 sends only the supported question part to the generator, verifies its claims, and returns PARTIAL with the uncovered part named.",
             "The lexical guard checks retrieved evidence and recognized content modifiers; it is conservative and can miss synonyms. It does not prove absence from the entire document.", "",
             "## Fresh Upload", ""] + block(policy["upload"])
    for row in policy["cases"]:
        lines += [f"## {row['id']}", "", "Input:", ""] + block({"question": row["question"]})
        lines += ["Predicted expectations:", ""] + block(row["predicted_expectation"])
        lines += ["Actual response and elapsed seconds:", ""] + block(row["actual"])
        lines += ["Checks:", ""] + block(row["checks"])
    (ROOT / "reports/POLICY4_CONDITION_REGRESSION.md").write_text("\n".join(lines), encoding="utf8")


if __name__ == "__main__":
    main()
