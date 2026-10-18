# ReelScope web product

The user refined the master brief into an Instagram-first creator-analysis and fact-research tool with a polished UI, free/local processing, and Vercel hosting. The original Python assignment project is preserved. The web app is in `web/`.

## Implemented

Next.js / React / TypeScript; locally bundled DM Sans and Manrope; responsive navigation and empty states; real original-video import, metadata, six frame samples, local preview, opt-in browser Whisper tiny transcription, Unicode transcript editing, transcript-based creator heuristics, manual/automatic claim queue, Wikipedia source context with linked citations, explicit unverified status, browser-local saved reports, two-report comparison, and Markdown export.

No synthetic example reports or engagement metrics are loaded by the product. A generated color-bar clip with original system speech was used only as an external temporary QA fixture. It is not shipped as empirical content.

## Verified

- `npm run build`: optimized Next.js production build passed.
- `npm run typecheck`: passed.
- `npm test`: 17 tests passed, covering Instagram URL validation, hostile/spoofed URL refusal, missing video/transcript states, actual text-derived evidence, Unicode/Urdu handling, unverified claim guardrails, bounded reference inputs, fixed upstream hosts, malformed request handling, and upstream-failure transparency.
- Browser: original 360×640 test clip imported with its measured ~7-second duration and six real frame samples; local Whisper downloaded and transcribed the clip on-device; generated report preserved local-transcript provenance, measured file dimensions, and unknown performance data.
- Browser: manually added research candidate retrieved five real English Wikipedia references for a user-specified query. Candidate status remained Needs verification.
- Browser: two explicitly saved transcript studies compared their different 15/18-word totals, unknown durations/rates, different claim counts, and unknown Instagram performance. Original videos and frames are excluded from stored reports.
- Production API: the hosted /api/research endpoint returned five real reference results successfully for a public test query.
- Browser download checks were not repeated after the earlier download-permission decline in the assignment-dashboard task. Markdown export generation is covered in tests; actual saved-file browser download remains unverified.

## Boundaries

The app does not automatically retrieve video from arbitrary Instagram URLs; an original file or transcript is required. It does not fetch private analytics, perform full semantic video interpretation, detect deepfakes, predict virality, or make automatic true/false verdicts. Wikipedia snippets are related context, not authoritative claim verification. Urdu/English transcription accuracy has not been evaluated on a reviewed corpus. A small successful English test does not establish model accuracy.

Videos stay on-device. User-triggered research queries go through the Vercel route to a fixed Wikipedia host. Explicitly saved studies remain in that browser's localStorage, capped at 20; original video and frame images are excluded. Model/runtime assets require an initial download and browser cache space. No paid AI API key is required.

## Deployment

Vercel project root is `web/`; framework Next.js; install `npm ci`; build `npm run build`. Production requires the user's authorized Vercel account. The temporary unauthenticated path was unavailable; the user completed device authorization. Vercel confirmed READY for production at https://reelscope-nu.vercel.app (deployment dpl_7zFugFUQ2gs4tbLPswjLTV7qzTvM). The deployed page was opened successfully in the browser. Deployment input inspection confirmed 20 web-only files (~171 KB) and excluded local credentials, node_modules, build output, test fixtures, and the Python project.
