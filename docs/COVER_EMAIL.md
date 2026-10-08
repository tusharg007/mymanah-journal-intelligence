Subject: Generative AI & Machine Learning Engineer Intern Assignment - Tushar

Dear Rakesh,

Thank you for the opportunity. I have completed the assignment and am sharing my implementation:

- [GitHub repository](https://github.com/tusharg007/mymanah-journal-intelligence)
- [2:05 policy-5 walkthrough](https://github.com/tusharg007/mymanah-journal-intelligence/blob/main/docs/walkthrough-short.mp4)
- [Approach, results and limitations](https://github.com/tusharg007/mymanah-journal-intelligence/blob/main/docs/SUBMISSION.md)

I built two workflows: structured journal analysis and PDF question answering with page-level, verbatim citations and evidence-based abstention. The application uses only pinned, locally run Hugging Face models: RoBERTa, DeBERTa NLI, E5 and Qwen3 4B through Ollama. FastAPI, React, isolated PDF parsing and principal-scoped persistence support the implementation.

After the README's Windows dependency setup, with Ollama running, the three-command quick start is:

```powershell
.venv\Scripts\python.exe scripts\bootstrap.py --generator qwen4b
.venv\Scripts\python.exe scripts\doctor.py
.venv\Scripts\python.exe scripts\start.py
```

The interface then opens at http://127.0.0.1:8000. Bootstrap requires model downloads; inference runs locally afterward. The deterministic suite passes 129 tests. Recorded short-entry timings are from my tested GPU laptop, not a CPU-only guarantee.

I assume English journals and text-based English PDFs. There is no OCR; Hindi/Hinglish is not implemented. Screening and confidence are uncalibrated, non-clinical outputs. Fresh testing retained two screening misses; limitations and AI-assisted test expectations are disclosed in the linked notes.

Best regards,
Tushar
