# Decisions and assumptions

## Phase 3 and dashboard redesign (2026-10-18; current scope)

- User cleared Phase 1, skipped Instagram, and requested Phase 3 plus a clean UI using Stitch. This supersedes earlier multi-platform UI plans. Preserve the existing Python research backend and prior web experiment.
- User explicitly authorized sharing the project UI brief, title, brand names, and aggregate counts with Google Stitch. The initial automatic approval rejection was resolved by that specific authorization. Only the approved design brief was sent; raw comment/transcript content and other credentials were excluded. Keep STITCH_API_KEY in ignored `.env` only.
- Adapt the successful Stitch reference to five native Streamlit sections, visible narrow-screen navigation, compact metrics, and one filter popover. Generated names or illustrative data are not research evidence. Use real brand names and computed values.
- Reuse shared cleaning, metrics, content rules, recommendations, and provenance. Add offline Phase 3 tables/report/ZIP and a guarded within-brand index. Preserve source CSVs; show unmatched or missing measurements honestly.
- Require repeated joint day/hour slots for timing comparisons. The current pilot has no eligible joint slot and no common brand age range, so it supports descriptive exploration and further labeling/collection rather than a causal optimum.
- Keep both caption tone and sampled-comment cues clearly unevaluated. Review/evaluation uploads need real human labels. Writing-brief export is the current AI-assistance handoff; an external model integration and pasted-link adviser remain later additions.

## YouTube acquisition milestone (2026-10-18; current scope)

- The user supplied the detailed implementation brief and explicitly prioritized YouTube first while deferring Instagram API work. A copy is preserved as `docs/PROJECT_SPECIFICATION.md`. The direct request overrides broader Instagram connector work in the attached plan for this milestone.
- Keep the supplied key only in ignored local `.env`, automatically loaded with python-dotenv. Public YouTube comment collection is explicitly authorized. Do not request author-profile fields or replies.
- Verify official account affiliation from corporate homepage hyperlinks and resolve immutable channel IDs through `channels.list`. Enumerate uploads with `playlistItems.list`; fetch metadata/metrics and capped newest top-level comments through official endpoints. Store raw responses before normalization, preserve missing values, and separate identity from observation snapshots in SQLite.
- The original April–September window supplied only 7 eligible Zong videos. The user explicitly approved extending all three brands' common window to October 2025–September 2026. The final pilot has 30 videos (10 per brand), 279 comments, zero API errors, and valid exports. Differences in actual publication dates/post ages remain visible.
- A cache resume is a replay of one snapshot, not refreshed analytics. The live resume made 0 new requests using 115 cached responses without duplicate rows. New acquisitions preserve additional metric snapshots.
- NLP is a transparent, unevaluated script/lexicon baseline with abstention. Human review and an evaluation upload are supported; no invented human labels or scores are used. A trained/evaluated multilingual model remains future work.
- Instagram CSV fallback accepts documented manual_public observations and validates provenance, dates, identities, URLs, and nullable metrics. Only fixtures were tested; no real Instagram collection or Meta connector is claimed.

## Assignment correction (2026-10-18; supersedes the web-product priority below)

- The user corrected the scope to the seven-question Pakistani Social Media Content Detective assignment. They confirmed no mandatory platform, sample size, or trained ML model, and requested a distinctive project beyond a classmate's YouTube API workflow.
- Restore the Python dashboard as the main deliverable and preserve `web/` as an earlier experiment. No production deployment is changed.
- Extend the existing analysis with Pakistan Content Lab: reviewed caption language, creative approach, and local context. These describe content, not viewer demographics. Compare observed metrics and quote sample sizes; do not invent empirical findings.
- Add manual public-post collection, optional bounded YouTube official API collection, staged CSV/source receipts, label editing, shared report tables, recommendation cards, and an AI evidence-prompt export. API collection needs a user-supplied key; no real dataset has been gathered yet. AI prompt export makes no model call.
- A pasted video adviser remains a later add-on requiring real benchmark data and a supported integration. No automatic Instagram/TikTok fetching or view prediction is claimed.
- Treat staged records as latest snapshots per platform/post ID; preserve each batch's source receipt separately. Collection stays in session memory until explicit download.

- 2026-10-17: Read the complete user-supplied master brief. Repository initially empty.
- Build a local Python 3.11+ / Streamlit / Pandas / Plotly MVP and shared-library Jupyter notebook. Python 3.12 is used for development because system Python is 3.9.
- User confirmed Streamlit + Jupyter, no dataset available, and approximately 3–4 days until submission. No additional course rubric or platform/brand priorities supplied.
- No verified real dataset was supplied. Demo accounts and observations are invented. No public dataset is downloaded or claimed verified. Real-data integration remains dependent on supplied observations.
- CSV is the supported import format; XLSX, linked comments, external LLM writing, deployment, and multilingual model evaluation are deferred optional enhancements.
- Use conservative ISO timestamps. Naive timestamps require explicit row timezone metadata or a declared import timezone; otherwise exclude them from local-time comparisons.
- Remove only identical original records, with counts reported. Retain conflicting source/account/post IDs in cleaned exports, flag them, and exclude them from analysis.
- Recommend using medians with a configurable minimum n (default 5). Rankings are descriptive; never generate statistical confidence scores.
- Use one metric for the active filtered dataset, favoring rate definitions with >=80% coverage. Partial coverage and cross-platform caveats stay visible. Users can explicitly select another metric.
- Audience fields are analyzed only with an explicit provenance note confirming segment evidence. Supplied captions and sentiment labels retain their source. Baseline sentiment is a tiny English lexicon with abstention for unsupported text, not a validated Urdu model.
- Keep uploads in session memory; no raw data is sent to an API or written to disk by the app. Export is explicit. Reports include the active manifest, filters, methodology, question support, and limitations.
- Verification refinements: abstain on ambiguous/nonexistent daylight-saving timestamps; foreign date-only observations cannot establish Karachi weekday. Reject pooled mixed-status recommendations and require a single status for dashboard analysis. Shortened overview labels after browser layout inspection.
- All 36 tests passed, and all eight notebook code cells executed. Actual browser upload/activation was verified. Browser ZIP download permission was declined, so saving that download remains unverified; no workaround was attempted.

## Web-product pivot (2026-10-17)

- User explicitly requested a polished video/link research tool deployed on Vercel, replacing the synthetic-data workflow as the primary product experience. Preserve the Python assignment project and build in web/.
- User selected both creator analysis and fact-checking/research, prefers free/local processing, and prioritizes Instagram for v1 testing.
- Use Next.js/React/TypeScript for Vercel. Process original uploaded videos in the browser; record Instagram URLs as source references. Do not claim arbitrary Instagram media retrieval without a supported integration.
- Free v1 combines real media metadata/frame sampling, opt-in local Whisper transcription, transparent transcript-based creator heuristics, claim candidates, and source-context retrieval. No virality predictions, fake scores, synthetic reports, or automatic truth verdicts.
- Local speech models require an initial download and can be slow or inaccurate, especially Urdu/code switching. Users can supply/correct a transcript.
- Reference retrieval sends only a user-triggered search query; the uploaded video stays local. Research results are context for verification, not proof of a claim. Optional external AI is not required for v1.
- Vercel deployment needs a connected Vercel account/project. No hosting purchase or paid AI API is authorized or required by the implementation.

- Vercel CLI temporary deployment was unavailable. User completed account/device authorization. Created and linked the new reelscope project in their workspace and deployed production at https://reelscope-nu.vercel.app; Vercel returned READY and the live page rendered successfully.
- Web verification: 17 tests, TypeScript and production builds passed; actual browser clip import/frame sampling, local English transcription, live reference retrieval, saved studies, and comparison were exercised. Urdu accuracy and automatic Instagram media retrieval remain unverified/unimplemented respectively.
