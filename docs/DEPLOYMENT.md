# Deploy Content Detective on Vercel

The current hosted application uses a Next.js interface in `web/` and a stateless FastAPI service in `api/index.py`. The API reuses the same `src/` cleaning, measurement, NLP cue, recommendation, and export code as the Streamlit assignment. `app.py` remains a local Streamlit entry point.

## Existing Vercel project

1. Sign in to the Vercel account that owns the site you want to replace (the supplied site was `web-adnan787.vercel.app`). Verify the project and domain before changing it; the old local CLI link names a separate project, `reelscope`.
2. Connect **adnanf787/content-detective**, production branch **main**.
3. In Build and Deployment settings, set **Root Directory** to the repository root (clear `web`). Select **Services** as the framework preset. Remove previous project-level Next.js build/install/output overrides; each service declares its own commands in the root `vercel.json`.
4. Use Node.js **24** for the frontend. The Python backend uses **3.12**, declared in `.python-version` and supported by `pyproject.toml`.
5. Deploy the latest `main` commit. The root configuration builds the two services together and routes requests under one domain.

No secrets are required to browse the saved pilot. The new homepage is **Content Detective — Pakistan Telecom Research**, with Overview, Content, Comments, Recommendations, and Data & methods. It should not show ReelScope or an Instagram upload screen.

Subsequent pushes to `main` trigger Vercel deployments when the Git integration is connected. GitHub contains the complete source, not a running application preview.

## Included snapshot

Git includes only these three processed public-pilot files:

- `data/processed/youtube_posts.csv`: 30 public videos, ten per verified brand.
- `data/processed/youtube_comments.csv`: 279 sampled public comments, without author profile fields.
- `data/processed/youtube_collection_report.json`: observation times, validation, counts, and limitations.

The bundled observations were collected on October 18, 2026. They do not continuously refresh. Credentials, raw responses, the local SQLite database, and other generated outputs stay excluded. Raw-response lineage paths identify local receipts but do not bundle those receipts in the hosted app.

## Workspace and collection behavior

Imports, label edits, and fresh collections live in each browser's current workspace. The browser sends that workspace to the API for shared analysis; the API does not save private uploads or overwrite the bundled dataset. Visitors should export their work before closing or reloading.

Hosted requests are capped at 3.5 MB; CSV imports at 2.5 MB and 5,000 post rows. The complete serialized workspace must fit the request cap. The web backend is stateless and does not rely on a local database surviving a server restart.

Fresh collection requires a visitor-supplied YouTube Data API key. It passes through the app to Google's official endpoint and is not saved. The backend never automatically exposes an owner's environment key to anonymous visitors. A temporary directory contains acquisition receipts during collection and is removed afterward; download the resulting evidence. Collection uses the visitor's API quota and may hit the function time limit or provider quota. The saved pilot remains available if collection fails.

## Verify after deployment

1. `/api/health` returns `application=content-detective` and `version=youtube-dashboard-v1`.
2. The unfiltered Overview shows **30 videos**, **279 sampled comments**, **3 brands**, and **100% measure coverage**.
3. Filter to Jazz: the workspace shows **10 videos** and **31 sampled comments**.
4. Open all five sections; search a source video and a sampled comment.
5. Download the evidence ZIP and verify it contains the active filters and only the selected posts' linked comments.

The root API and frontend are tested locally. A successful local build does not confirm a production deployment; verify Vercel's deployment result and the live URL.

## Optional Streamlit hosting

If a Streamlit URL is desired separately, Community Cloud can still deploy root `app.py` on branch `main` with root `requirements.txt`. This is an alternative presentation of the assignment, not required for the Vercel deployment.

Official Vercel references: [Services](https://vercel.com/docs/services) · [configuration](https://vercel.com/docs/services/config-reference) · [Python runtime](https://vercel.com/docs/functions/runtimes/python).
