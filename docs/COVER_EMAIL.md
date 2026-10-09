Subject: Generative AI & Machine Learning Engineer Intern Assignment - Tushar

Dear Rakesh,

Thank you for the opportunity. I have completed the assignment and am sharing my implementation:

- [GitHub repository](https://github.com/tusharg007/mymanah-journal-intelligence/tree/submission-v2)
- [Full desktop walkthrough (8:09)](https://github.com/tusharg007/mymanah-journal-intelligence/blob/submission-v2/docs/walkthrough-desktop.mp4)
- [Approach, results and limitations](https://github.com/tusharg007/mymanah-journal-intelligence/blob/submission-v2/docs/SUBMISSION.md)

Reviewed commit: submission-v2

I built structured journal analysis and PDF question answering with verbatim page-level citations and evidence-based abstention. Only pinned, local Hugging Face models run: RoBERTa, DeBERTa NLI, E5 and Qwen3 4B through Ollama. No hosted LLM APIs are used. The application uses FastAPI, React, isolated PDF parsing and principal-scoped persistence.

After the README's Windows dependency setup, with Ollama running, the three-command quick start is:

```powershell
.venv\Scripts\python.exe scripts\bootstrap.py --generator qwen4b
.venv\Scripts\python.exe scripts\doctor.py
.venv\Scripts\python.exe scripts\start.py
```

A Linux CPU Docker profile is also included. Open http://127.0.0.1:8000. Bootstrap downloads models; inference runs locally afterward. All 129 deterministic tests pass. Recorded timings are from my tested GPU laptop, not a CPU-only guarantee.

The current version supports English journals and English PDFs with selectable text, not scanned PDFs or Hindi/Hinglish. Risk labels and confidence scores are estimates, not clinical assessments. In testing, two concerning entries received LOW or MEDIUM when HIGH was expected. These expectations were AI-assisted, not clinical ground truth. The linked notes include both entries and the remaining limitations.

Best regards,
Tushar
