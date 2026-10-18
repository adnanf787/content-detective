# Verification record

## Latest Stitch screen adaptation — 2026-10-18

- Retrieved the existing project's second screen, `15bec2f4c90949b5ac3133907cea9405` (Content Detective - Interactive Analytical Dashboard), using the official Stitch MCP endpoint. Downloaded its screenshot and HTML from the Google asset URLs returned by that endpoint. Inspected the generated HTML as data; no generated scripts were executed and no research rows were uploaded.
- Adapted its emerald study panel, neutral canvas, white metric cards, desktop side rail, and brand-composition panel to the working Streamlit application. Narrow screens retain the five visible destinations. Brand coverage and metric-help text are derived from the active sample. Generated PTCL/JazzDigital/version labels were not copied as facts.
- Added `docs/FEATURE_GUIDE.md`, also readable within Data & methods → Study & quality. It distinguishes actual API observations, calculations, configured sample settings, coded cue rules, and template-based recommendations, and explains every analysis/import/export control.
- **72 tests passed**, including the desktop export shortcut's navigation callback and title-only library search. Browser verified the new narrow-screen layout and guide entry against the actual sample; proof is in `docs/stitch-redesign-preview.jpg`. Desktop side-rail CSS is implemented but has not been separately screenshot-tested in a wide viewport.

## Phase 3 analysis and UI — 2026-10-18 (current)

- Replaced 15 competing destinations with **Overview, Content, Comments, Recommendations, Data & methods**. The saved validated pilot loads offline automatically; the visible Filter sample popover contains native filters. Collection, import, label review, formulas, and exports are grouped under Data & methods.
- Google Stitch generated a desktop reference using the exact user-approved UI brief and aggregate counts. The reference is preserved under `docs/stitch/`; its HTML was treated as a design reference, not executed as application code. No raw comments, transcripts, or YouTube credentials were sent to Stitch.
- `scripts/analyze_youtube.py` executed against **30 actual videos and 279 linked comments**, without API calls. Derived CSVs, JSON summary, Markdown report, and ZIP were created. Their age-overlap flag is false; the 14 positive / 9 negative / 256 unassessed cue counts remain explicit. No human evaluation score or trained-model accuracy is reported.
- **72 automated tests passed**, including five-section AppTest navigation, offline autoload, empty/incomplete data, brand filtering, label-review navigation, comment coverage, legacy-session migration, guarded within-brand indexing, non-overlapping ages, sparse joint timing slots, and filtered ZIP/comment linkage. Existing acquisition/validation tests continue to pass.
- Browser checked the actual five-section layout in the 603px in-app panel: header and navigation fit, native metric tiles form a readable 2×2 grid, Filter sample opens, Content tabs render, the sparse timing view refuses a recommendation, and Comments shows **279 / 23 / 256 / 8.2%**. Actual overview proof: `docs/phase3-overview.jpg`. Wide desktop rendering has not been separately screenshot-tested.
- Actual saved-data AppTest rendered all five sections plus the five export controls without exceptions. The generated ZIP passed its integrity check and contains 14 entries, 30 analyzed videos, and 279 linked comments. Both Phase 1 source CSVs remain byte-identical to the archived acquisition snapshot. An exact-key scan found zero matches outside ignored `.env`, with owner-only mode `0600`. Browser file saving was not repeated. Synthetic fixtures remain separate from the actual empirical run. Instagram remains deferred. AI-assisted writing is a downloadable evidence brief, not an external model call.

## YouTube-first real-data milestone — 2026-10-18 (historical UI checkpoint)

- Exact corporate homepage hyperlinks were fetched for Jazz, Zong, and Ufone and resolved with official `channels.list`. `scripts/verify_youtube_channels.py` was executed live and all three were verified. Evidence is in `config/brands.yml` and `config/brand_verification.json`.
- First live April–September run: **27 videos / 238 comments / 0 API errors**; Zong had only 7 eligible uploads. The user explicitly approved a common October 2025–September 2026 window. Expanded live run: **30 videos / 279 sampled top-level public comments / 0 API errors**, with 10 videos per brand. Counts and all missing fields are in `docs/YOUTUBE_COLLECTION_LOG.md` and `data/processed/youtube_collection_report.json`.
- Actual CSVs were reloaded and validated: unique identities, post/comment linkage, count validity, HTTPS sources, explicit timezones, and chronological plausibility passed. SQLite foreign-key checks passed. Current SQLite contains 30 unique posts, 279 unique comments, and 57 separate measurement snapshots across the two acquisition runs.
- Actual resume of `20261018T070121103737Z`: **0 new network requests, 115 cached responses**; original observation timestamps retained and no duplicate posts, comments, or metric snapshots added. Source request success/cache handling is distinct from controlled fixture tests.
- Real-pilot AppTest loaded the actual saved CSVs and linked comments and rendered **all 15 pages** without exceptions. The in-memory schema migration is separately covered after an older browser dataset exposed a missing derived-column problem.
- `scripts/execute_notebook.py --notebook notebooks/youtube_pilot_analysis.ipynb`: **all 6 code cells executed** with actual source coverage, post-age ranges, charts, cue-label counts, and a computed findings export.
- `python -m pytest -q`: **65 tests passed**. Coverage adds retry/key/quota errors, comment-disabled states, pagination, date-window/shortfall behavior, raw credential/profile-field exclusion, cache replay and SQLite idempotence, strict five-row Instagram CSV fixtures, missing metrics, post ages, NLP abstention/evaluation, source-example citations, and schema migration. Syntax compilation and whitespace checks also passed.
- Browser verification: restarted the local server to load updated modules, activated the actual 30-video pilot, and confirmed the collection summary shows **30 videos, 279 comments, status complete, 0 API errors, validation passed**, with brand counts 10/31, 10/140, and 10/108. Saved the visible proof in `docs/youtube-collection-preview.jpg`. The app remains open on that summary; download file saving was not separately exercised through the browser.
- Local `.env` was created with owner-only mode `0600` and is Git-ignored. An exact credential scan found **0 occurrences outside `.env`** in inspected project/data artifacts. Raw and processed research data plus SQLite are also ignored.
- **Unverified/deferred:** no real Instagram media or Business Discovery request; CSV fallback tested with controlled fixtures only. No human sentiment evaluation set, trained multilingual model, calibrated confidence, audience-demographic evidence, or external AI recommendation call. Baseline cue labels cover only 23/279 sampled comments and remain unevaluated. These limits are visible in UI and reports.

The earlier entries below are historical checkpoints and do not describe the current real-data availability.

## Assignment correction verified on 2026-10-18

- `python -m pytest -q`: **54 tests passed**. Includes all prior coverage plus accepted/rejected video URL forms, deduplication, bounded search pagination and metadata batches, omitted IDs, missing API counts, credential-safe errors/receipts, exact manual observations, visible interactions per 1,000 views, Pakistan content comparisons in recommendations/exports, and the manual staging → activation → annotation → lab workflow.
- Streamlit AppTest visits every page with both the synthetic demo and a captions-only dataset. Fixed an existing filter bug that excluded every post when a category had no supplied values; partially labeled collections now remain analyzable. Explicitly clearing a populated filter still returns no rows.
- `python scripts/execute_notebook.py`: all **8 code cells executed**, with refreshed outputs saved. A local kernel required sandbox escalation for loopback socket binding; execution then succeeded.
- Syntax compilation passed. The local Streamlit server is bound to `127.0.0.1:8501` for review.
- In-app browser: inspected the empty-state assignment story, manual/API collection tabs, synthetic dataset loading, and actual Pakistan Content Lab language charts/tables. Saved a labeled synthetic preview in `docs/pakistan-content-lab-preview.png`. Manual staging/activation and annotation submission were exercised through AppTest rather than entering invented posts as real in the browser.
- **No live YouTube call was made**: no API key was supplied. API integration behavior is tested with controlled responses, not a live-service guarantee. **No real dataset has yet been collected**, and no actual Pakistani audience finding or trained multilingual model is claimed. Browser file downloads for the new collection exports have not been exercised.

## Earlier verification (historical)

Verified locally on 2026-10-17 using Python 3.12.14 on Apple Silicon. Exact installed dependencies are in requirements-lock.txt.

## Completed checks

- `python -m pytest -q`: **36 tests passed**. Covers nullable/missing counts, positive rate denominators, observed zeros, invalid inputs, metric selection, coverage/mean/median/n, exact vs conflicting duplicates, mapping aliases, Unicode hashtags, caption preservation, sentiment abstention/source, recommendation evidence/sparsity/coverage, mixed-data separation, audience provenance guards, and conservative timezone parsing including daylight-saving ambiguity.
- Streamlit AppTest: welcome/empty state, demo loading, every page, platform filtering (180 → 60 rows), empty selection, and every page with a captions-only dataset lacking all measurements.
- `python scripts/execute_notebook.py`: all **8 code cells** executed successfully with displayed tables, Plotly charts, recommendations, and executive summary saved into the notebook.
- `python -m compileall -q app.py src scripts`: syntax/import compilation passed.
- Local Streamlit server started on `http://127.0.0.1:8501`.
- Browser: welcome and synthetic overview rendered; narrow-panel layout inspected. Actual CSV file chooser uploaded the 180-row demo; reviewable mapping and manifest rendered, form activated, and quality scorecard displayed 180 rows, 0 conflicts, 0 invalid numeric entries, known timestamps, and persistent SYNTHETIC DEMO status. Report/export page rendered all seven questions and export controls.

## Limitations of verification

- The final browser ZIP download was blocked by browser security review because download permission was declined. No bypass/retry was attempted. Export-page execution and Markdown report generation passed, but the actual saved ZIP was not verified through the browser.
- No real dataset has been supplied or analyzed. No candidate external dataset, license, real audience segment, or sentiment accuracy has been verified.
- Initial dependency download and local server/kernel startup needed sandbox approval. They were subsequently authorized and succeeded. These are development-environment permissions, not application API-key requirements.
- AppTest does not implement the file-uploader interaction, so the actual uploader was separately checked in the browser. Alternate aliases and mapping collisions are covered by unit tests.

Re-run these checks after changing analytics. Real-data integration requires its own profile, provenance audit, mapping review, and interpretation before any empirical conclusion.
