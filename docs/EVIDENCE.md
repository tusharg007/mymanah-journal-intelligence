# Evidence Ledger

Final inference policy: **journal-policy-5**, frozen after W1-W8. The
[fresh report](../reports/UNSEEN_HOPELESSNESS_8.md) records exact inputs, outputs,
timings and source-byte fingerprints. No inference policy, model, prompt,
confidence or summary-verification changes followed that assessment.

Stages reuse inputs and must not be added together as independent evidence.
AI-assisted predictions and engineering annotations are not independent clinical
ground truth. Historical figures do not measure the final tuned policy.

## Journal Evidence by Stage

| Stage | Policy / Scope | Actual Results | Source |
| --- | --- | --- | --- |
| Generator comparison | Before policy 3; 50 development journals and 30 PDF questions | 4B: 49/50 valid journals, 30/30 question responses; 1.5B: 41/50, 21/30 | [Comparison](../reports/generator-comparison.json) |
| Original held-out | Before policy 3; 100 provisional English cases | 96 valid; sentiment 95/100, emotion 93/100, risk 81/100 including errors; MEDIUM recall 13/28 | [Frozen measurements](../reports/heldout-qwen4b.json) |
| Self-test pack | Before policy 3; 76 AI-assisted predicted-expectation cases | Original errors and provisional mood guesses retained; mood guesses are not label failures | [Original pack](../reports/REVIEWER_TEST_PACK.md) |
| Seen development | Policy 3; 20 pack journals and development regressions | 20/20 valid pack responses, 19/20 specified-label matches; J14 emotion disagreement | [Policy 3](../reports/JOURNAL_POLICY3_REGRESSION.md) |
| Seen development | Policy 4; 20 pack journals, four J1 regressions and long01 | 25 valid, all generated summaries; 19/20 pack label matches; J2/J12 confidence 0.9773/0.9736 | [Policy 4](../reports/JOURNAL_POLICY4_REGRESSION.md) |
| Original U1-U10 | Policy 4; AI-assisted inputs run once before tuning on results | 10 valid, 8/10 specified-label matches; U6 anger/MEDIUM and U10 MEDIUM missed predicted HIGH | [Original unseen assessment](../reports/UNSEEN_REVIEW_10.md) |
| Safety diagnostic | Policy 4; U6/U10 and U7-U9 controls | U6/U10 hopelessness 0.842/0.995, overwhelm 0.628/0.572; the 0.65 distress cutoff blocked HIGH, not a persistence-and-impairment conjunction | [Pre-change signals](../reports/policy4-hopelessness-diagnostic.json) |
| Seen follow-up | Policy 5; 25 prior development requests plus now-seen U6-U10 | 30 valid, 28/30 specified-label matches; U6/J14 emotion errors remain; all 25 original risk labels unchanged | [Policy 5](../reports/JOURNAL_POLICY5_REGRESSION.md) |
| J12 style follow-up | Policy 5; one seen input | Concrete generated summary in 3.686 s after one repair; first abstract response preserved | [Full response](../reports/policy5-summary-followup.json) |
| Fresh W1-W8 | Policy 5; eight AI-assisted inputs, once without HTTP retries or subsequent tuning | 8 valid, 6/8 specified-label matches; W2 MEDIUM and W3 LOW instead of HIGH; no false HIGH for W4/W5/W7 | [Fresh report](../reports/UNSEEN_HOPELESSNESS_8.md) |

U1-U10 was unseen only at its original policy-4 assessment. U6-U10 became seen
inputs for the requested policy-5 correction. W1-W8 was not used to tune policy 5;
the two fresh misses remain unchanged. No broad generalization claim follows
from this eight-input sample. [Fresh raw data](../reports/unseen-hopelessness-8.json).

W6/W7 used verified extractive fallbacks after two generation/verification
attempts; six other W summaries were generated. W5 inferred male gender without
source support. W7 returned negative/anger for a mundane umbrella entry; its
supplied expectation prescribed only LOW risk, not sentiment or emotion. W2/W3
both had 0.99 sad-emotion confidence despite incorrect risk priority. These
limitations are retained rather than hidden by the six-of-eight expectation count.

## Timing Scope

All short-entry and long-entry figures below are observations on the tested GPU
laptop with CPU classifiers and GPU-offloaded generation, not CPU-only guarantees.

| Stage | Short-Entry p50 / p95 | Long Entries |
| --- | --- | --- |
| Policy-4 seen | 2.467 / 2.706 s, 19 samples | J20 23.807809 s; 512-word long01 20.539648 s |
| Policy-4 U1-U10 | 1.829 / 2.241 s, 10 samples | Not measured |
| Policy-5 seen | 2.501 / 2.747 s, 19 samples | J20 24.070286 s; long01 20.934335 s |
| Fresh W1-W8 | 2.134 / 3.482 s, 8 samples | Not measured; first request may include a model reload |

Earlier equal J20/long01 13.406-second values remain historical rounded
observations. Later reports use independent nanosecond intervals and input hashes.
Frozen pre-policy-3 held-out p50/p95 was 11.71/18.39 s. The original 4B versus
1.5B successful development p50/p95 was 11.23/15.56 versus 2.25/2.54 s; RAM and
dependency versions differed, so this was not a controlled speed comparison.

The historical Linux CPU smoke journal took **19.69 s**, with fresh two-page READY
in 0.898 s. Those are individual pre-policy-3 observations, not current percentiles.
CPU-only long journals can exhaust the 60-second deadline; Linux GPU execution
is unverified.

## CI and Engineering Checks

[checks.yml](../.github/workflows/checks.yml) explicitly triggers on **push and
pull_request**. The jobs are `test` and `container`; configured pull-request
coverage is not a claim that a pull-request run was executed.

- Policy-5 implementation commit `3b9f2e9`: [green push run](https://github.com/tusharg007/mymanah-journal-intelligence/actions/runs/37854784087).
- Policy-5 evidence commit `ac66336`: [green push run](https://github.com/tusharg007/mymanah-journal-intelligence/actions/runs/37855946849).
- Pinned runner/actions commit `cf0d2b9`: [green push run](https://github.com/tusharg007/mymanah-journal-intelligence/actions/runs/37857697838), both jobs passed.
- Both runners are `ubuntu-24.04`. Verified full-SHA pins use Node 24: [checkout v5](https://github.com/actions/checkout/blob/fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09/action.yml), [setup-python v6](https://github.com/actions/setup-python/blob/ece7cb06caefa5fff74198d8649806c4678c61a1/action.yml), [setup-node v6](https://github.com/actions/setup-node/blob/249970729cb0ef3589644e2896645e5dc5ba9c38/action.yml). Application Python 3.11 and Node 22 are unchanged.
- Windows: 129 deterministic tests passed; two actual-model smoke tests passed separately. Linux CI checks lint, deterministic tests, frontend production build, CPU image build, imports and fail-closed non-root startup. It does not run full-model inference on every push.
- The separate [manually dispatched CPU Docker integration](https://github.com/tusharg007/mymanah-journal-intelligence/actions/runs/37673144901) passed two actual-model tests before policy 3. It is distinct from ordinary push-triggered engineering checks.

## PDF and Operational Evidence

All seven [targeted PDF checks](../reports/POLICY4_CONDITION_REGRESSION.md) matched
predicted status/fact/page checks after fresh HTTP 201 READY in 1.329 s. R2/R8/R18
preserve cap/expiry/approval conditions. R12 returns verified sick leave as PARTIAL,
retains its certificate condition and names missing stock options. R14 abstains
without citations before generation in 0.062 s. This is not another 76-case pass count.

The earlier new ten-page PDF reached READY in 0.865 s. Expected-page retrieval
hit 27/27 answerable/partial cases; automated end-to-end matches were 27/30. One
mismatch is a singular/plural matcher false negative; two are conservative full
abstentions instead of partial answers. [Original RAG benchmark](../reports/rag-qwen4b.json).

RoBERTa's original fine-tuned sentiment baseline matched 99/100 annotations,
versus NLI 97/100. Counts, macro metrics, confusion matrices and uncertainty are
retained; incompatible emotion taxonomies were not presented as a seven-class comparison.

Real browser workflows, citation inspection, nonblank PDF canvas, page navigation,
[four-width responsive checks](../reports/responsive-layout.json),
[offline API-process smoke](../reports/offline-smoke.json) and
[restored-index/keyed-isolation rehearsal](../reports/backup-restore-smoke.json)
passed. Offline instrumentation covered the API process, not an OS firewall or
every subprocess. Embedded storage and one process are not a distributed deployment.

## Media and Residual Risk

[Walkthrough guide](WALKTHROUGH.md) and [compiled recording results](VIDEO_TEST_RESULTS.md)
identify each video's policy and actual outputs. The prior
[26-link anonymous check](../reports/submission-link-check.json) checked commit
`3b9f2e9`, with media sizes and GitHub rate-limit backoffs; it is not presented as
a check of later edited documents or replaced media.

The original held-out set, original U assessment, approved implementation plan
and older measured outputs are preserved. Screening is not clinically validated;
confidence/mood are uncalibrated, and verification can accept unsupported details
or reject valid paraphrases. [Security notes](../reports/SECURITY.md) retain scoped
Chroma advisories and the CPU-Torch audit coverage gap. No zero-vulnerability,
zero-hallucination or zero-bug claim is made. Public hosting needs additional TLS,
proxy, secret-management and operational controls. No public deployment is claimed.
