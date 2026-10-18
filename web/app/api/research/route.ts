import { researchSchema, normalizeSources } from '@/lib/research';
export const runtime = 'nodejs';
export const maxDuration = 15;

export async function POST(request: Request) {
  const body = await request.text();
  if (body.length > 2000) return Response.json({ error: 'Search request is too large.' }, { status: 413 });
  let input;
  try { input = researchSchema.parse(JSON.parse(body)); }
  catch { return Response.json({ error: 'Use a search query of 3–180 characters and a supported language.' }, { status: 400 }); }
  try {
    const url = new URL(`https://${input.language}.wikipedia.org/w/rest.php/v1/search/page`);
    url.searchParams.set('q', input.query); url.searchParams.set('limit', '5');
    const response = await fetch(url, { headers: { 'User-Agent': 'ReelScope/0.1 (educational reference search)', Accept: 'application/json' },
      signal: AbortSignal.timeout(8000), redirect: 'error', cache: 'no-store' });
    if (!response.ok) return Response.json({ error: `Reference search is temporarily unavailable (${response.status}). Use the external search links or try later.` }, { status: 502 });
    const data = await response.json();
    return Response.json({ sources: normalizeSources(data.pages, input.language), query: input.query,
      note: 'Related references, not fact-check verdicts. Read original sources and verify that they address the exact claim.' },
      { headers: { 'Cache-Control': 'no-store' } });
  } catch {
    return Response.json({ error: 'Reference search could not reach Wikipedia. Check your connection or use the external research links.' }, { status: 502 });
  }
}
