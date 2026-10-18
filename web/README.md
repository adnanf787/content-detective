# Content Detective web dashboard

The current Pakistan telecom YouTube research dashboard. This is the Next.js interface for the same Python analysis used by the root Streamlit assignment. The default page no longer opens the earlier ReelScope interface.

**Live dashboard: https://web-two-orpin-90.vercel.app**. The existing `web-adnan787.vercel.app` alias also serves this deployment but requires the existing Vercel login.

## Run locally

Use Python 3.12 and Node.js 22+ (Node 24 verified). From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn api.index:app --host 127.0.0.1 --port 8001
```

In a second terminal:

```bash
cd web
npm ci
npm run dev
```

Open http://127.0.0.1:3000. Next.js proxies local `/api/*` requests to port 8001. The included public snapshot loads without an API key: 30 videos and 279 sampled public comments.

## Current features

- Five sections: Overview, Content, Comments, Recommendations, Data & methods.
- Shared brand, measure, publication-date, video-age, and minimum-group-size filters.
- Actual brand medians, coverage, distributions, video ages, and seven-question evidence support.
- Suggested and reviewed topics/language, hashtags, Karachi publishing patterns, and searchable source videos.
- Sampled-comment search and cue filters, review-sheet download, and evaluation against uploaded human labels.
- Whole-workspace content-label review with a reviewer/codebook note; source counts remain preserved.
- Documented CSV import with reviewable column mapping, dataset status, timezone, and provenance.
- Optional official telecom-pilot collection using the visitor's own YouTube API key; no shared owner credential is used.
- Evidence-supported recommendation templates and an exportable writing brief. No AI model calls or predicted view gains.
- Filtered evidence ZIP, findings Markdown, analyzed-post CSV, linked-comment CSV, and analysis-summary JSON.

Workspaces are held in browser memory for the current visit and sent to the Python service for analysis. Imports, labels, and fresh collections do not modify the bundled snapshot or another visitor's workspace. Export work before closing or reloading. Hosted requests are limited to 3.5 MB; post CSV upload is limited to 2.5 MB and 5,000 rows. Private CSVs are sent to the app's backend for processing; review a file before uploading it.

## Deploy on Vercel

Import **the repository root**, select the **Services** framework, and use the root `vercel.json`. It deploys two services under one domain:

- `web/`: Next.js frontend.
- `api.index:app`, rooted at the repository root: FastAPI with the shared `src/` analysis modules and included snapshot.

The top-level rewrites route `/api/*` to Python and everything else to Next.js. Root Python dependencies come from `pyproject.toml`; frontend dependencies come from `web/package-lock.json`. No environment secrets are needed for the saved study.

Do not leave the Vercel Root Directory set to `web`. That configuration only builds the frontend and does not deploy the Python research service. See [deployment instructions](../docs/DEPLOYMENT.md).

## Verify

```bash
# From the repository root
.venv/bin/python -m pytest -q

# From web/
npm test
npm run typecheck
npm run build
```

The earlier ReelScope modules remain in source history and supporting files; they are not the current homepage. No Instagram retrieval or video transcription is implied by the current YouTube study.
