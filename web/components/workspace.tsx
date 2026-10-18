'use client';

import { useEffect, useRef, useState } from 'react';
import { ArrowDown, ArrowLeft, ArrowRight, ArrowSquareOut, BookOpen, Check, CheckCircle, Clock, DownloadSimple, FileText, FilmStrip, FloppyDisk, FolderSimple, GearSix, Globe, InstagramLogo, Link as LinkIcon, List, MagnifyingGlass, Microphone, Plus, Scan, ShieldCheck, SlidersHorizontal, Sparkle, SquaresFour, Trash, UploadSimple, VideoCamera, WarningCircle, Waveform, X } from '@phosphor-icons/react';
import { analyze, extractKeywords, formatTime, reportMarkdown } from '@/lib/analysis';
import { inspectVideo, decodeAudio, validateVideoFile } from '@/lib/media';
import { parseInstagramUrl } from '@/lib/instagram';
import { loadReports, saveReports } from '@/lib/storage';
import type { MediaInfo, Report, Source } from '@/lib/types';

type View = 'desk' | 'saved' | 'compare' | 'guide';
type Tab = 'overview' | 'creator' | 'claims' | 'transcript' | 'frames';

function IconBadge({ children, tone = '' }: { children: React.ReactNode; tone?: string }) { return <span className={`icon-badge ${tone}`}>{children}</span>; }
function Empty({ icon, title, text }: { icon: React.ReactNode; title: string; text: string }) { return <div className="empty"><span>{icon}</span><h3>{title}</h3><p>{text}</p></div>; }
function downloadText(text: string, filename: string, type: string) {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = filename; anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export default function Workspace() {
  const [view, setView] = useState<View>('desk');
  const [mobileNav, setMobileNav] = useState(false);
  const [sourceMode, setSourceMode] = useState<'upload' | 'link' | 'text'>('upload');
  const [link, setLink] = useState('');
  const [attachedLink, setAttachedLink] = useState('');
  const [name, setName] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [media, setMedia] = useState<MediaInfo | null>(null);
  const [videoUrl, setVideoUrl] = useState('');
  const [transcript, setTranscript] = useState('');
  const [transcriptSource, setTranscriptSource] = useState<Report['transcriptSource']>('manual');
  const [language, setLanguage] = useState('auto');
  const [goal, setGoal] = useState('Improve my next Reel');
  const [rights, setRights] = useState(false);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [dragging, setDragging] = useState(false);
  const [report, setReport] = useState<Report | null>(null);
  const [tab, setTab] = useState<Tab>('overview');
  const [saved, setSaved] = useState<Report[]>([]);
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [showModelConsent, setShowModelConsent] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const workerRef = useRef<Worker | null>(null);
  const fileVersion = useRef(0);
  const speechVersion = useRef(0);

  useEffect(() => { setSaved(loadReports()); return () => workerRef.current?.terminate(); }, []);
  useEffect(() => {
    if (!file) { setVideoUrl(''); return; }
    const url = URL.createObjectURL(file); setVideoUrl(url); return () => URL.revokeObjectURL(url);
  }, [file]);
  useEffect(() => {
    if (!notice) return;
    const id = setTimeout(() => setNotice(''), 5500); return () => clearTimeout(id);
  }, [notice]);

  async function addFile(next: File | undefined) {
    if (!next || busy) return;
    const version = ++fileVersion.current;
    setError(''); setNotice(''); setReport(null); setMedia(null); setFile(null); setTranscript('');
    try {
      validateVideoFile(next); setBusy('Reading your original video and sampling six frames…');
      const result = await inspectVideo(next);
      if (version !== fileVersion.current) return;
      setFile(next); setMedia(result); setName(next.name.replace(/\.[^.]+$/, ''));
    } catch (e) { setError(e instanceof Error ? e.message : 'Could not inspect the video.'); }
    finally { if (version === fileVersion.current) setBusy(''); }
  }
  function attachLink() {
    try { const source = parseInstagramUrl(link); setAttachedLink(source.url); setError(''); setNotice('Instagram source attached. Add the original video or a transcript to inspect its content.'); }
    catch (e) { setAttachedLink(''); setError(e instanceof Error ? e.message : 'Invalid Instagram URL.'); }
  }
  function newStudy() {
    fileVersion.current++; speechVersion.current++; workerRef.current?.terminate(); workerRef.current = null;
    setBusy(''); setFile(null); setMedia(null); setTranscript(''); setLink(''); setAttachedLink(''); setReport(null);
    setName(''); setRights(false); setError(''); setNotice(''); setView('desk'); setMobileNav(false); setTab('overview');
  }
  function generate() {
    setError('');
    if (!rights) { setError('Confirm that you can use this video or transcript before analyzing it.'); return; }
    try {
      const canonical = link.trim() ? parseInstagramUrl(link).url : attachedLink;
      setAttachedLink(canonical);
      const result = analyze({ name, instagramUrl: canonical, goal, transcript, transcriptSource, language, media });
      setReport(result); setTab('overview'); setNotice('Your study is ready. Observations are based on the file and text you supplied.');
    } catch (e) { setError(e instanceof Error ? e.message : 'Could not analyze this input.'); }
  }
  async function transcribe() {
    if (!file || busy) return;
    const version = ++speechVersion.current;
    setShowModelConsent(false); setError(''); setBusy('Decoding audio locally…');
    try {
      const audio = await decodeAudio(file);
      if (version !== speechVersion.current) return;
      if (!workerRef.current) workerRef.current = new Worker(new URL('../workers/transcribe.ts', import.meta.url), { type: 'module' });
      const worker = workerRef.current;
      worker.onmessage = event => {
        if (version !== speechVersion.current) return;
        if (event.data.type === 'progress') {
          const detail = event.data.progress !== undefined ? ` (${Math.round(event.data.progress)}% of current file)` : '';
          setBusy(event.data.status === 'transcribing' ? 'Transcribing on your device. This can take several minutes…' : `Preparing local speech model${detail}…`);
        }
        if (event.data.type === 'complete') {
          setTranscript(event.data.text); setTranscriptSource('local-whisper'); setBusy('');
          setNotice('Local transcript ready. Review and correct it before analysis.');
        }
        if (event.data.type === 'error') { setError('Local transcription failed: ' + event.data.message); setBusy(''); }
      };
      worker.onerror = () => { setError('Local speech worker could not start. Try a recent browser or paste a transcript.'); setBusy(''); worker.terminate(); workerRef.current = null; };
      worker.postMessage({ audio, language }, [audio.buffer]);
    } catch (e) { setError(e instanceof Error ? e.message : 'Could not transcribe audio.'); setBusy(''); }
  }
  function cancelTranscription() { speechVersion.current++; workerRef.current?.terminate(); workerRef.current = null; setBusy(''); setNotice('Local transcription stopped. You can paste or edit a transcript.'); }
  function saveCurrent() {
    if (!report) return;
    const next = [report, ...saved.filter(r => r.id !== report.id)].slice(0, 20);
    try { saveReports(next); setSaved(loadReports()); setNotice('Saved in this browser only. Original video and frame images are not persisted.'); }
    catch (e) { setError((e as Error).message); }
  }
  function removeSaved(id: string) {
    const next = saved.filter(r => r.id !== id);
    try { saveReports(next); setSaved(next); setCompareIds(ids => ids.filter(i => i !== id)); }
    catch (e) { setError((e as Error).message); }
  }
  function openSaved(item: Report) {
    setReport(item); setFile(null); setMedia(null); setTranscript(item.transcript); setName(item.name); setView('desk'); setTab('overview'); setError('');
  }
  function nav(next: View) { setView(next); setMobileNav(false); setError(''); }
  const activeName = { desk: 'Research desk', saved: 'Saved studies', compare: 'Compare studies', guide: 'How it works' }[view];

  return <div className="app-shell">
    <a className="skip-link" href="#main">Skip to workspace</a>
    {mobileNav && <button className="nav-scrim" aria-label="Close navigation" onClick={() => setMobileNav(false)} />}
    <aside className={`sidebar ${mobileNav ? 'is-open' : ''}`}>
      <button className="brand" onClick={() => nav('desk')} aria-label="ReelScope research desk"><span className="brand-mark"><Scan size={23} weight="bold" /></span><span>reelscope<span className="brand-dot">.</span></span></button>
      <div className="workspace-label"><span className="workspace-avatar">P</span><div><strong>Personal workspace</strong><small>Instagram research</small></div><SlidersHorizontal size={16}/></div>
      <button className="new-study" onClick={newStudy}><Plus size={18} weight="bold"/> New study <span>↗</span></button>
      <p className="nav-caption">WORKSPACE</p>
      <nav aria-label="Main navigation">
        <button className={view === 'desk' ? 'active' : ''} onClick={() => nav('desk')}><SquaresFour size={19}/>Research desk</button>
        <button className={view === 'saved' ? 'active' : ''} onClick={() => nav('saved')}><FolderSimple size={19}/>Saved studies<span className="count">{saved.length}</span></button>
        <button className={view === 'compare' ? 'active' : ''} onClick={() => nav('compare')}><FilmStrip size={19}/>Compare</button>
      </nav>
      <p className="nav-caption">RESOURCES</p>
      <nav aria-label="Resources"><button className={view === 'guide' ? 'active' : ''} onClick={() => nav('guide')}><BookOpen size={19}/>How it works</button></nav>
      <div className="sidebar-bottom"><div className="local-card"><ShieldCheck size={21}/><strong>Your video stays yours.</strong><p>Media inspection and transcription run on your device.</p><button onClick={() => nav('guide')}>About local processing <ArrowRight size={13}/></button></div><div className="profile-row"><span className="profile-avatar">Y</span><div><strong>Your workspace</strong><small>Local browser storage</small></div></div></div>
    </aside>
    <div className="workspace-shell">
      <header className="topbar"><div className="breadcrumb"><button className="mobile-menu icon-button" aria-label="Open navigation" onClick={() => setMobileNav(true)}><List size={21}/></button><span>Workspace</span><span className="slash">/</span><strong>{activeName}</strong></div><div className="topbar-right"><span className="local-indicator"><span/>Local-first</span><button className="icon-button" onClick={() => nav('guide')} aria-label="Open product guide"><GearSix size={19}/></button><span className="mini-avatar">Y</span></div></header>
      <main id="main" className="main-content">
        {notice && <div className="notice" role="status"><CheckCircle size={18}/><span>{notice}</span><button aria-label="Dismiss notification" onClick={() => setNotice('')}><X size={15}/></button></div>}
        {error && <div className="error-message" role="alert"><WarningCircle size={20}/><span>{error}</span><button aria-label="Dismiss error" onClick={() => setError('')}><X size={16}/></button></div>}
        {view === 'desk' && !report && <>
          <div className="page-intro"><div className="eyebrow"><InstagramLogo size={15}/> INSTAGRAM RESEARCH STUDIO</div><h1>Give your next Reel<br/>a closer look<span>.</span></h1><p>Understand the content. Question the claims.<br className="desktop-break"/> Find a clearer direction for what comes next.</p></div>
          <div className="intake-grid">
            <section className="intake-panel panel"><div className="panel-heading"><div><h2>Start a new study</h2><p>Bring the original. We’ll help you inspect it.</p></div><span className="step-label">01 / SOURCE</span></div>
              <div className="source-tabs" role="tablist" aria-label="Input source">
                <button role="tab" aria-selected={sourceMode === 'upload'} onClick={() => setSourceMode('upload')}><UploadSimple size={16}/>Upload video</button>
                <button role="tab" aria-selected={sourceMode === 'link'} onClick={() => setSourceMode('link')}><LinkIcon size={16}/>Instagram link</button>
                <button role="tab" aria-selected={sourceMode === 'text'} onClick={() => setSourceMode('text')}><FileText size={16}/>Transcript</button>
              </div>
              <input ref={inputRef} type="file" accept="video/mp4,video/webm,video/quicktime" className="visually-hidden" aria-label="Choose original video" onChange={event => { void addFile(event.target.files?.[0]); event.target.value = ''; }}/>
              {sourceMode === 'link' && <div className="link-pane"><label htmlFor="instagram-link">Instagram Reel or post URL</label><div className="input-action"><InstagramLogo size={20}/><input id="instagram-link" placeholder="https://www.instagram.com/reel/…" value={link} onChange={e => setLink(e.target.value)}/><button onClick={attachLink} disabled={!!busy}>Attach <ArrowRight size={15}/></button></div><div className="inline-note"><LinkIcon size={17}/><p>A link identifies the source. This free version cannot fetch Instagram’s media automatically. Add your original video below, or provide its transcript.</p></div></div>}
              {sourceMode !== 'text' && (file && media ? <div className="loaded-file"><IconBadge><VideoCamera size={23}/></IconBadge><div><strong>{file.name}</strong><span>{formatTime(media.duration)} · {media.width} × {media.height} · {(media.size / 1048576).toFixed(1)} MB</span></div><button className="icon-button" aria-label="Remove video" disabled={!!busy} onClick={() => { setFile(null); setMedia(null); setTranscript(''); }}><X size={18}/></button></div> : <div className={`dropzone ${dragging ? 'dragging' : ''}`} onDragOver={event => { event.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={event => { event.preventDefault(); setDragging(false); void addFile(event.dataTransfer.files[0]); }}><div className="upload-illustration"><span/><UploadSimple size={27} weight="regular"/></div><h3>Drop your Reel right here</h3><p>or <button className="text-button" onClick={() => inputRef.current?.click()} disabled={!!busy}>choose a video</button> from your device</p><small>MP4, MOV, WebM · Up to 150 MB · 5 minutes</small></div>)}
              {attachedLink && <div className="attached-source"><CheckCircle size={16}/><span>Instagram source attached</span><a href={attachedLink} target="_blank" rel="noreferrer" aria-label="Open attached Instagram source"><ArrowSquareOut size={16}/></a></div>}
              <div className="transcript-section"><div className="field-title"><label htmlFor="transcript">Spoken transcript <span>{sourceMode === 'text' ? '' : 'optional'}</span></label>{file && <button className="small-button" onClick={() => setShowModelConsent(true)} disabled={!!busy}><Waveform size={15}/> Transcribe locally</button>}</div><textarea id="transcript" dir="auto" rows={sourceMode === 'text' ? 7 : 4} maxLength={60000} value={transcript} onChange={e => { setTranscript(e.target.value); setTranscriptSource('manual'); }} placeholder="Paste what is actually said in the video, or transcribe a local clip. English and Urdu text are preserved."/><div className="field-footer"><span>Review speech recognition before using it as evidence.</span><span>{transcript.length.toLocaleString()} / 60,000</span></div></div>
              <div className="form-row"><div><label htmlFor="study-name">Study name <span>optional</span></label><input id="study-name" value={name} maxLength={120} onChange={e => setName(e.target.value)} placeholder="e.g. Product launch Reel"/></div><div><label htmlFor="study-goal">What are you working on?</label><select id="study-goal" value={goal} onChange={e => setGoal(e.target.value)}><option>Improve my next Reel</option><option>Research claims and credibility</option><option>Explore both content and claims</option></select></div></div>
              <label className="check-label"><input type="checkbox" checked={rights} onChange={e => setRights(e.target.checked)}/><span>I own this content or have permission to analyze it.</span></label>
              {busy && <div className="processing" role="status"><span className="spinner"/><span>{busy}</span>{busy.toLowerCase().includes('model') || busy.toLowerCase().includes('transcri') ? <button onClick={cancelTranscription}>Stop</button> : null}</div>}
              <button className="primary-button analyze-button" onClick={generate} disabled={!!busy || (!media && !transcript.trim())}><Scan size={19}/> Create research report <ArrowRight size={18}/></button><div className="under-button"><ShieldCheck size={14}/><span>No account. No paid AI key. No video upload to a server.</span></div>
            </section>
            <aside className="intake-aside"><div className="preview-panel panel"><div className="aside-heading"><span>YOUR SOURCE</span><span className="small-status">{file ? 'Original file' : 'Nothing added yet'}</span></div>{videoUrl ? <video className="source-video" src={videoUrl} controls playsInline preload="metadata" aria-label="Original video preview"/> : <div className="source-placeholder"><div className="viewfinder"><span/><span/><span/><span/><VideoCamera size={38} weight="thin"/></div><p>A fresh perspective<br/>starts with the original.</p><small>Your video preview appears here.</small></div>}<div className="preview-bottom"><span className="circle-check"><Check size={12}/></span><span>Private by design. Inspected locally.</span></div></div>
              <div className="outcomes"><h3>A study, with substance.</h3><div><IconBadge><Waveform size={18}/></IconBadge><p><strong>Content & delivery</strong><span>Transcript, repeated themes, and editing experiments.</span></p></div><div><IconBadge><MagnifyingGlass size={18}/></IconBadge><p><strong>Claims & reference sources</strong><span>A verification queue, with evidence you can inspect.</span></p></div><div><IconBadge><FilmStrip size={18}/></IconBadge><p><strong>The details in the frame</strong><span>Actual dimensions, duration, and sampled moments.</span></p></div></div><div className="honesty-note"><span>One useful distinction</span><p>A source match isn’t a fact-check. A content suggestion isn’t a promise of engagement.</p></div>
            </aside>
          </div><div className="workspace-footer"><span>Built for a closer look, not a crystal ball.</span><button onClick={() => nav('guide')}>Understand the methods <ArrowSquareOut size={13}/></button></div>
        </>}

        {view === 'desk' && report && <>
          <div className="report-top"><div><button className="back-link" onClick={() => setReport(null)}><ArrowLeft size={14}/> Back to source</button><div className="eyebrow">YOUR RESEARCH STUDY</div><h1 className="report-title">{report.name}</h1><p>{new Date(report.createdAt).toLocaleDateString('en-GB')} · {report.media ? 'Original video inspected' : 'Transcript-only analysis'} · {report.transcriptSource === 'local-whisper' ? 'Local Whisper transcript' : report.transcriptSource === 'manual' ? 'User-provided transcript' : 'No transcript'}</p></div><div className="report-actions"><button className="secondary-button" onClick={saveCurrent}><FloppyDisk size={16}/>Save study</button><button className="secondary-button" onClick={() => downloadText(reportMarkdown(report), 'reelscope-report.md', 'text/markdown;charset=utf-8')}><DownloadSimple size={16}/>Export</button></div></div>
          <div className="report-tabs" role="tablist" aria-label="Report sections">{([['overview', 'Overview'], ['creator', 'Creator notes'], ['claims', 'Claims & sources'], ['transcript', 'Transcript'], ['frames', 'Frame review']] as [Tab, string][]).map(([key, label]) => <button key={key} role="tab" aria-selected={tab === key} onClick={() => setTab(key)}>{label}{key === 'claims' && <span>{report.claims.length}</span>}</button>)}</div>
          {tab === 'overview' && <><div className="report-metrics"><Metric label="Clip duration" value={report.media ? formatTime(report.media.duration) : '—'} note={report.media ? 'From the original file' : 'No video supplied'}/><Metric label="Transcript words" value={report.wordCount.toLocaleString()} note={`${report.sentenceCount} text segments`}/><Metric label="Review candidates" value={String(report.claims.length)} note="Claims still need verification"/><Metric label="Performance data" value="Unknown" note="No Instagram analytics connected"/></div><div className="report-grid"><section className="panel report-panel"><div className="section-heading"><h2>The content in focus</h2><IconBadge><Scan size={20}/></IconBadge></div>{report.opening ? <><p className="label">OPENING TRANSCRIPT EXCERPT</p><blockquote dir="auto">“{report.opening}”</blockquote><p className="muted">This is the first text sentence, not a measured first-three-second hook.</p></> : <Empty icon={<FileText size={28}/>} title="No spoken text yet" text="Add or transcribe the spoken content for topic and claim analysis."/>}<div className="keyword-row">{report.keywords.map(k => <span key={k.term}>{k.term}<small>×{k.count}</small></span>)}</div><p className="muted">Repeated terms in the supplied transcript. They do not establish trending topics.</p><button className="text-button with-icon" onClick={() => setTab('creator')}>Explore editing experiments <ArrowRight size={16}/></button></section><section className="panel report-panel next-step"><IconBadge><MagnifyingGlass size={22}/></IconBadge><h2>Question what’s being claimed.</h2><p>{report.claims.length ? `${report.claims.length} statement${report.claims.length === 1 ? '' : 's'} matched the claim-review rules. Inspect the exact wording and find source context before reaching a conclusion.` : 'No statement matched the simple claim rules. You can add a claim manually; this does not establish that the content is accurate.'}</p><button className="secondary-button" onClick={() => setTab('claims')}>Open research queue <ArrowRight size={16}/></button></section></div><Limits report={report}/></>}
          {tab === 'creator' && <section className="observations">{report.observations.map((o, i) => <article className="panel observation" key={i}><div className="observation-index">{String(i + 1).padStart(2, '0')}</div><div><span className="category-label">{o.category}</span><h2>{o.title}</h2><p className="evidence"><strong>Observed</strong> {o.evidence}</p><p><strong>What to test</strong> {o.suggestion}</p></div></article>)}<div className="method-note"><ShieldCheck size={20}/><p>These are local, rule-based editing prompts. No model has watched and interpreted the full video, and no engagement lift is predicted.</p></div></section>}
          {tab === 'claims' && <ResearchPanel report={report} onChange={setReport}/>}
          {tab === 'transcript' && <section className="panel report-panel"><div className="section-heading"><div><h2>The words behind the report</h2><p>Source: {report.transcriptSource}. Verify this against the audio.</p></div><button className="secondary-button" onClick={() => { setTranscript(report.transcript); setReport(null); setSourceMode('text'); }}>Edit & re-analyze</button></div><div className="transcript-body" dir="auto">{report.transcript || 'No transcript supplied. Add reviewed spoken text to analyze its content.'}</div></section>}
          {tab === 'frames' && <section className="panel report-panel"><div className="section-heading"><div><h2>Inspect the original moments</h2><p>Six samples, not a scene-by-scene interpretation. Brightness is average luminance on a 0–255 scale.</p></div></div>{report.media?.frames.length ? <><div className="frame-grid">{report.media.frames.map((frame, i) => <button key={i} className="frame-card" onClick={() => { if (videoRef.current) { videoRef.current.currentTime = frame.time; void videoRef.current.play().catch(() => {}); } }}><img src={frame.image} alt={`Actual sampled video frame at ${formatTime(frame.time)}`}/><span>{formatTime(frame.time)}<small>Light {frame.brightness}/255</small></span></button>)}</div>{videoUrl && <video ref={videoRef} className="review-video" src={videoUrl} controls playsInline aria-label="Review sampled moments in the original video"/>}<p className="muted">Frame thumbnails are excluded from saved browser studies. Keep this session open to inspect them.</p></> : <Empty icon={<FilmStrip size={32}/>} title="No frame samples in this study" text="Add the original video to inspect frames. Saved reports retain metadata; they do not store media."/>}</section>}
        </>}

        {view === 'saved' && <><div className="section-intro"><span className="eyebrow">YOUR LIBRARY</span><h1>Work worth returning to.</h1><p>Only studies you explicitly save live here, in this browser. Original videos and frame images are never stored.</p></div>{saved.length ? <div className="saved-list">{saved.map(item => <article key={item.id} className="panel saved-card"><IconBadge><FileText size={23}/></IconBadge><div><h2>{item.name}</h2><p>{new Date(item.createdAt).toLocaleDateString('en-GB')} · {item.wordCount} transcript words · {item.claims.length} review candidates</p></div><button className="secondary-button" onClick={() => openSaved(item)}>Open <ArrowRight size={15}/></button><button className="icon-button" aria-label={`Remove saved study ${item.name}`} onClick={() => removeSaved(item.id)}><Trash size={18}/></button></article>)}</div> : <div className="panel"><Empty icon={<FolderSimple size={35}/>} title="A clean desk, for now." text="Create a real study, then save it when it is useful. There are no sample reports or invented metrics here."/><div className="empty-action"><button className="primary-button" onClick={newStudy}>Start a study <Plus size={16}/></button></div></div>}</>}
        {view === 'compare' && <><div className="section-intro"><span className="eyebrow">SIDE BY SIDE</span><h1>Spot the differences.</h1><p>Compare the actual file and transcript measurements of two saved studies. This does not compare Instagram performance.</p></div>{saved.length < 2 ? <div className="panel"><Empty icon={<FilmStrip size={35}/>} title="Two studies make a comparison." text="Save at least two reports to compare duration, aspect ratio, transcript density, and source coverage."/></div> : <><div className="compare-selects">{[0, 1].map(i => <div key={i}><label htmlFor={`compare-${i}`}>{i === 0 ? 'First study' : 'Second study'}</label><select id={`compare-${i}`} value={compareIds[i] || ''} onChange={e => setCompareIds(old => { const next = [...old]; next[i] = e.target.value; return next; })}><option value="">Choose a saved study</option>{saved.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}</select></div>)}</div>{compareIds[0] && compareIds[1] && compareIds[0] !== compareIds[1] ? <Comparison reports={compareIds.map(id => saved.find(r => r.id === id)!).filter(Boolean)}/> : <p className="muted">Choose two different studies to inspect their measurements.</p>}</>}</>}
        {view === 'guide' && <Guide/>}
      </main>
    </div>
    {showModelConsent && <div className="modal-overlay" onClick={() => setShowModelConsent(false)}><section className="modal panel" role="dialog" aria-modal="true" aria-labelledby="model-title" onClick={e => e.stopPropagation()}><button className="modal-close icon-button" aria-label="Close model dialog" onClick={() => setShowModelConsent(false)}><X size={20}/></button><IconBadge><Waveform size={26}/></IconBadge><h2 id="model-title">Speech recognition, on your device.</h2><p>The first run downloads the open Whisper tiny model and its runtime from Hugging Face/CDN services. The download can be substantial and processing can take several minutes. Your media is processed locally.</p><label htmlFor="speech-language">Spoken language</label><select id="speech-language" value={language} onChange={e => setLanguage(e.target.value)}><option value="auto">Auto-detect (review carefully)</option><option value="english">English</option><option value="urdu">Urdu (accuracy not validated)</option></select><div className="inline-note"><WarningCircle size={20}/><p>Tiny models can hallucinate words in music or silence. Urdu and mixed-language transcripts need careful correction.</p></div><button className="primary-button" onClick={() => void transcribe()}><ArrowDown size={17}/> Download & transcribe locally</button></section></div>}
  </div>;
}

function Metric({ label, value, note }: { label: string; value: string; note: string }) { return <div className="metric"><span>{label}</span><strong>{value}</strong><small>{note}</small></div>; }
function Limits({ report }: { report: Report }) { return <details className="limitations panel"><summary><ShieldCheck size={18}/> How to read this report <Plus size={17}/></summary><ul>{report.limitations.map((l, i) => <li key={i}>{l}</li>)}</ul></details>; }
function Comparison({ reports }: { reports: Report[] }) {
  if (reports.length !== 2) return null;
  const rows = [ ['Duration', ...reports.map(r => r.media ? `${r.media.duration.toFixed(1)} sec` : 'Not available')], ['Dimensions', ...reports.map(r => r.media ? `${r.media.width} × ${r.media.height}` : 'Not available')], ['Transcript words', ...reports.map(r => r.wordCount)], ['Whole-clip words/min', ...reports.map(r => r.wordsPerMinute ?? 'Not available')], ['Review candidates', ...reports.map(r => r.claims.length)], ['Reference sources retrieved', ...reports.map(r => r.claims.reduce((sum, c) => sum + c.sources.length, 0))], ['Instagram performance', 'Unknown', 'Unknown'] ];
  return <div className="panel table-scroll"><table className="comparison-table"><thead><tr><th>Measurement</th>{reports.map(r => <th key={r.id}>{r.name}</th>)}</tr></thead><tbody>{rows.map(row => <tr key={String(row[0])}>{row.map((cell, i) => <td key={i}>{cell}</td>)}</tr>)}</tbody></table></div>;
}

function ResearchPanel({ report, onChange }: { report: Report; onChange: (r: Report) => void }) {
  const [selected, setSelected] = useState(report.claims[0]?.id || '');
  const [custom, setCustom] = useState('');
  const [query, setQuery] = useState(report.claims[0]?.text.slice(0, 180) || '');
  const [language, setLanguage] = useState('en');
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState('');
  const [searched, setSearched] = useState(false);
  const requestRef = useRef<AbortController | null>(null);
  useEffect(() => () => requestRef.current?.abort(), []);
  const claim = report.claims.find(c => c.id === selected);
  async function research() {
    if (!claim || searching) return;
    const controller = new AbortController(); requestRef.current = controller;
    setSearching(true); setError(''); setSearched(false);
    try {
      const response = await fetch('/api/research', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query, language }), signal: controller.signal });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Reference search failed.');
      onChange({ ...report, claims: report.claims.map(c => c.id === claim.id ? { ...c, sources: data.sources as Source[], researchQuery: query } : c) }); setSearched(true);
    } catch (e) { if (!controller.signal.aborted) setError((e as Error).message); }
    finally { if (!controller.signal.aborted) setSearching(false); }
  }
  function addClaim() {
    if (custom.trim().length < 10 || custom.length > 600) { setError('Add a statement of 10–600 characters.'); return; }
    const id = crypto.randomUUID();
    onChange({ ...report, claims: [...report.claims, { id, text: custom.trim(), reason: 'Added manually by the researcher; verify the original wording and context.', status: 'Needs verification', sources: [] }] });
    setSelected(id); setQuery(custom.trim().slice(0, 180)); setCustom(''); setError(''); setSearched(false);
  }
  return <div className="research-layout"><aside className="panel claims-queue"><div className="section-heading"><h2>Verification queue</h2><span className="count">{report.claims.length}</span></div><p className="muted">Text-rule candidates, not factual verdicts.</p>{report.claims.map((c, i) => <button className={`claim-choice ${c.id === selected ? 'selected' : ''}`} key={c.id} onClick={() => { setSelected(c.id); setQuery(c.text.slice(0, 180)); setSearched(false); setError(''); }}><span>STATEMENT {String(i + 1).padStart(2, '0')}</span><p dir="auto">{c.text}</p><small><span/>Needs verification</small></button>)}<div className="add-claim"><label htmlFor="custom-claim">Add a statement to review</label><textarea id="custom-claim" rows={3} maxLength={600} value={custom} onChange={e => setCustom(e.target.value)} placeholder="Paste a specific claim…"/><button className="small-button" onClick={addClaim} disabled={searching}><Plus size={15}/> Add to queue</button></div></aside><section className="panel research-content">{claim ? <><span className="category-label">UNVERIFIED STATEMENT</span><h2 className="claim-title" dir="auto">{claim.text}</h2><p className="muted">{claim.reason}</p><div className="reference-search"><label htmlFor="reference-query">Search reference context</label><div className="input-action"><MagnifyingGlass size={18}/><input id="reference-query" dir="auto" value={query} maxLength={180} onChange={e => setQuery(e.target.value)} placeholder="Refine into a short topic or exact claim"/></div><div className="search-options"><select aria-label="Reference language" value={language} onChange={e => setLanguage(e.target.value)}><option value="en">English Wikipedia</option><option value="ur">Urdu Wikipedia</option></select><button className="primary-button" onClick={() => void research()} disabled={query.trim().length < 3 || searching}>{searching ? <span className="spinner"/> : <MagnifyingGlass size={16}/>}Find references</button></div><p className="privacy-caption"><Globe size={13}/>Only this search query leaves your device. Your video is not sent.</p></div>{error && <div className="error-message" role="alert">{error}</div>}<div className="source-results"><div className="section-heading"><h3>Retrieved references</h3><span>{claim.sources.length} sources</span></div>{claim.sources.length ? claim.sources.map((s, i) => <article className="source-result" key={s.url}><span className="source-number">{String(i + 1).padStart(2, '0')}</span><div><a href={s.url} target="_blank" rel="noreferrer">{s.title}<ArrowSquareOut size={15}/></a><small>{s.publisher}</small><p>{s.excerpt || 'Open the article to inspect the context and its cited sources.'}</p></div></article>) : <Empty icon={<MagnifyingGlass size={27}/>} title={searched ? 'No matching context found' : 'Start with evidence, not a verdict.'} text={searched ? 'Try a shorter topic query. No results do not mean the claim is false.' : 'Search to retrieve related reference pages. A match does not establish support or contradiction.'}/>}</div><div className="external-research"><h3>Go beyond reference context</h3><p>Read primary sources and look for existing professional fact-checks. These links open searches; results are not automatically analyzed.</p><a href={`https://www.google.com/search?q=${encodeURIComponent(claim.text)}`} target="_blank" rel="noreferrer">Search the exact statement <ArrowSquareOut size={14}/></a><a href={`https://toolbox.google.com/factcheck/explorer/search/${encodeURIComponent(claim.text)}`} target="_blank" rel="noreferrer">Look in Fact Check Explorer <ArrowSquareOut size={14}/></a></div><div className="inline-note"><ShieldCheck size={20}/><p>Current status: <strong>Needs verification.</strong> This app does not turn related Wikipedia pages into true/false judgments, identify deepfakes, or establish original provenance.</p></div></> : <Empty icon={<MagnifyingGlass size={32}/>} title="Choose a statement to investigate" text="Add a specific claim from the video to the queue. A clip without detected claims is not automatically accurate."/>}</section></div>;
}

function Guide() {
  const steps = [ ['Bring the source', 'Upload an original Instagram clip you may use. A Reel link is a source reference; it does not grant access to Instagram media. Links alone cannot be analyzed in this free version.'], ['Inspect what is measurable', 'Your browser reads duration, dimensions, and six actual frames. Brightness is a numeric pixel measurement, not visual understanding or scene detection.'], ['Add the words', 'Paste reviewed spoken text, or opt into a browser-based Whisper tiny download. The model runs locally. English, Urdu, accents, music, and code switching can produce errors; correct the transcript first.'], ['Investigate the content', 'Creator notes use transparent metadata/text rules. Claim candidates are only a research queue. Wikipedia search retrieves real context with links and dates, not authoritative fact-check verdicts.'], ['Keep what is useful', 'Save studies explicitly in browser storage or export Markdown. Saved studies include text, metadata, and reference sources, but exclude the original video and frame images.'] ];
  return <><div className="section-intro"><span className="eyebrow">THE METHOD, IN THE OPEN</span><h1>Useful tools.<br/>Honest boundaries.</h1><p>ReelScope is an Instagram-first research workbench. It helps you inspect your material and gather references without invented performance scores.</p></div><div className="guide-grid"><section className="panel report-panel">{steps.map(([title, text], i) => <div className="guide-step" key={title}><span>{String(i + 1).padStart(2, '0')}</span><div><h2>{title}</h2><p>{text}</p></div></div>)}</section><aside className="panel report-panel guide-aside"><IconBadge><ShieldCheck size={25}/></IconBadge><h2>What “free/local” means</h2><p>No paid AI API is called. Video processing happens on the visitor’s device, which makes speed and browser compatibility important.</p><p>The initial speech model requires internet and browser cache space. Source searches use the app’s lightweight Vercel route to contact Wikipedia. Vercel’s plan and usage limits still apply.</p><h3>What this version does not do</h3><ul><li>Fetch arbitrary Instagram media from a link</li><li>Read private reach, retention, or demographics</li><li>Understand every visual scene or detect deepfakes</li><li>Guarantee engagement or declare a claim true/false</li><li>Automatically analyze YouTube, Facebook, or Snapchat</li></ul><a href="https://huggingface.co/Xenova/whisper-tiny" target="_blank" rel="noreferrer">Speech model and license <ArrowSquareOut size={14}/></a><a href="https://www.mediawiki.org/wiki/API:REST_API" target="_blank" rel="noreferrer">Reference search API <ArrowSquareOut size={14}/></a></aside></div></>;
}
