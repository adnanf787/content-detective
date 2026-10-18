# ReelScope

Instagram-first video research for creators: inspect an original clip, review its spoken text, investigate factual assertions, and export evidence-based editing notes.

Live production: **https://reelscope-nu.vercel.app**.

The main project is now the Pakistani Social Media Content Detective assignment dashboard in the parent directory. This earlier video/fact-checking experiment is preserved for possible later reuse; it is not the assignment workflow. See the parent README for the corrected scope.

## Run locally

Node.js 22+ is required (Node 24 tested).

```bash
cd "/Users/adnan/Documents/ChatGPT/scraper tool/web"
npm ci
npm run dev
```

Open http://127.0.0.1:3000. No paid AI API key is required. There are no synthetic reports or sample engagement metrics in the product.

## What works

- Original MP4/WebM/MOV selection or drag-and-drop, with a local video preview; file-size/codec/duration validation (150 MB, 5 minutes maximum).
- Real metadata and six actual frame samples with timestamps and measured average luminance.
- Instagram Reel/post URL validation and canonical source references, including tracking-parameter removal. Links alone do **not** provide video content.
- User-reviewed transcripts, preserved Unicode text, and opt-in local Whisper tiny transcription in a browser worker. First use downloads model/runtime files from Hugging Face/CDNs; audio stays in the browser.
- Transparent creator notes based on actual dimensions, duration, transcript token counts, repeated terms, opening excerpt, and text-rule claim candidates. No fabricated retention/virality scores.
- Claim review queue, manual candidate addition, real English/Urdu Wikipedia context retrieval with citation URLs and retrieval dates, and links for additional web/professional fact-check searches.
- Explicit unverified status: retrieved references are not automatic true/false verdicts.
- Saved studies and side-by-side measurement comparison in browser storage. Save is explicit; original video and frame thumbnails are excluded from persistent reports.
- Markdown export with source provenance, evidence, method limitations, and retrieved reference context.
- Responsive, accessible navigation, loading/error states, local processing notices, and documented methods.

## Free/local trade-offs

The browser handles media and speech inference. Speed depends on hardware, browser, and codec. Tiny Whisper can make serious transcription errors, especially with Urdu, code switching, music, accents, and silence. Review every transcript.

The creator notes are deterministic heuristics, not a large model's full interpretation of the video. Frame samples do not detect objects, scenes, cuts, manipulation, or deepfakes. Keyword repetition is not a trend signal.

The only app-server feature is a bounded reference-search endpoint against fixed Wikipedia hosts. A user-triggered query is sent to Wikipedia; raw video, audio, and full transcripts are not automatically transmitted. Research queries may themselves contain private information, so review the query before searching.

## Instagram access boundary

This version **cannot fetch arbitrary Instagram media from pasted links**, access private analytics, or bypass platform access restrictions. Upload an original file you may use and optionally attach its Instagram URL. Automatic retrieval requires a supported, separately implemented integration and appropriate access; it is not silently simulated.

YouTube, Snapchat, and Facebook are not implemented for this Instagram-first release. There is no claim that a public Instagram post supplies audience geography, retention, reach, shares, or follower demographics.

## Deploy on Vercel

Deploy the **web/** directory as the project root. Framework: **Next.js**. Build: `npm run build`. Install: `npm ci`. Output directory: default. Node.js: 24 (or another compatible version supported by the chosen Vercel project).

There are no required environment secrets, no video-storage bucket, no long-running GPU server, and no server-side video upload endpoint. Large files remain on the visitor's device, so they do not pass through Vercel Functions' request bodies. Hosting remains subject to Vercel's account/plan and usage limits.

Using an authenticated Vercel CLI:

```bash
cd "/Users/adnan/Documents/ChatGPT/scraper tool/web"
npx vercel
npx vercel --prod
```

For Git integration, push the repository to your chosen Git host, import it into Vercel, and set Root Directory to `web`. Publishing requires your Vercel account authorization. Do not put credentials in source files or paste tokens into chat.

## Verification

```bash
npm test
npm run typecheck
npm run build
```

Tests exercise source URL validation, unsupported inputs, nullable measurements, transcript evidence, Urdu/Unicode processing, unverified claim guardrails, safe reference normalization, and bounded query inputs. See `../docs/WEB_PRODUCT.md` for verification status and outstanding integration limits.

## Data lifecycle

- A new study uses in-memory browser state. Video object URLs are released when replaced or unmounted.
- Local speech-model downloads are cached by the browser/model runtime. No media is submitted to a hosted speech API.
- Saving explicitly persists report text, metadata, and retrieved references in localStorage, up to 20 studies. Original media and frame data URLs are excluded.
- Removing a saved study removes that browser copy. Exported files and other saved browser sessions are separate copies.
- No account system, cross-device sync, analytics tracking, or hosted media archive is implemented.

## Extending the product

Priorities after testing on a real owned Instagram Reel: validate Urdu transcription with reviewed examples; obtain a supported Instagram media integration; add professional fact-check data sources with documented access; consider an optional local semantic model. Stronger factual verdicts need actual evidence comparison, reliable sources, date/context checks, and human review. They must not be inferred from search-result matches.
