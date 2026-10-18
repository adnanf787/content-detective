import test from 'node:test';
import assert from 'node:assert/strict';
import { POST } from '../app/api/research/route';

const request = (data: unknown) => new Request('https://reelscope.example/api/research', { method: 'POST', body: JSON.stringify(data), headers: { 'Content-Type': 'application/json' } });
test('research rejects bad JSON, oversized content, and arbitrary target input', async () => {
  assert.equal((await POST(new Request('https://reelscope.example/api/research', { method: 'POST', body: '{broken' }))).status, 400);
  assert.equal((await POST(request({ query: 'a'.repeat(3000) }))).status, 413);
  assert.equal((await POST(request({ query: 'Pakistan', url: 'http://127.0.0.1' }))).status, 400);
});
test('research uses only the fixed wiki host and returns context without a verdict', async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async (input, options) => {
    const url = new URL(String(input));
    assert.equal(url.hostname, 'ur.wikipedia.org'); assert.equal(url.searchParams.get('q'), 'پاکستان');
    assert.equal(options?.redirect, 'error');
    return Response.json({ pages: [{ title: 'پاکستان', key: 'پاکستان', excerpt: 'Reference context' }] });
  };
  try {
    const result = await POST(request({ query: 'پاکستان', language: 'ur' }));
    assert.equal(result.status, 200);
    const body = await result.json(); assert.equal(body.sources.length, 1);
    assert.match(body.note, /not fact-check verdicts/);
  } finally { globalThis.fetch = original; }
});
test('upstream failures are surfaced without a fake source or claim judgment', async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async () => { throw new Error('offline'); };
  try {
    const result = await POST(request({ query: 'Pakistan' }));
    assert.equal(result.status, 502); const body = await result.json();
    assert.match(body.error, /could not reach Wikipedia/); assert.equal(body.sources, undefined);
  } finally { globalThis.fetch = original; }
});
