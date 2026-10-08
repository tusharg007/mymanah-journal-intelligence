Subject: Generative AI & Machine Learning Engineer Intern Assignment - Tushar

Dear Rakesh,

Thank you for the opportunity. I have completed the assignment and am sharing my implementation:

- [GitHub repository](https://github.com/tusharg007/mymanah-journal-intelligence/tree/submission-v1)
- [2:05 policy-5 walkthrough](https://github.com/tusharg007/mymanah-journal-intelligence/blob/submission-v1/docs/walkthrough-short.mp4)
- [Approach, results and limitations](https://github.com/tusharg007/mymanah-journal-intelligence/blob/submission-v1/docs/SUBMISSION.md)

Reviewed commit: submission-v1

I built structured journal analysis and PDF question answering with verbatim page-level citations and evidence-based abstention. Only pinned, local Hugging Face models run: RoBERTa, DeBERTa NLI, E5 and Qwen3 4B through Ollama. The application uses FastAPI, React, isolated PDF parsing and principal-scoped persistence.

After the README's Windows dependency setup, with Ollama running, the three-command quick start is:

```powershell
.venv\Scripts\python.exe scripts\bootstrap.py --generator qwen4b
.venv\Scripts\python.exe scripts\doctor.py
.venv\Scripts\python.exe scripts\start.py
```

A Linux CPU Docker profile is also included. Open http://127.0.0.1:8000. Bootstrap downloads models; inference runs locally afterward. All 129 deterministic tests pass. Recorded timings are from my tested GPU laptop, not a CPU-only guarantee.

I assume English journals and text-based English PDFs. OCR and Hindi/Hinglish are not implemented. Screening and confidence are uncalibrated, non-clinical outputs. Fresh testing missed two screening cases: some passive-ideation phrasing can be rated LOW or MEDIUM instead of HIGH. AI-assisted expectations and limitations are disclosed in the notes.

Best regards,
Tushar
