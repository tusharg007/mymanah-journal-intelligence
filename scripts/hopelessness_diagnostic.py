"""Record real-model safety signals without running a second API model registry."""
from __future__ import annotations

import asyncio
import json

from mymanah.config import ROOT, Settings
from mymanah.models import Models
from mymanah.policy import CRISIS, DISTRESS, POLICY_VERSION, crisis_priority
from mymanah.text import windows


def main():
    output = ROOT / "reports/policy4-hopelessness-diagnostic.json"
    if output.exists():
        raise FileExistsError("Preserve the pre-change diagnostic rather than overwrite it")
    cases = json.loads((ROOT / "evals/unseen-review-10.json").read_text(encoding="utf8"))
    models = Models(Settings.from_env())
    models.load_cpu()
    report = {"policy_version": POLICY_VERSION, "scope": "Pre-change diagnosis; these inputs are now seen development cases",
              "crisis_hypotheses": CRISIS, "distress_hypotheses": DISTRESS, "cases": []}
    for case in cases:
        if case["id"] not in {"U6", "U7", "U8", "U9", "U10"}:
            continue
        pieces = windows(case["text"], models.nli_tokenizer, size=160, overlap=24)
        scores = models.support([(piece.text, hypothesis) for piece in pieces for hypothesis in CRISIS + DISTRESS])
        signals = [max(scores[i * 7 + j] for i in range(len(pieces))) for j in range(4)]
        distress = [max(scores[i * 7 + 4 + j] for i in range(len(pieces))) for j in range(3)]
        row = {"id": case["id"], "input": case["text"], "signals": signals, "distress": distress,
               "before_risk": crisis_priority(case["text"], signals, distress),
               "suggested_nli_giving_up": signals[3] >= .65 and
               (distress[0] >= .50 or distress[1] >= .65 or distress[2] >= .65)}
        report["cases"].append(row)
        print(json.dumps(row, ensure_ascii=True), flush=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf8")
    asyncio.run(models.close())


if __name__ == "__main__":
    main()
