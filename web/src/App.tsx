import { lazy, Suspense, useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { ArrowRight, Check, ChevronRight, ExternalLink, FileText, KeyRound, LoaderCircle, LogOut, NotebookPen, Plus, ShieldCheck, Trash2, X } from 'lucide-react';

type Journal = { sentiment: string; emotion: string; moodScore: number; summary: string; crisisRisk: string; confidence: number };
type Doc = { id: string; filename: string; state: string; pages: number; chunks: number; error: string | null };
type Citation = { document_id: string; filename: string; page: number; chunk_id: string; quote: string };
type Answer = { status: string; answer: string; citations: Citation[] };
type Health = { status: string; authEnabled: boolean; failure: string | null };
const PdfPreview = lazy(() => import('./PdfPreview'));

export default function App() {
  const [view, setView] = useState<'journal' | 'documents'>('journal');
  const [health, setHealth] = useState<Health | null>(null);
  const [key, setKey] = useState('');
  const [keyInput, setKeyInput] = useState('');
  const [text, setText] = useState('');
  const [result, setResult] = useState<Journal | null>(null);
  const [docs, setDocs] = useState<Doc[]>([]);
  const [selected, setSelected] = useState('');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [progress, setProgress] = useState(0);
  const [pdfUrl, setPdfUrl] = useState('');
  const [previewPage, setPreviewPage] = useState(1);
  const [elapsed, setElapsed] = useState<number | null>(null);
  const cancel = useRef<AbortController | null>(null);
  const uploadRequest = useRef<XMLHttpRequest | null>(null);
  const uploadInput = useRef<HTMLInputElement>(null);
  const document = docs.find(d => d.id === selected);
  const canAccess = !health?.authEnabled || !!key;

  async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(path, { ...options, headers: { ...(key ? { Authorization: `Bearer ${key}` } : {}), ...options.headers } });
    if (!response.ok) {
      const payload = await response.json().catch(() => null);
      throw new Error(payload?.error?.message || `Request failed (${response.status})`);
    }
    if (response.status === 204) return undefined as T;
    return response.json();
  }

  useEffect(() => {
    let alive = true;
    const check = () => fetch('/health/ready').then(r => r.json()).then(h => { if (alive) setHealth(h); }).catch(() => { if (alive) setHealth(null); });
    check();
    const timer = setInterval(check, 5000);
    return () => { alive = false; clearInterval(timer); };
  }, []);

  useEffect(() => {
    let alive = true;
    if (canAccess) api<{ documents: Doc[] }>('/documents').then(data => { if (alive) setDocs(data.documents); }).catch(e => { if (alive) setError(e.message); });
    return () => { alive = false; };
  }, [key, health?.authEnabled]);

  useEffect(() => {
    let alive = true;
    let objectUrl = '';
    setPdfUrl('');
    setPreviewPage(1);
    if (selected && document?.state === 'READY') {
      fetch(`/documents/${selected}/file`, { headers: key ? { Authorization: `Bearer ${key}` } : {} })
        .then(r => { if (!r.ok) throw new Error('PDF preview unavailable'); return r.blob(); })
        .then(blob => { objectUrl = URL.createObjectURL(blob); if (alive) setPdfUrl(objectUrl); else URL.revokeObjectURL(objectUrl); })
        .catch(e => { if (alive) setError(e.message); });
    }
    return () => { alive = false; if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [selected, key, document?.state]);

  useEffect(() => () => { cancel.current?.abort(); uploadRequest.current?.abort(); }, []);

  async function analyze(event: FormEvent) {
    event.preventDefault();
    setBusy('Analyzing journal'); setError(''); setResult(null); setElapsed(null);
    const controller = new AbortController(); cancel.current = controller;
    const started = performance.now();
    try {
      setResult(await api<Journal>('/analyze-journal', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text }), signal: controller.signal }));
      setElapsed((performance.now() - started) / 1000);
    } catch (e) { if (!controller.signal.aborted) setError((e as Error).message); }
    finally { setBusy(null); cancel.current = null; }
  }

  async function ask(event: FormEvent) {
    event.preventDefault();
    setBusy('Checking document evidence'); setError(''); setAnswer(null);
    const controller = new AbortController(); cancel.current = controller;
    try { setAnswer(await api<Answer>(`/documents/${selected}/questions`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question }), signal: controller.signal })); }
    catch (e) { if (!controller.signal.aborted) setError((e as Error).message); }
    finally { setBusy(null); cancel.current = null; }
  }

  async function upload(file?: File) {
    if (!file) return;
    setBusy('Uploading PDF'); setError(''); setProgress(0); setAnswer(null);
    const xhr = new XMLHttpRequest(); uploadRequest.current = xhr;
    try {
      const data = await new Promise<{ document: Doc }>((resolve, reject) => {
        xhr.open('POST', '/documents'); xhr.timeout = 65000;
        if (key) xhr.setRequestHeader('Authorization', `Bearer ${key}`);
        xhr.upload.onprogress = e => { if (e.lengthComputable) { setProgress(Math.round(e.loaded / e.total * 100)); if (e.loaded === e.total) setBusy('Indexing PDF'); } };
        xhr.onload = () => { try { const payload = JSON.parse(xhr.responseText); if (xhr.status >= 200 && xhr.status < 300) resolve(payload); else reject(new Error(payload?.error?.message || 'Upload failed')); } catch { reject(new Error('Invalid upload response')); } };
        xhr.onerror = () => reject(new Error('Unable to reach the service'));
        xhr.ontimeout = () => reject(new Error('Upload timed out; retry the file'));
        xhr.onabort = () => reject(new Error('Upload cancelled'));
        const form = new FormData(); form.append('file', file); xhr.send(form);
      });
      setDocs((await api<{ documents: Doc[] }>('/documents')).documents);
      setSelected(data.document.id); setQuestion('');
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(null); uploadRequest.current = null; if (uploadInput.current) uploadInput.current.value = ''; }
  }

  async function remove(doc: Doc) {
    if (!confirm(`Delete ${doc.filename} and its index?`)) return;
    setBusy('Deleting document'); setError('');
    try {
      await api(`/documents/${doc.id}`, { method: 'DELETE' });
      setDocs(docs.filter(d => d.id !== doc.id)); if (selected === doc.id) { setSelected(''); setAnswer(null); }
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(null); }
  }

  function logout() { if (busy) return; setKey(''); setKeyInput(''); setDocs([]); setSelected(''); setResult(null); setAnswer(null); setText(''); setQuestion(''); setError(''); }

  return <div className="app">
    <aside className="sidebar">
      <a className="brand" href="/" aria-label="MyManah home"><span className="brand-icon"><NotebookPen size={23} /></span><span>MyManah<small>Journal intelligence</small></span></a>
      <nav aria-label="Workspace"><span className="nav-label">WORKSPACE</span>
        <button className={view === 'journal' ? 'nav active' : 'nav'} onClick={() => { setView('journal'); setError(''); }}><NotebookPen size={18} />Journal<ChevronRight size={15} /></button>
        <button className={view === 'documents' ? 'nav active' : 'nav'} onClick={() => { setView('documents'); setError(''); }}><FileText size={18} />Documents<ChevronRight size={15} /></button>
      </nav>
      <div className="sidebar-bottom"><ShieldCheck size={18} /><span>Local inference<small>English release</small></span>{key && <button className="icon" title="Clear session key" disabled={!!busy} onClick={logout}><LogOut size={17} /></button>}</div>
    </aside>
    <div className="workspace">
      <header className="topbar"><span>{view === 'journal' ? 'Journal' : 'Documents'}</span><div className="runtime"><i className={health?.status === 'ready' ? 'dot ready' : 'dot'} />{health?.status === 'ready' ? 'Models ready' : health ? 'Models unavailable' : 'Service unavailable'}{key && <button className="icon" title="Clear session key" disabled={!!busy} onClick={logout}><LogOut size={17} /></button>}</div></header>
      <main>
        {health?.authEnabled && !key ? <section className="access"><KeyRound size={28} /><h1>Workspace access</h1><form onSubmit={e => { e.preventDefault(); setKey(keyInput); setError(''); }}><label htmlFor="key">API key</label><input id="key" type="password" value={keyInput} onChange={e => setKeyInput(e.target.value)} autoComplete="off" required /><button className="primary" type="submit">Connect<ArrowRight size={16} /></button></form></section> : <>
        <div className="page-heading"><div><span className="eyebrow">{view === 'journal' ? 'PERSONAL REFLECTION' : 'DOCUMENT WORKSPACE'}</span><h1>{view === 'journal' ? 'Journal analysis' : 'Your documents'}</h1></div>{view === 'documents' && <button className="primary" disabled={!!busy || health?.status !== 'ready'} onClick={() => uploadInput.current?.click()}><Plus size={17} />Upload PDF</button>}</div>
        {error && <div className="error" role="alert"><span>{error}</span><button className="icon" title="Dismiss error" onClick={() => setError('')}><X size={16} /></button></div>}
        {health && health.status !== 'ready' && <div className="notice" role="status">Local models are not ready{health.failure ? ` (${health.failure})` : ''}.</div>}
        {busy && <div className="activity" role="status"><LoaderCircle className="spin" size={17} /><span>{busy}{busy === 'Uploading PDF' ? ` · ${progress}%` : ''}</span><button className="icon" title="Cancel request" onClick={() => { cancel.current?.abort(); uploadRequest.current?.abort(); }}><X size={17} /></button></div>}
        {view === 'journal' ? <div className="journal-layout">
          <form className="journal-editor" onSubmit={analyze}><div className="section-label"><label htmlFor="journal">Journal entry</label><span>{new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric' }).format(new Date())}</span></div><textarea id="journal" value={text} disabled={!!busy} onChange={e => { setText(e.target.value); setResult(null); setElapsed(null); }} maxLength={8000} placeholder="What's on your mind today?" required /><div className="editor-footer"><span>{text.length.toLocaleString()} / 8,000</span><button className="primary" disabled={!!busy || !text.trim() || health?.status !== 'ready'}>Analyze<ArrowRight size={16} /></button></div></form>
          <section className="journal-results" aria-live="polite"><div className="section-label"><h2>Analysis</h2>{elapsed !== null && <span>{elapsed.toFixed(1)} s</span>}</div>{result ? <>
            <div className="mood-line"><div className="mood-number">{result.moodScore}<span>/ 10</span></div><div><span className="small-label">Mood score</span><div className="mood-track">{Array.from({ length: 10 }, (_, i) => <i key={i} className={i < result.moodScore ? 'filled' : ''} />)}</div></div></div>
            <dl className="result-list"><div><dt>Sentiment</dt><dd className={result.sentiment}>{result.sentiment}</dd></div><div><dt>Dominant emotion</dt><dd>{result.emotion}</dd></div><div><dt>Classification score</dt><dd>{(result.confidence * 100).toFixed(0)}%</dd></div><div><dt>Screening priority</dt><dd className={`risk ${result.crisisRisk.toLowerCase()}`}>{result.crisisRisk}</dd></div></dl>
            <div className="summary"><h3>Summary</h3><p>{result.summary}</p></div><p className="disclaimer">Screening priority is a text-based indicator, not a diagnosis or prediction of personal safety.</p>
          </> : <div className="empty"><NotebookPen size={34} strokeWidth={1.4} /><span>No analysis yet</span></div>}</section>
        </div> : <div className="documents-layout">
          <input className="hidden" ref={uploadInput} type="file" accept="application/pdf,.pdf" onChange={e => upload(e.target.files?.[0])} />
          <section className="document-list"><div className="section-label"><h2>Library</h2><span>{docs.length}</span></div>{docs.length ? docs.map(doc => <div className={`document-row ${selected === doc.id ? 'selected' : ''}`} key={doc.id}><button className="document-select" disabled={!!busy} onClick={() => { setSelected(doc.id); setAnswer(null); setQuestion(''); setError(''); }}><FileText size={20} /><span><strong>{doc.filename}</strong><small>{doc.state === 'READY' ? `${doc.pages} pages · ${doc.chunks} chunks` : doc.state}</small></span>{doc.state === 'READY' && <Check size={14} />}</button><button className="icon" title={`Delete ${doc.filename}`} disabled={!!busy} onClick={() => remove(doc)}><Trash2 size={15} /></button></div>) : <div className="empty library-empty"><FileText size={30} strokeWidth={1.4} /><span>No documents</span></div>}</section>
          <section className="document-question"><div className="section-label"><h2>{document?.filename || 'Document questions'}</h2>{document?.state === 'READY' && <span className="ready-label">READY</span>}</div>{document ? <><form onSubmit={ask}><label htmlFor="question">Question</label><textarea id="question" rows={3} maxLength={1500} placeholder="Ask a question about this document" value={question} disabled={!!busy} onChange={e => { setQuestion(e.target.value); setAnswer(null); }} required /><button className="primary" disabled={!!busy || !question.trim() || document.state !== 'READY' || health?.status !== 'ready'}>Ask document<ArrowRight size={16} /></button></form>{answer && <div className="answer" aria-live="polite"><div className="answer-status">{answer.status.replaceAll('_', ' ')}</div><p>{answer.answer}</p>{answer.citations.map((citation, i) => <details key={`${citation.chunk_id}-${i}`} onToggle={e => { if (e.currentTarget.open) setPreviewPage(citation.page); }}><summary>[{i + 1}] {citation.filename} · Page {citation.page}</summary><blockquote>{citation.quote}</blockquote></details>)}</div>}{pdfUrl && <div className="pdf-preview"><div className="section-label"><h3>Source document</h3><a className="icon" href={`${pdfUrl}#page=${previewPage}&view=FitH`} target="_blank" rel="noreferrer" title="Open source PDF" aria-label="Open source PDF"><ExternalLink size={16} /></a></div><Suspense fallback={<div role="status">Loading source document</div>}><PdfPreview url={pdfUrl} page={previewPage} onPageChange={setPreviewPage} /></Suspense></div>}</> : <div className="empty"><FileText size={34} strokeWidth={1.4} /><span>No document selected</span></div>}</section>
        </div>}
        </>}
      </main>
    </div>
  </div>;
}
