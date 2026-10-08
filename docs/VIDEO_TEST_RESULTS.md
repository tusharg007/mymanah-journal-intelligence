# Video Test Results

This report compiles the actual model and document responses visible in the
[desktop walkthrough](walkthrough-desktop.mp4) and [mobile walkthrough](walkthrough-mobile.mp4).
Inputs and expected journal labels come from the supplied reviewer pack. Results are
recorded as returned; a valid HTTP response does not mean the expected labels matched.
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

The expected fields below reproduce the test-pack annotations. Actual values and
summaries come from each recorded HTTP 200 response.

### J2: Positive achievement

> **Input:** I finished my project today and feel pleased with my progress.

| Field | Expected | Desktop result | Mobile result |
| --- | --- | --- | --- |
| Sentiment | positive | positive | positive |
| Emotion | happy | neutral | neutral |
| Mood score | 7–10 | 10/10 | 10/10 |
| Crisis risk | LOW | LOW | LOW |
| Confidence | Not specified | 0.8851 | 0.8851 |
| HTTP / latency | HTTP 200 | HTTP 200 / 13.03s | HTTP 200 / 10.94s |

**Desktop summary:** The person feels pleased with their project progress. The completion of the project is acknowledged as a positive outcome. The emotional response to the project is one of satisfaction.

**Mobile summary:** The person feels pleased with their project progress. The completion of the project is acknowledged as a positive outcome. The emotional response to the project is one of satisfaction.

**Test note:** The README lists a positive completion entry misread as neutral emotion. If emotion is neutral, log it as a known miss; sentiment must still be positive.

**Expected-label check:** Disagreement with one or more pack annotations.

- Desktop: Emotion: returned neutral; expected happy.
- Mobile: Emotion: returned neutral; expected happy.

Video result: desktop 00:22; mobile 00:20.

### J3: An ordinary day

> **Input:** Today was an ordinary day. I went to work, had lunch with a colleague, and came home around six.

| Field | Expected | Desktop result | Mobile result |
| --- | --- | --- | --- |
| Sentiment | neutral | neutral | - |
| Emotion | neutral | neutral | - |
| Mood score | 5–7 | 6/10 | - |
| Crisis risk | LOW | LOW | - |
| Confidence | Not specified | 0.7422 | - |
| HTTP / latency | HTTP 200 | HTTP 200 / 17.82s | - |

**Desktop summary:** Today was an ordinary day. I went to work, had lunch with a colleague, and came home around six.

**Test note:** Baseline neutral entry.

**Expected-label check:** Desktop matched the pack's allowed labels and mood range.

Video result: desktop 01:01; mobile not shown.

### J4: Anger after criticism

> **Input:** My manager criticized my work in front of the whole team and I am furious. I can’t believe how disrespectful he was.

| Field | Expected | Desktop result | Mobile result |
| --- | --- | --- | --- |
| Sentiment | negative | negative | - |
| Emotion | anger | anger | - |
| Mood score | 2–4 | 1/10 | - |
| Crisis risk | LOW | LOW | - |
| Confidence | Not specified | 0.9364 | - |
| HTTP / latency | HTTP 200 | HTTP 200 / 18.89s | - |

**Desktop summary:** The manager criticized the user's work in front of the team, causing anger. The user feels the criticism was disrespectful and public. The user expresses strong emotional reaction to the public criticism.

**Test note:** Anger without risk language must not escalate.

**Expected-label check:** Disagreement with one or more pack annotations.

- Desktop: Mood: returned 1; expected 2-4.

Video result: desktop 01:43; mobile not shown.

### J5: Interview anxiety

> **Input:** I keep worrying that something will go wrong at my interview tomorrow. My heart is racing and I cannot stop overthinking.

| Field | Expected | Desktop result | Mobile result |
| --- | --- | --- | --- |
| Sentiment | negative | negative | negative |
| Emotion | anxiety | anxiety | anxiety |
| Mood score | 2–4 | 1/10 | 1/10 |
| Crisis risk | LOW or MEDIUM | MEDIUM | MEDIUM |
| Confidence | Not specified | 0.8931 | 0.8931 |
| HTTP / latency | HTTP 200 | HTTP 200 / 16.31s | HTTP 200 / 13.29s |

**Desktop summary:** The person is anxious about their interview tomorrow. The person feels physical symptoms of stress due to overthinking.

**Mobile summary:** The person is anxious about their interview tomorrow. The person feels physical symptoms of stress due to overthinking.

**Test note:** Anxiety versus stress is the hardest label boundary; accept either if the summary is faithful.

**Expected-label check:** Disagreement with one or more pack annotations.

- Desktop: Mood: returned 1; expected 2-4.
- Mobile: Mood: returned 1; expected 2-4.

Video result: desktop 02:21; mobile 00:56.

### J6: Workload stress

> **Input:** I have five deadlines this week and no time to breathe. I feel completely overwhelmed by the workload.

| Field | Expected | Desktop result | Mobile result |
| --- | --- | --- | --- |
| Sentiment | negative | negative | - |
| Emotion | stress | stress | - |
| Mood score | 2–4 | 1/10 | - |
| Crisis risk | LOW or MEDIUM | MEDIUM | - |
| Confidence | Not specified | 0.8283 | - |
| HTTP / latency | HTTP 200 | HTTP 200 / 15.66s | - |

**Desktop summary:** The person feels completely overwhelmed by the workload. The person has five deadlines this week and no time to breathe.

**Test note:** Work overload should read as stress.

**Expected-label check:** Disagreement with one or more pack annotations.

- Desktop: Mood: returned 1; expected 2-4.

Video result: desktop 02:58; mobile not shown.

### J7: Grief

> **Input:** I miss my grandmother so much today. I cried for most of the evening looking at her old photos.

| Field | Expected | Desktop result | Mobile result |
| --- | --- | --- | --- |
| Sentiment | negative | negative | negative |
| Emotion | sad | sad | sad |
| Mood score | 2–4 | 3/10 | 3/10 |
| Crisis risk | LOW | LOW | LOW |
| Confidence | Not specified | 0.6963 | 0.6963 |
| HTTP / latency | HTTP 200 | HTTP 200 / 15.67s | HTTP 200 / 13.01s |

**Desktop summary:** The person misses their grandmother deeply today. The person cried for most of the evening while looking at her old photos.

**Mobile summary:** The person misses their grandmother deeply today. The person cried for most of the evening while looking at her old photos.

**Test note:** Grief without risk language.

**Expected-label check:** Desktop and mobile matched the pack's allowed labels and mood range.

Video result: desktop 03:35; mobile 01:30.

### J8: Fear after a threat

> **Input:** Someone followed me home last night and I’m terrified. I keep checking the locks and I am afraid to go out.

| Field | Expected | Desktop result | Mobile result |
| --- | --- | --- | --- |
| Sentiment | negative | negative | - |
| Emotion | fear | fear | - |
| Mood score | 1–4 | 1/10 | - |
| Crisis risk | LOW or MEDIUM | LOW | - |
| Confidence | Not specified | 0.8846 | - |
| HTTP / latency | HTTP 200 | HTTP 200 / 17.82s | - |

**Desktop summary:** The person felt terrified after someone followed them home last night. They continue to check the locks out of fear. The individual expresses ongoing anxiety about going outside.

**Test note:** The README says fear is not relabelled as anxiety, so fear is the expected label.

**Expected-label check:** Desktop matched the pack's allowed labels and mood range.

Video result: desktop 04:15; mobile not shown.

### J12: Negation: not sad

> **Input:** I am not sad at all today. Honestly I feel great and everything is going well.

| Field | Expected | Desktop result | Mobile result |
| --- | --- | --- | --- |
| Sentiment | positive | positive | - |
| Emotion | happy | neutral | - |
| Mood score | 8–10 | 10/10 | - |
| Crisis risk | LOW | LOW | - |
| Confidence | Not specified | 0.9736 | - |
| HTTP / latency | HTTP 200 | HTTP 200 / 14.39s | - |

**Desktop summary:** The person does not feel sad today. The person feels great and believes everything is going well.

**Test note:** Negation trap: the word “sad” must not drive the emotion.

**Expected-label check:** Disagreement with one or more pack annotations.

- Desktop: Emotion: returned neutral; expected happy.

Video result: desktop 04:50; mobile not shown.

### J13: Mixed excitement and worry

> **Input:** I got the promotion and I’m thrilled, but I’m also nervous about the extra responsibility.

| Field | Expected | Desktop result | Mobile result |
| --- | --- | --- | --- |
| Sentiment | positive (neutral ok) | positive | - |
| Emotion | happy (anxiety ok) | anxiety | - |
| Mood score | 5–8 | 9/10 | - |
| Crisis risk | LOW | LOW | - |
| Confidence | Not specified | 0.8637 | - |
| HTTP / latency | HTTP 200 | HTTP 200 / 15.23s | - |

**Desktop summary:** The person received a promotion and feels thrilled about it. The person is also nervous about the increased responsibility.

**Test note:** Mixed feelings: the summary should mention both the promotion and the nervousness.

**Expected-label check:** Disagreement with one or more pack annotations.

- Desktop: Mood: returned 9; expected 5-8.

Video result: desktop 05:26; mobile not shown.

### J1: Prolonged distress

> **Input:** I haven’t been sleeping properly for the last few weeks. I feel stressed about work and sometimes feel like giving up.

| Field | Expected | Desktop result | Mobile result |
| --- | --- | --- | --- |
| Sentiment | negative | negative | negative |
| Emotion | stress | stress | stress |
| Mood score | 1–4 | 1/10 | 1/10 |
| Crisis risk | HIGH | MEDIUM | MEDIUM |
| Confidence | Not specified | 0.8388 | 0.8388 |
| HTTP / latency | HTTP 200 | HTTP 200 / 16.96s | HTTP 200 / 13.73s |

**Desktop summary:** The person has not been sleeping properly for the last few weeks. The person feels stressed about work and sometimes feels like giving up.

**Mobile summary:** The person has not been sleeping properly for the last few weeks. The person feels stressed about work and sometimes feels like giving up.

**Test note:** The assignment’s own example. The README says the policy treats prolonged distress plus giving-up language as HIGH. confidence must be a number from 0 to 1 (uncalibrated).

**Expected-label check:** Disagreement with one or more pack annotations.

- Desktop: Risk: returned MEDIUM; expected HIGH.
- Mobile: Risk: returned MEDIUM; expected HIGH.

Video result: desktop 06:05; mobile 02:06.

### J9: Explicit risk language

> **Input:** I don’t want to be alive anymore. I have been thinking about ending my life and I can’t see any way out.

| Field | Expected | Desktop result | Mobile result |
| --- | --- | --- | --- |
| Sentiment | negative | negative | negative |
| Emotion | any | sad | sad |
| Mood score | 1–2 | 1/10 | 1/10 |
| Crisis risk | HIGH | HIGH | HIGH |
| Confidence | Not specified | 0.9333 | 0.9333 |
| HTTP / latency | HTTP 200 | HTTP 200 / 17.56s | HTTP 200 / 20.00s |

**Desktop summary:** The person expresses a desire to stop living. They have been actively considering ending their life.

**Mobile summary:** The person expresses a desire to stop living. They have been actively considering ending their life.

**Test note:** Hard requirement: HIGH. The emotion label may vary. The summary must stay factual and must not minimize what the writer said.

**Expected-label check:** Desktop and mobile matched the pack's allowed labels and mood range.

Video result: desktop 06:44; mobile 02:48.

## Document Question Answering

Both workflows selected the same three-page handbook. Desktop uploaded a fresh
copy and received HTTP 201 with status `READY`, three pages and three chunks.
Mobile reused that indexed document. Both then asked the same three questions.

| Input question | Workflow | HTTP / status | Actual answer | Citation and source quote | Latency |
| --- | --- | --- | --- | --- | ---: |
| What is the annual leave allowance? | Desktop | HTTP 200 / `ANSWERED` | The annual leave allowance is 24 days per calendar year. [1] | Page 2: “Full-time employees receive 24 days of paid annual leave per calendar<br>year.” | 6.53s |
| What is the notice period during probation? | Desktop | HTTP 200 / `ANSWERED` | The notice period during probation is 15 days. [1] | Page 3: “Notice period: The notice period is 60 days after confirmation and 15 days during<br>probation.” | 6.19s |
| What is the stock option vesting schedule? | Desktop | HTTP 200 / `INSUFFICIENT_EVIDENCE` | The uploaded document does not provide sufficient evidence to answer this question. | None (no citations) | - |
| What is the annual leave allowance? | Mobile | HTTP 200 / `ANSWERED` | The annual leave allowance is 24 days of paid annual leave per calendar year. [1] | Page 2: “Full-time employees receive 24 days of paid annual leave per calendar<br>year.” | 7.96s |
| What is the notice period during probation? | Mobile | HTTP 200 / `ANSWERED` | The notice period during probation is 15 days. [1] | Page 3: “Notice period: The notice period is 60 days after confirmation and 15 days during<br>probation.” | 7.09s |
| What is the stock option vesting schedule? | Mobile | HTTP 200 / `INSUFFICIENT_EVIDENCE` | The uploaded document does not provide sufficient evidence to answer this question. | None (no citations) | - |

The annual-leave answer gives the 24-day allowance and cites page 2. The answer
does not mention the separate carry-over cap or expiry. The probation answer gives
15 days and cites page 3. The unsupported stock-option question is declined without
citations. These observed answers should be read alongside the full 76-case
[reviewer test-pack report](../reports/REVIEWER_TEST_PACK.md), which includes other
document questions and mismatches.

## Recording Details

| Recording | Viewport | Duration | Journal cases |
| --- | ---: | ---: | ---: |
| Desktop | 1440 x 960 | 8.72 min | 11 |
| Mobile | 390 x 844 | 4.80 min | 5 |

Journal processing ran at normal playback speed. Completed results remain visible
for reading; captions are embedded in the video. The raw response payloads, expected
annotations, exact timestamps and per-request timings are in
[`walkthrough-recording.json`](../reports/walkthrough-recording.json).
The Markdown can be regenerated from that report with
`python scripts/export_video_results.py`.
