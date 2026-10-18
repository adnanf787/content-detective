import type { MediaInfo, Report, Observation, Claim } from './types';

const STOP = new Set('the and that this with from have your you for are was were into can will would could should about there their they them our what when where how why just more some than then also not its it is of to in on a an as be by or at we i my me us he she his her has had but if so do did an up out all very really hai hain aur ka ki ke ko se yeh woh mein bhi aik'.split(' '));
export function words(text: string): string[] {
  return text.toLocaleLowerCase().match(/[\p{L}\p{M}\p{N}]+(?:['’][\p{L}\p{M}]+)?/gu) || [];
}
export function extractKeywords(text: string) {
  const counts = new Map<string, number>();
  for (const token of words(text)) if (token.length > 2 && !STOP.has(token) && !/^\d+$/.test(token)) counts.set(token, (counts.get(token) || 0) + 1);
  return [...counts].map(([term, count]) => ({ term, count })).sort((a, b) => b.count - a.count || a.term.localeCompare(b.term)).slice(0, 10);
}
export function extractHashtags(text: string): string[] {
  return [...new Set((text.match(/#[\p{L}\p{M}\p{N}_]+/gu) || []).map(t => t.toLocaleLowerCase()))];
}
export function extractClaims(text: string): Claim[] {
  const sentences = text.split(/(?<=[.!?۔！？])\s+|\n+/u).map(s => s.trim()).filter(Boolean);
  return sentences.filter(s => s.length >= 20 && s.length <= 600 && !/[?؟]\s*$/.test(s) &&
    (/\d|\b(study|studies|research|proven|always|never|cure|cures|causes?|percent|largest|first|banned|according|million|billion|scientists|guarantee)\b/i.test(s) || /ہے|ہیں|فیصد|تحقیق|علاج|ثابت/.test(s)))
    .slice(0, 8).map((text, i) => ({ id: `claim-${i}`, text,
      reason: /\d|percent|فیصد/.test(text) ? 'Contains a numerical or dated assertion. Verify the figure and its context.' : 'Contains wording that may make a factual assertion. Human review is required.',
      status: 'Needs verification', sources: [] }));
}

export type AnalysisInput = { name?: string; instagramUrl?: string; goal: string; transcript: string; transcriptSource: Report['transcriptSource']; language: string; media: MediaInfo | null };
export function analyze(input: AnalysisInput): Report {
  const transcript = input.transcript.trim();
  if (!input.media && !transcript) throw new Error('Add an original video or a transcript first. An Instagram link alone does not supply its content.');
  if (transcript.length > 60000) throw new Error('Transcript exceeds the 60,000-character limit.');
  const tokens = words(transcript);
  const sentences = transcript.split(/(?<=[.!?۔！？])\s+|\n+/u).filter(s => s.trim());
  const keywords = extractKeywords(transcript);
  const claims = extractClaims(transcript);
  const duration = input.media?.duration;
  const wordsPerMinute = duration && tokens.length ? Math.round(tokens.length / duration * 60) : null;
  const observations: Observation[] = [];
  const opening = sentences[0]?.slice(0, 320) || '';
  if (opening) {
    observations.push({ title: 'Make the opening earn its place', category: 'Content', evidence: `The first transcript sentence is: “${opening}”`,
      suggestion: 'Test a shorter opening that leads with the viewer’s problem or the result. Compare it with your current opening; this is an editing experiment, not a retention prediction.' });
  }
  if (keywords.length) {
    observations.push({ title: 'Build the next post around one clear thread', category: 'Content', evidence: keywords.slice(0, 3).map(k => `“${k.term}” appears ${k.count} time${k.count === 1 ? '' : 's'}`).join('; ') + '.',
      suggestion: `Test a focused follow-up explaining “${keywords[0].term}” with a concrete example. Repeated words are topic clues, not trend or audience-demand evidence.` });
  }
  if (wordsPerMinute !== null) {
    observations.push({ title: 'Review the delivery against the transcript', category: 'Delivery', evidence: `${tokens.length} transcript tokens across ${duration!.toFixed(1)} seconds gives approximately ${wordsPerMinute} words/minute.`,
      suggestion: wordsPerMinute > 190 ? 'The transcript is dense relative to the clip length. Check for a pasted caption or inaccurate transcript first; if this is all spoken, test fewer words and more pauses.' : 'Read the transcript alongside the audio and check pauses, on-screen captions, and clarity. This whole-clip estimate includes silence and is not a measured speaking rate.' });
  }
  if (input.media) {
    const { width, height, duration, frames } = input.media;
    observations.push({ title: height > width ? 'Portrait canvas detected' : 'Review the canvas for a Reel', category: 'Format', evidence: `The actual file is ${width} × ${height} pixels (${(width / height).toFixed(2)}:1), ${duration.toFixed(1)} seconds.`,
      suggestion: height > width ? 'Inspect text, faces, and subtitles in the frame strip. Keep important details clear of interface overlays and compare the result in Instagram’s preview.' : 'Test a portrait edit and check the crop manually. Orientation is a technical observation, not proof that another format will perform better.' });
    if (frames.some(f => f.brightness < 25)) observations.push({ title: 'Inspect the darkest sampled frame', category: 'Format', evidence: `${frames.filter(f => f.brightness < 25).length} of ${frames.length} sampled frames have average luminance below 25/255.`, suggestion: 'Review the frame strip. A dark frame may be intentional; check subject visibility and caption contrast before changing it.' });
  }
  observations.push({ title: claims.length ? 'Source the checkable statements' : 'Keep claims traceable', category: 'Trust', evidence: `${claims.length} possible factual assertion${claims.length === 1 ? '' : 's'} flagged by transparent text rules. This is not exhaustive claim detection.`,
    suggestion: claims.length ? 'Review each candidate, search its precise wording, and compare original sources and dates. Reference matches do not establish whether a claim is true.' : 'No candidate matched the simple rules. That does not mean the video is factually correct. Add a claim manually in the research panel if needed.' });
  return {
    id: crypto.randomUUID(), name: input.name?.trim() || input.media?.name || (transcript ? tokens.slice(0, 6).join(' ') : 'Untitled research'),
    createdAt: new Date().toISOString(), instagramUrl: input.instagramUrl || '', goal: input.goal,
    transcript, transcriptSource: transcript ? input.transcriptSource : 'none', language: input.language,
    media: input.media, wordCount: tokens.length, sentenceCount: sentences.length, wordsPerMinute,
    opening, keywords, hashtags: extractHashtags(transcript), observations, claims,
    limitations: [
      'No Instagram performance or audience analytics were retrieved. Reach, retention, demographics, and viral potential are unknown.',
      'Creator notes are deterministic editing suggestions based on measured metadata and supplied text. They are not full semantic video understanding.',
      'Frame inspection samples the video and measures brightness only. It does not identify objects, people, scenes, cuts, or authenticity.',
      'Claim candidates use text rules and may miss assertions or flag opinions. No automatic true/false verdict is issued.',
      'Wikipedia search results are reference context, not authoritative fact-checks. Check primary sources, dates, and original media.',
      ...(transcript ? ['Transcripts can be wrong or incomplete. Local Whisper is especially uncertain for Urdu, Roman Urdu, accents, music, and code switching. Review the words before interpreting results.'] : ['No transcript is present. Content, topic, and claim analysis are unavailable; only file-level observations are supported.']),
    ],
  };
}

export function formatTime(seconds: number) {
  return `${Math.floor(seconds / 60)}:${Math.floor(seconds % 60).toString().padStart(2, '0')}`;
}
export function reportMarkdown(r: Report): string {
  const media = r.media ? `${r.media.width} × ${r.media.height}, ${r.media.duration.toFixed(1)} seconds, ${(r.media.size / 1048576).toFixed(1)} MB` : 'No video inspected; transcript-only study';
  return [`# ReelScope: ${r.name}`, `Created: ${r.createdAt}`, `Source: ${r.instagramUrl || 'User-provided original file/text'}`, `Goal: ${r.goal}`, `Media: ${media}`, `Transcript provenance: ${r.transcriptSource}`, `Words: ${r.wordCount}; whole-clip words/minute: ${r.wordsPerMinute ?? 'unavailable'}`, '## Creator notes', ...r.observations.map(o => `### ${o.title}\nEvidence: ${o.evidence}\n\nExperiment: ${o.suggestion}`), '## Claim research', ...(r.claims.length ? r.claims.map(c => `### ${c.text}\nStatus: ${c.status}. ${c.reason}\nResearch query: ${c.researchQuery || "No reference query recorded"}\n${c.sources.map(s => `- [${s.title}](${s.url}) — ${s.publisher}, retrieved ${s.retrievedAt}\n  Reference context: ${s.excerpt}`).join('\n') || 'No reference sources retrieved.'}`) : ['No candidates matched the rules. This is not proof of factual accuracy.']), '## Transcript', r.transcript || 'Unavailable', '## Limitations', ...r.limitations.map(l => `- ${l}`)].join('\n\n');
}
