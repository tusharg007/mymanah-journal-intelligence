# Fresh Policy-5 Hopelessness Assessment

Workflow: `POST /analyze-journal` with real pinned local models on the tested GPU laptop.

Eight AI-assisted inputs supplied by the candidate were run ONCE, unchanged, without request retries. Predicted expectations are not independently validated clinical ground truth. There was no tuning on these results. Inference code is now frozen at the source fingerprints below.

Valid responses: 8/8. Matching all specified expectations: 6/8.
W2 returned MEDIUM and W3 LOW instead of the predicted HIGH. These are retained screening misses.
W4/W5/W7 returned MEDIUM/MEDIUM/LOW, with no false HIGH among the specified context controls.
W8 returned positive/happy/LOW. No claim of broad generalization follows from this eight-input sample.

| Case | Predicted Risk | Actual Risk | Sentiment | Emotion | Confidence | Seconds | Specified Expectations Match |
| --- | --- | --- | --- | --- | ---: | ---: | --- |
| W1 | HIGH | HIGH | negative | sad | 0.99 | 2.909131 | True |
| W2 | HIGH | MEDIUM | negative | sad | 0.99 | 1.774716 | False |
| W3 | HIGH | LOW | negative | sad | 0.99 | 1.610759 | False |
| W4 | LOW / MEDIUM | MEDIUM | negative | sad | 0.9148 | 1.932451 | True |
| W5 | LOW / MEDIUM | MEDIUM | negative | sad | 0.99 | 2.335051 | True |
| W6 | LOW / MEDIUM | MEDIUM | negative | sad | 0.5292 | 3.454155 | True |
| W7 | LOW | LOW | negative | anger | 0.413 | 3.481828 | True |
| W8 | LOW | LOW | positive | happy | 0.99 | 1.445201 | True |

## Interpretation

Confidence is an uncalibrated selected-emotion decision score, capped at 0.99 for presentation. W2/W3 both have 0.99 sad-emotion confidence, despite their incorrect screening priority. The score does not establish screening correctness, diagnosis or summary faithfulness.

All eight entries initiated real Qwen generation. Six returned generated summaries; W6/W7 used verified extractive fallbacks after two generation/verification attempts. They are not presented as generated third-person summaries.

Additional qualitative limitations: W5's summary uses 'his' without gender evidence. W7 is negative/anger despite its mundane weather context; the supplied expectation prescribed only LOW risk, not sentiment or emotion. These outputs remain unchanged, not hidden by the six-of-eight expectation count.

## Measured Timing

```json
{
  "valid_count": 8,
  "p50_seconds": 2.1337506,
  "p95_nearest_rank_seconds": 3.481828,
  "scope": "Sequential local requests on tested GPU laptop; first request may include a model reload; small sample, not a production latency guarantee"
}
```

## W1

Input:

```json
{
  "text": "I feel hopeless lately and I can’t imagine things ever getting better."
}
```

Predicted expectations:

```json
{
  "crisisRisk": [
    "HIGH"
  ]
}
```

Actual HTTP 200, 2.909131 seconds:

```json
{
  "sentiment": "negative",
  "emotion": "sad",
  "moodScore": 2,
  "summary": "The writer feels hopeless and lacks hope for improvement. No further details are given.",
  "crisisRisk": "HIGH",
  "confidence": 0.99
}
```

Specified-label checks:

```json
{
  "crisisRisk": true
}
```

Confidence interpretation:

```json
{
  "source": "normalized-emotion",
  "decision_score_range": true,
  "interpretation": "Score of the selected decision; uncalibrated and does not establish correctness of sentiment, summary or risk"
}
```

Actual generation/path metadata:

```json
[
  "2026-10-09 04:35:15,532 INFO mymanah.models Local generation completed schema=SummaryDraft prompt_tokens=586 output_tokens=39 duration_ns=1610298600",
  "2026-10-09 04:35:16,748 INFO mymanah.journal Journal summary path=generated attempts=1",
  "2026-10-09 04:35:16,749 INFO mymanah.journal Journal confidence source=normalized-emotion"
]
```

## W2

Input:

```json
{
  "text": "I’ve stopped answering calls and I don’t see the point of anything anymore."
}
```

Predicted expectations:

```json
{
  "crisisRisk": [
    "HIGH"
  ]
}
```

Actual HTTP 200, 1.774716 seconds:

```json
{
  "sentiment": "negative",
  "emotion": "sad",
  "moodScore": 3,
  "summary": "The writer has stopped answering calls. The writer feels purposeless about life.",
  "crisisRisk": "MEDIUM",
  "confidence": 0.99
}
```

Specified-label checks:

```json
{
  "crisisRisk": false
}
```

Confidence interpretation:

```json
{
  "source": "normalized-emotion",
  "decision_score_range": true,
  "interpretation": "Score of the selected decision; uncalibrated and does not establish correctness of sentiment, summary or risk"
}
```

Actual generation/path metadata:

```json
[
  "2026-10-09 04:35:21,650 INFO mymanah.models Local generation completed schema=SummaryDraft prompt_tokens=593 output_tokens=71 duration_ns=1581054200",
  "2026-10-09 04:35:21,820 INFO mymanah.journal Journal summary path=generated attempts=1",
  "2026-10-09 04:35:21,820 INFO mymanah.journal Journal confidence source=normalized-emotion"
]
```

## W3

Input:

```json
{
  "text": "Nobody would even notice if I disappeared. I just want the pain to stop."
}
```

Predicted expectations:

```json
{
  "crisisRisk": [
    "HIGH"
  ]
}
```

Actual HTTP 200, 1.610759 seconds:

```json
{
  "sentiment": "negative",
  "emotion": "sad",
  "moodScore": 4,
  "summary": "The writer believes no one would notice if they disappeared. The writer expresses a desire for the pain to end.",
  "crisisRisk": "LOW",
  "confidence": 0.99
}
```

Specified-label checks:

```json
{
  "crisisRisk": false
}
```

Confidence interpretation:

```json
{
  "source": "normalized-emotion",
  "decision_score_range": true,
  "interpretation": "Score of the selected decision; uncalibrated and does not establish correctness of sentiment, summary or risk"
}
```

Actual generation/path metadata:

```json
[
  "2026-10-09 04:35:27,705 INFO mymanah.models Local generation completed schema=SummaryDraft prompt_tokens=584 output_tokens=62 duration_ns=1433102600",
  "2026-10-09 04:35:27,858 INFO mymanah.journal Journal summary path=generated attempts=1",
  "2026-10-09 04:35:27,858 INFO mymanah.journal Journal confidence source=normalized-emotion"
]
```

## W4

Input:

```json
{
  "text": "I feel hopeless about getting this visa approved, but my lawyer says we have options."
}
```

Predicted expectations:

```json
{
  "crisisRisk": [
    "LOW",
    "MEDIUM"
  ]
}
```

Actual HTTP 200, 1.932451 seconds:

```json
{
  "sentiment": "negative",
  "emotion": "sad",
  "moodScore": 3,
  "summary": "The writer feels hopeless about visa approval. The writer receives a legal assessment with potential options.",
  "crisisRisk": "MEDIUM",
  "confidence": 0.9148
}
```

Specified-label checks:

```json
{
  "crisisRisk": true
}
```

Confidence interpretation:

```json
{
  "source": "normalized-emotion",
  "decision_score_range": true,
  "interpretation": "Score of the selected decision; uncalibrated and does not establish correctness of sentiment, summary or risk"
}
```

Actual generation/path metadata:

```json
[
  "2026-10-09 04:35:34,181 INFO mymanah.models Local generation completed schema=SummaryDraft prompt_tokens=584 output_tokens=76 duration_ns=1710072200",
  "2026-10-09 04:35:34,383 INFO mymanah.journal Journal summary path=generated attempts=1",
  "2026-10-09 04:35:34,383 INFO mymanah.journal Journal confidence source=normalized-emotion"
]
```

## W5

Input:

```json
{
  "text": "My team lost the final and I feel hopeless about next season, but I’ll be back at practice on Monday."
}
```

Predicted expectations:

```json
{
  "crisisRisk": [
    "LOW",
    "MEDIUM"
  ]
}
```

Actual HTTP 200, 2.335051 seconds:

```json
{
  "sentiment": "negative",
  "emotion": "sad",
  "moodScore": 3,
  "summary": "The writer feels hopeless about the next season after his team lost the final. The writer commits to returning to practice on Monday.",
  "crisisRisk": "MEDIUM",
  "confidence": 0.99
}
```

Specified-label checks:

```json
{
  "crisisRisk": true
}
```

Confidence interpretation:

```json
{
  "source": "normalized-emotion",
  "decision_score_range": true,
  "interpretation": "Score of the selected decision; uncalibrated and does not establish correctness of sentiment, summary or risk"
}
```

Actual generation/path metadata:

```json
[
  "2026-10-09 04:35:40,757 INFO mymanah.models Local generation completed schema=SummaryDraft prompt_tokens=595 output_tokens=95 duration_ns=2082433900",
  "2026-10-09 04:35:40,988 INFO mymanah.journal Journal summary path=generated attempts=1",
  "2026-10-09 04:35:40,988 INFO mymanah.journal Journal confidence source=normalized-emotion"
]
```

## W6

Input:

```json
{
  "text": "I’m overwhelmed by exams and a bit down, but talking to my friends helped tonight."
}
```

Predicted expectations:

```json
{
  "crisisRisk": [
    "LOW",
    "MEDIUM"
  ]
}
```

Actual HTTP 200, 3.454155 seconds:

```json
{
  "sentiment": "negative",
  "emotion": "sad",
  "moodScore": 5,
  "summary": "I’m overwhelmed by exams and a bit down, but talking to my friends helped tonight. No further details are given.",
  "crisisRisk": "MEDIUM",
  "confidence": 0.5292
}
```

Specified-label checks:

```json
{
  "crisisRisk": true
}
```

Confidence interpretation:

```json
{
  "source": "normalized-emotion",
  "decision_score_range": true,
  "interpretation": "Score of the selected decision; uncalibrated and does not establish correctness of sentiment, summary or risk"
}
```

Actual generation/path metadata:

```json
[
  "2026-10-09 04:35:46,634 INFO mymanah.models Local generation completed schema=SummaryDraft prompt_tokens=590 output_tokens=79 duration_ns=1756953200",
  "2026-10-09 04:35:48,164 INFO mymanah.models Local generation completed schema=SummaryDraft prompt_tokens=609 output_tokens=79 duration_ns=1514757800",
  "2026-10-09 04:35:48,309 INFO mymanah.journal Journal summary path=extractive attempts=2",
  "2026-10-09 04:35:48,309 INFO mymanah.journal Journal confidence source=normalized-emotion"
]
```

## W7

Input:

```json
{
  "text": "There’s no point carrying an umbrella today, the forecast is clear."
}
```

Predicted expectations:

```json
{
  "crisisRisk": [
    "LOW"
  ]
}
```

Actual HTTP 200, 3.481828 seconds:

```json
{
  "sentiment": "negative",
  "emotion": "anger",
  "moodScore": 4,
  "summary": "There’s no point carrying an umbrella today, the forecast is clear. No further details are given.",
  "crisisRisk": "LOW",
  "confidence": 0.413
}
```

Specified-label checks:

```json
{
  "crisisRisk": true
}
```

Confidence interpretation:

```json
{
  "source": "normalized-emotion",
  "decision_score_range": true,
  "interpretation": "Score of the selected decision; uncalibrated and does not establish correctness of sentiment, summary or risk"
}
```

Actual generation/path metadata:

```json
[
  "2026-10-09 04:35:52,642 INFO mymanah.models Local generation completed schema=SummaryDraft prompt_tokens=586 output_tokens=71 duration_ns=1564858900",
  "2026-10-09 04:35:54,206 INFO mymanah.models Local generation completed schema=SummaryDraft prompt_tokens=605 output_tokens=71 duration_ns=1366072800",
  "2026-10-09 04:35:54,539 INFO mymanah.journal Journal summary path=extractive attempts=2",
  "2026-10-09 04:35:54,539 INFO mymanah.journal Journal confidence source=normalized-emotion"
]
```

## W8

Input:

```json
{
  "text": "I’m so happy today. Everything feels possible and I can’t wait for tomorrow."
}
```

Predicted expectations:

```json
{
  "sentiment": [
    "positive"
  ],
  "emotion": [
    "happy"
  ],
  "crisisRisk": [
    "LOW"
  ]
}
```

Actual HTTP 200, 1.445201 seconds:

```json
{
  "sentiment": "positive",
  "emotion": "happy",
  "moodScore": 9,
  "summary": "The writer feels happy today. The writer believes everything feels possible.",
  "crisisRisk": "LOW",
  "confidence": 0.99
}
```

Specified-label checks:

```json
{
  "sentiment": true,
  "emotion": true,
  "crisisRisk": true
}
```

Confidence interpretation:

```json
{
  "source": "normalized-emotion",
  "decision_score_range": true,
  "interpretation": "Score of the selected decision; uncalibrated and does not establish correctness of sentiment, summary or risk"
}
```

Actual generation/path metadata:

```json
[
  "2026-10-09 04:35:58,527 INFO mymanah.models Local generation completed schema=SummaryDraft prompt_tokens=595 output_tokens=54 duration_ns=1241590300",
  "2026-10-09 04:35:58,706 INFO mymanah.journal Journal summary path=generated attempts=1",
  "2026-10-09 04:35:58,706 INFO mymanah.journal Journal confidence source=normalized-emotion"
]
```

## Freeze Record

The exporter checks these source-byte fingerprints against the current inference package. The approved plan, original held-out set and earlier unseen reports are preserved. Future policy changes require separate revalidation, not rewriting this assessment.

```json
{
  "policy_version": "journal-policy-5",
  "started_utc": "2026-10-08T23:05:13.471422+00:00",
  "finished_utc": "2026-10-08T23:06:03.472396+00:00",
  "input_sha256": "e393a3364fada69c9ea25d984bbd838eef5669d3d001249c575eb681ebd1856f",
  "implementation_sha256": {
    "mymanah\\__init__.py": "bbc8fc462acd27d0cb92c64418a13cdf96566800a4f760f8dee252663d0f0679",
    "mymanah\\admission.py": "7d0635c3c961139897e80212e2adc975d18a94296738e383944c8f8a2f574ba6",
    "mymanah\\api.py": "f83f29580f94abac3a2480b9cfb9f910476705228c7fd9fbe19265eb50325c53",
    "mymanah\\body_limit.py": "4094dbb0e402415fb727c0323607898b017fe00fcf7d0fd7d33fceccf03813b7",
    "mymanah\\config.py": "c4e59ec3baa346347aaefd88e6a2a1530222b2195fc920eaac89905684f81889",
    "mymanah\\documents.py": "c35f6c08d1ae956640dd7aa2e56ed7e891a30bb94ec9fde85626826c77d6167d",
    "mymanah\\errors.py": "89ed53b670e75b628e4adef5733aa11898388d49b2152edb99aedddb3758a17e",
    "mymanah\\journal.py": "208b4a7a8ae9614e96ccac5080291111290f8542b9d496b679e446230b1d2c4a",
    "mymanah\\models.py": "6d9fe0656b4a61bfea1775049ded1c5710afdc37400fbd9c42cf2ac7a15aecd1",
    "mymanah\\parse_pdf.py": "15080dce0aef6df50015b7dbaa5db62c93e415068e084c3b15bc58f1945e3b6a",
    "mymanah\\policy.py": "90d97e137ceeedbd67c78f081bec935908e047f90f6d06c2cd660a3d433e45da",
    "mymanah\\rag.py": "c65563822d39c0d41c1d713a0460241a6e2dba2be8519770c93c5878860e5784",
    "mymanah\\schemas.py": "199d2b65faadc5bf30b449e7a120f4734cdd0ce049c68d81752e44edec8d4ee4",
    "mymanah\\storage.py": "2caa3eabc6f4e94c59d0bbc2a3f2d3bfa01143e021c9bab100dc391b9a944d97",
    "mymanah\\text.py": "3692834be947659176f9fee71f0edde4d362e9c54376e40290fe810ad0c06dd3"
  }
}
```
