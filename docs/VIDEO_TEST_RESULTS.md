# Video Test Results

This report compiles the actual model and document responses visible in the
[desktop walkthrough](walkthrough-desktop.mp4) and [mobile walkthrough](walkthrough-mobile.mp4).
Inputs come from an AI-assisted self-test pack with predicted expectations supplied
by the candidate. These predictions are not ground truth. Mood ranges are provisional
guesses and are recorded separately from sentiment, emotion and risk agreement.
Confidence is the system's uncalibrated score, not a probability of correctness.

## Coverage

| Workflow | Desktop | Mobile |
| --- | ---: | ---: |
| Journal analysis | 11 inputs | 5 inputs |
| PDF questions | 2 supported, 1 unsupported | 2 supported, 1 unsupported |
| Uploaded document | Fresh upload, READY | Reused indexed document, READY |

The videos contain 16 journal requests across 11 distinct test inputs: five inputs
are repeated in the mobile workflow. The PDF is the three-page `Employee_Handbook_Test.pdf`.

## Journal Analysis

Workflow endpoint: `POST /analyze-journal`, with request body `{"text": "entry"}`.

The predicted fields below reproduce the self-test expectations. Actual values and
summaries come from each recorded HTTP 200 response.

### J1: Prolonged distress

> **Input:** I haven’t been sleeping properly for the last few weeks. I feel stressed about work and sometimes feel like giving up.

| Field | Predicted expectation | Desktop result | Mobile result |
| --- | --- | --- | --- |
| Sentiment | negative | negative | negative |
| Emotion | stress | stress | stress |
| Mood score (provisional range) | 1–4 | 2/10 | 2/10 |
| Crisis risk | HIGH | HIGH | HIGH |
| Confidence | Not specified | 0.8390 | 0.8390 |
| HTTP / latency | HTTP 200 | HTTP 200 / 2.25s | HTTP 200 / 2.38s |

**Desktop summary:** I haven’t been sleeping properly for the last few weeks. I feel stressed about work and sometimes feel like giving up.

**Mobile summary:** I haven’t been sleeping properly for the last few weeks. I feel stressed about work and sometimes feel like giving up.

**Predicted-label comparison:** Desktop and mobile matched the predicted sentiment, emotion and risk labels.

**Mood calibration:** The predicted range is provisional and is not counted as a failed label check.

Video result: desktop 00:15; mobile 00:15.

### J2: Positive achievement

> **Input:** I finished my project today and feel pleased with my progress.

| Field | Predicted expectation | Desktop result | Mobile result |
| --- | --- | --- | --- |
| Sentiment | positive | positive | positive |
| Emotion | happy | happy | happy |
| Mood score (provisional range) | 7–10 | 9/10 | 9/10 |
| Crisis risk | LOW | LOW | LOW |
| Confidence | Not specified | 0.2558 | 0.2558 |
| HTTP / latency | HTTP 200 | HTTP 200 / 1.84s | HTTP 200 / 1.83s |

**Desktop summary:** I finished my project today. I feel pleased with my progress.

**Mobile summary:** I finished my project today. I feel pleased with my progress.

**Predicted-label comparison:** Desktop and mobile matched the predicted sentiment, emotion and risk labels.

**Mood calibration:** The predicted range is provisional and is not counted as a failed label check.

Video result: desktop 00:36; mobile 00:36.

### J3: An ordinary day

> **Input:** Today was an ordinary day. I went to work, had lunch with a colleague, and came home around six.

| Field | Predicted expectation | Desktop result | Mobile result |
| --- | --- | --- | --- |
| Sentiment | neutral | neutral | - |
| Emotion | neutral | neutral | - |
| Mood score (provisional range) | 5–7 | 7/10 | - |
| Crisis risk | LOW | LOW | - |
| Confidence | Not specified | 0.7422 | - |
| HTTP / latency | HTTP 200 | HTTP 200 / 3.89s | - |

**Desktop summary:** I went to work and had lunch with a colleague. Today was an ordinary day.

**Predicted-label comparison:** Desktop matched the predicted sentiment, emotion and risk labels.

**Mood calibration:** The predicted range is provisional and is not counted as a failed label check.

Video result: desktop 01:01; mobile not shown.

### J4: Anger after criticism

> **Input:** My manager criticized my work in front of the whole team and I am furious. I can’t believe how disrespectful he was.

| Field | Predicted expectation | Desktop result | Mobile result |
| --- | --- | --- | --- |
| Sentiment | negative | negative | - |
| Emotion | anger | anger | - |
| Mood score (provisional range) | 2–4 | 3/10 | - |
| Crisis risk | LOW | LOW | - |
| Confidence | Not specified | 0.9364 | - |
| HTTP / latency | HTTP 200 | HTTP 200 / 2.16s | - |

**Desktop summary:** My manager criticized my work in front of the whole team. I can’t believe how disrespectful he was.

**Predicted-label comparison:** Desktop matched the predicted sentiment, emotion and risk labels.

**Mood calibration:** The predicted range is provisional and is not counted as a failed label check.

Video result: desktop 01:26; mobile not shown.

### J5: Interview anxiety

> **Input:** I keep worrying that something will go wrong at my interview tomorrow. My heart is racing and I cannot stop overthinking.

| Field | Predicted expectation | Desktop result | Mobile result |
| --- | --- | --- | --- |
| Sentiment | negative | negative | negative |
| Emotion | anxiety | anxiety | anxiety |
| Mood score (provisional range) | 2–4 | 3/10 | 3/10 |
| Crisis risk | LOW or MEDIUM | MEDIUM | MEDIUM |
| Confidence | Not specified | 0.8931 | 0.8931 |
| HTTP / latency | HTTP 200 | HTTP 200 / 1.99s | HTTP 200 / 2.19s |

**Desktop summary:** I worry something will go wrong at my interview tomorrow. My heart is racing and I cannot stop overthinking.

**Mobile summary:** I worry something will go wrong at my interview tomorrow. My heart is racing and I cannot stop overthinking.

**Predicted-label comparison:** Desktop and mobile matched the predicted sentiment, emotion and risk labels.

**Mood calibration:** The predicted range is provisional and is not counted as a failed label check.

Video result: desktop 01:50; mobile 01:01.

### J6: Workload stress

> **Input:** I have five deadlines this week and no time to breathe. I feel completely overwhelmed by the workload.

| Field | Predicted expectation | Desktop result | Mobile result |
| --- | --- | --- | --- |
| Sentiment | negative | negative | - |
| Emotion | stress | stress | - |
| Mood score (provisional range) | 2–4 | 3/10 | - |
| Crisis risk | LOW or MEDIUM | MEDIUM | - |
| Confidence | Not specified | 0.8283 | - |
| HTTP / latency | HTTP 200 | HTTP 200 / 2.04s | - |

**Desktop summary:** I have five deadlines this week and no time to breathe. I feel completely overwhelmed by the workload.

**Predicted-label comparison:** Desktop matched the predicted sentiment, emotion and risk labels.

**Mood calibration:** The predicted range is provisional and is not counted as a failed label check.

Video result: desktop 02:14; mobile not shown.

### J7: Grief

> **Input:** I miss my grandmother so much today. I cried for most of the evening looking at her old photos.

| Field | Predicted expectation | Desktop result | Mobile result |
| --- | --- | --- | --- |
| Sentiment | negative | negative | negative |
| Emotion | sad | sad | sad |
| Mood score (provisional range) | 2–4 | 4/10 | 4/10 |
| Crisis risk | LOW | LOW | LOW |
| Confidence | Not specified | 0.6963 | 0.6963 |
| HTTP / latency | HTTP 200 | HTTP 200 / 3.63s | HTTP 200 / 3.60s |

**Desktop summary:** I miss my grandmother so much today. I cried for most of the evening looking at her old photos.

**Mobile summary:** I miss my grandmother so much today. I cried for most of the evening looking at her old photos.

**Predicted-label comparison:** Desktop and mobile matched the predicted sentiment, emotion and risk labels.

**Mood calibration:** The predicted range is provisional and is not counted as a failed label check.

Video result: desktop 02:39; mobile 01:26.

### J8: Fear after a threat

> **Input:** Someone followed me home last night and I’m terrified. I keep checking the locks and I am afraid to go out.

| Field | Predicted expectation | Desktop result | Mobile result |
| --- | --- | --- | --- |
| Sentiment | negative | negative | - |
| Emotion | fear | fear | - |
| Mood score (provisional range) | 1–4 | 3/10 | - |
| Crisis risk | LOW or MEDIUM | LOW | - |
| Confidence | Not specified | 0.8846 | - |
| HTTP / latency | HTTP 200 | HTTP 200 / 2.16s | - |

**Desktop summary:** Someone followed me home last night and I am terrified. I keep checking the locks and I am afraid to go out.

**Predicted-label comparison:** Desktop matched the predicted sentiment, emotion and risk labels.

**Mood calibration:** The predicted range is provisional and is not counted as a failed label check.

Video result: desktop 03:03; mobile not shown.

### J12: Negation: not sad

> **Input:** I am not sad at all today. Honestly I feel great and everything is going well.

| Field | Predicted expectation | Desktop result | Mobile result |
| --- | --- | --- | --- |
| Sentiment | positive | positive | - |
| Emotion | happy | happy | - |
| Mood score (provisional range) | 8–10 | 9/10 | - |
| Crisis risk | LOW | LOW | - |
| Confidence | Not specified | 0.0026 | - |
| HTTP / latency | HTTP 200 | HTTP 200 / 2.08s | - |

**Desktop summary:** I am not sad at all today. Honestly I feel great and everything is going well.

**Predicted-label comparison:** Desktop matched the predicted sentiment, emotion and risk labels.

**Mood calibration:** The predicted range is provisional and is not counted as a failed label check.

Video result: desktop 03:25; mobile not shown.

### J13: Mixed excitement and worry

> **Input:** I got the promotion and I’m thrilled, but I’m also nervous about the extra responsibility.

| Field | Predicted expectation | Desktop result | Mobile result |
| --- | --- | --- | --- |
| Sentiment | positive (neutral ok) | positive | - |
| Emotion | happy (anxiety ok) | anxiety | - |
| Mood score (provisional range) | 5–8 | 7/10 | - |
| Crisis risk | LOW | LOW | - |
| Confidence | Not specified | 0.8637 | - |
| HTTP / latency | HTTP 200 | HTTP 200 / 2.33s | - |

**Desktop summary:** I received a promotion and feel thrilled about it. I am nervous about the extra responsibility it brings.

**Predicted-label comparison:** Desktop matched the predicted sentiment, emotion and risk labels.

**Mood calibration:** The predicted range is provisional and is not counted as a failed label check.

Video result: desktop 03:48; mobile not shown.

### J9: Explicit risk language

> **Input:** I don’t want to be alive anymore. I have been thinking about ending my life and I can’t see any way out.

| Field | Predicted expectation | Desktop result | Mobile result |
| --- | --- | --- | --- |
| Sentiment | negative | negative | negative |
| Emotion | any | sad | sad |
| Mood score (provisional range) | 1–2 | 2/10 | 2/10 |
| Crisis risk | HIGH | HIGH | HIGH |
| Confidence | Not specified | 0.9333 | 0.9333 |
| HTTP / latency | HTTP 200 | HTTP 200 / 2.33s | HTTP 200 / 2.35s |

**Desktop summary:** I don’t want to be alive anymore. I have been thinking about ending my life and I can’t see any way out.

**Mobile summary:** I don’t want to be alive anymore. I have been thinking about ending my life and I can’t see any way out.

**Predicted-label comparison:** Desktop and mobile matched the predicted sentiment, emotion and risk labels.

**Mood calibration:** The predicted range is provisional and is not counted as a failed label check.

Video result: desktop 04:12; mobile 01:50.

## Document Question Answering

Workflow endpoints: `POST /documents`, then `POST /documents/{document_id}/questions`.

Both workflows selected the same three-page handbook. Desktop uploaded a fresh
copy and received HTTP 201 with status `READY`, three pages and three chunks.
Mobile reused that indexed document. Both then asked the same three questions.

| Input question | Workflow | HTTP / status | Actual answer | Citation and source quote | Latency |
| --- | --- | --- | --- | --- | ---: |
| What is the annual leave allowance? | Desktop | HTTP 200 / `ANSWERED` | The annual leave allowance is 24 days per calendar year. [1]<br>Up to 5 unused days may be carried into the next year and must be used by 31 March. [2] | Page 2: “Full-time employees receive 24 days of paid annual leave per calendar<br>year.” | 5.75s |
| What is the notice period during probation? | Desktop | HTTP 200 / `ANSWERED` | The notice period during probation is 15 days. [1] | Page 3: “Notice period: The notice period is 60 days after confirmation and 15 days during<br>probation.” | 3.30s |
| What is the stock option vesting schedule? | Desktop | HTTP 200 / `INSUFFICIENT_EVIDENCE` | The uploaded document does not provide sufficient evidence to answer this question. | None (no citations) | - |
| What is the annual leave allowance? | Mobile | HTTP 200 / `ANSWERED` | The annual leave allowance is 24 days per calendar year. [1]<br>Up to 5 unused days may be carried into the next year and must be used by 31 March. [2] | Page 2: “Full-time employees receive 24 days of paid annual leave per calendar<br>year.” | 4.97s |
| What is the notice period during probation? | Mobile | HTTP 200 / `ANSWERED` | The notice period during probation is 15 days. [1] | Page 3: “Notice period: The notice period is 60 days after confirmation and 15 days during<br>probation.” | 2.81s |
| What is the stock option vesting schedule? | Mobile | HTTP 200 / `INSUFFICIENT_EVIDENCE` | The uploaded document does not provide sufficient evidence to answer this question. | None (no citations) | - |

The annual-leave answer gives the 24-day allowance and cites page 2. The probation answer gives
15 days and cites page 3. The unsupported stock-option question is declined without
citations. These observed answers should be read alongside the full 76-case
[AI-assisted self-test report](../reports/REVIEWER_TEST_PACK.md), which retains original
document questions and mismatches. The separate [policy-condition regression](../reports/POLICY_CONDITION_REGRESSION.md)
checks carry-over caps/expiry and approval requirements after the correction.

## Recording Details

| Recording | Viewport | Duration | Journal cases |
| --- | ---: | ---: | ---: |
| Desktop | 1440 x 960 | 6.13 min | 11 |
| Mobile | 390 x 844 | 3.69 min | 5 |

Journal processing ran at normal playback speed. Completed results remain visible
for reading; captions are embedded in the video. The raw response payloads, expected
annotations, exact timestamps and per-request timings are in
[`walkthrough-recording.json`](../reports/walkthrough-recording.json).
Regenerate this file with `python scripts/export_video_results.py`.
