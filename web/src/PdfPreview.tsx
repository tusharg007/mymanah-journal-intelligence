import { useEffect, useRef, useState } from 'react';
import { ChevronLeft, ChevronRight, Maximize2, Minus, Plus } from 'lucide-react';
import { AnnotationMode, GlobalWorkerOptions, getDocument } from 'pdfjs-dist';
import type { PDFDocumentProxy, RenderTask } from 'pdfjs-dist';
import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url';

GlobalWorkerOptions.workerSrc = workerUrl;

export default function PdfPreview({ url, page, onPageChange }: {
  url: string; page: number; onPageChange: (page: number) => void;
}) {
  const [pdf, setPdf] = useState<PDFDocumentProxy | null>(null);
  const [width, setWidth] = useState(0);
  const [zoom, setZoom] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const viewport = useRef<HTMLDivElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    let alive = true;
    setPdf(null); setError(''); setLoading(true); setZoom(1);
    const task = getDocument({ url, cMapUrl: '/pdfjs/cmaps/', cMapPacked: true,
      standardFontDataUrl: '/pdfjs/standard_fonts/', wasmUrl: '/pdfjs/wasm/', iccUrl: '/pdfjs/iccs/',
      maxImageSize: 8_000_000, canvasMaxAreaInBytes: 32_000_000, enableXfa: false });
    task.promise.then(document => { if (alive) setPdf(document); })
      .catch(() => { if (alive) { setError('Source PDF could not be rendered.'); setLoading(false); } });
    return () => { alive = false; void task.destroy().catch(() => {}); };
  }, [url]);

  useEffect(() => {
    const element = viewport.current;
    if (!element) return;
    const observer = new ResizeObserver(entries => setWidth(entries[0].contentRect.width));
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!pdf || !width) return;
    if (page > pdf.numPages) { onPageChange(pdf.numPages); return; }
    let alive = true;
    let render: RenderTask | undefined;
    setLoading(true); setError('');
    pdf.getPage(page).then(async source => {
      if (!alive || !canvas.current) return;
      const natural = source.getViewport({ scale: 1 });
      if (![natural.width, natural.height].every(value => Number.isFinite(value) && value > 0)) {
        throw new Error('Invalid source page dimensions');
      }
      const scale = Math.min((width - 24) / natural.width * zoom,
        2000 / natural.width, 5000 / natural.height);
      const view = source.getViewport({ scale });
      const ratio = Math.min(window.devicePixelRatio || 1, 2,
        Math.sqrt(8_000_000 / (view.width * view.height)));
      const target = canvas.current;
      target.width = Math.ceil(view.width * ratio); target.height = Math.ceil(view.height * ratio);
      target.style.width = `${view.width}px`; target.style.height = `${view.height}px`;
      render = source.render({ canvas: target, viewport: view,
        transform: [ratio, 0, 0, ratio, 0, 0], annotationMode: AnnotationMode.DISABLE });
      await render.promise;
      if (alive) setLoading(false);
    }).catch(e => {
      if (alive && e.name !== 'RenderingCancelledException') { setError('Source page could not be rendered.'); setLoading(false); }
    });
    return () => { alive = false; render?.cancel(); };
  }, [pdf, page, width, zoom, onPageChange]);

  return <div className="pdf-viewer">
    <div className="pdf-toolbar">
      <button className="icon" title="Previous page" disabled={!pdf || page <= 1} onClick={() => onPageChange(page - 1)}><ChevronLeft size={17} /></button>
      <input aria-label="Source page" type="number" min={1} max={pdf?.numPages || 1} value={page} disabled={!pdf}
        onChange={e => { const value = Number(e.target.value); if (Number.isInteger(value) && value >= 1 && value <= (pdf?.numPages || 1)) onPageChange(value); }} />
      <span>/ {pdf?.numPages || '-'}</span>
      <button className="icon" title="Next page" disabled={!pdf || page >= pdf.numPages} onClick={() => onPageChange(page + 1)}><ChevronRight size={17} /></button>
      <div className="pdf-zoom">
        <button className="icon" title="Zoom out" disabled={zoom <= .5} onClick={() => setZoom(Math.max(.5, zoom / 1.25))}><Minus size={16} /></button>
        <button className="icon" title="Fit page width" onClick={() => setZoom(1)}><Maximize2 size={16} /></button>
        <button className="icon" title="Zoom in" disabled={zoom >= 2.5} onClick={() => setZoom(Math.min(2.5, zoom * 1.25))}><Plus size={16} /></button>
      </div>
    </div>
    <div className="pdf-viewport" ref={viewport}>
      {(loading || error) && <div className="pdf-state" role="status">{error || 'Loading source page'}</div>}
      <div className="pdf-canvas"><canvas ref={canvas} aria-label={`Source document page ${page}`} role="img" data-rendered={!loading && !error} /></div>
    </div>
  </div>;
}
