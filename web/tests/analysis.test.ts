import test from 'node:test';
import assert from 'node:assert/strict';
import { analyze, extractClaims, extractHashtags, extractKeywords, reportMarkdown } from '../lib/analysis';
import { parseInstagramUrl } from '../lib/instagram';
import { normalizeSources, researchSchema, plainText } from '../lib/research';
import { validateVideoFile } from '../lib/media';
import type { MediaInfo } from '../lib/types';

const media: MediaInfo = { name: 'owned.mp4', type: 'video/mp4', size: 10000, duration: 60, width: 1080, height: 1920, frames: [] };
const base = { goal: 'Improve my next Reel', language: 'auto', transcriptSource: 'manual' as const };

test('Instagram normalizes only permitted source URLs and removes tracking', () => {
  assert.equal(parseInstagramUrl('https://www.instagram.com/reel/Abc_123/?igsh=tracking').url, 'https://www.instagram.com/reel/Abc_123/');
  assert.equal(parseInstagramUrl('https://instagram.com/p/Abc123/').kind, 'post');
  assert.equal(parseInstagramUrl('https://m.instagram.com/reels/Abc123/').kind, 'reel');
});
test('Instagram refuses spoofed hosts, private routes, credentials and network targets', () => {
  for (const url of ['https://instagram.com.evil.example/reel/Abc123/', 'http://instagram.com/reel/Abc123/', 'https://instagram.com@evil.example/reel/Abc123/', 'https://instagram.com/direct/inbox', 'https://instagram.com/stories/user/123/', 'https://127.0.0.1/reel/Abc123/', 'https://instagram.com:4000/reel/Abc123/']) assert.throws(() => parseInstagramUrl(url));
});
test('a URL alone never becomes content analysis', () => {
  assert.throws(() => analyze({ ...base, media: null, transcript: '', instagramUrl: 'https://www.instagram.com/reel/Abc123/' }), /original video or a transcript/);
});
test('metadata-only study has no fabricated text, audience, claims or performance', () => {
  const result = analyze({ ...base, media, transcript: '' });
  assert.equal(result.wordCount, 0); assert.equal(result.wordsPerMinute, null); assert.equal(result.opening, '');
  assert.equal(result.claims.length, 0); assert.equal(result.transcriptSource, 'none');
  assert.ok(result.limitations.some(l => l.includes('No transcript')));
  assert.ok(result.limitations.some(l => l.includes('analytics')));
});
test('creator text evidence derives from the supplied transcript', () => {
  const text = 'Learning helps people. Learning needs practice. The first course launched in 2024.';
  const result = analyze({ ...base, media, transcript: text });
  assert.equal(result.wordCount, 12); assert.equal(result.wordsPerMinute, 12);
  assert.equal(result.keywords.find(k => k.term === 'learning')?.count, 2);
  assert.ok(result.observations.some(o => o.evidence.includes('1080 × 1920')));
  assert.ok(result.observations.some(o => o.evidence.includes('Learning helps people.')));
});
test('text-only input has no invented duration or speech rate', () => {
  const result = analyze({ ...base, media: null, transcript: 'A new product is ready for review.' });
  assert.equal(result.media, null); assert.equal(result.wordsPerMinute, null);
});
test('Unicode hashtags and words preserve Urdu and combining marks', () => {
  assert.deepEqual(extractHashtags('#پاکستان #خُوبصورت #STYLE #style'), ['#پاکستان', '#خُوبصورت', '#style']);
  assert.ok(extractKeywords('پاکستان پاکستان').some(k => k.term === 'پاکستان' && k.count === 2));
});
test('claim candidates stay unverified, including numeric and Urdu text', () => {
  const claims = extractClaims('This product always cures every illness. The project began in 2023. اس شہر کی آبادی دس لاکھ ہے۔ What is a good design?');
  assert.equal(claims.length, 3); assert.ok(claims.every(c => c.status === 'Needs verification' && !c.sources.length));
});
test('ordinary transcript with no rule matches is not declared accurate', () => {
  const result = analyze({ ...base, media: null, transcript: 'Welcome to our new collection. Enjoy a closer look at the design.' });
  assert.equal(result.claims.length, 0);
  assert.ok(result.observations.some(o => o.suggestion.includes('does not mean the video is factually correct')));
});
test('reports quote sources and honest method limitations', () => {
  const result = analyze({ ...base, media: null, transcript: 'The project began in 2023.' });
  result.claims[0].sources = [{ title: 'Project reference', url: 'https://example.org/evidence', excerpt: 'A related context snippet.', publisher: 'Example reference', retrievedAt: '2026-10-17' }];
  const md = reportMarkdown(result);
  assert.match(md, /Needs verification/); assert.match(md, /https:\/\/example.org\/evidence/);
  assert.match(md, /No video inspected/); assert.match(md, /No automatic true\/false verdict/);
});
test('oversized transcript is rejected', () => {
  assert.throws(() => analyze({ ...base, media: null, transcript: 'a'.repeat(60001) }), /60,000/);
});
test('video accepts only valid bounded original files', () => {
  validateVideoFile({ name: 'clip.mp4', type: 'video/mp4', size: 1024 });
  assert.throws(() => validateVideoFile({ name: 'huge.mp4', type: 'video/mp4', size: 200 * 1024 * 1024 }));
  assert.throws(() => validateVideoFile({ name: 'empty.mp4', type: 'video/mp4', size: 0 }));
  assert.throws(() => validateVideoFile({ name: 'page.html', type: 'text/html', size: 100 }));
});
test('research schema forbids arbitrary upstream hosts and unsupported languages', () => {
  assert.equal(researchSchema.parse({ query: 'Pakistan' }).language, 'en');
  assert.equal(researchSchema.safeParse({ query: 'Pakistan', url: 'http://127.0.0.1' }).success, false);
  assert.equal(researchSchema.safeParse({ query: 'Pakistan', language: 'invalid' }).success, false);
  assert.equal(researchSchema.safeParse({ query: 'x' }).success, false);
});
test('reference parsing removes markup, bounds results, and constructs safe citations', () => {
  const result = normalizeSources([{ title: '<b>Pakistan</b>', key: 'Pakistan', excerpt: 'A <span>reference</span> &amp; context.' }], 'en', '2026-10-17');
  assert.equal(result[0].title, 'Pakistan'); assert.equal(result[0].excerpt, 'A reference & context.');
  assert.equal(result[0].url, 'https://en.wikipedia.org/wiki/Pakistan');
  assert.equal(result[0].retrievedAt, '2026-10-17');
  assert.deepEqual(normalizeSources(null, 'en'), []);
  assert.equal(plainText('a'.repeat(5000)).length, 1000);
});
