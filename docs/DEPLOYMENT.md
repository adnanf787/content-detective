# Deploy the current YouTube dashboard

The current application is Streamlit. `app.py` loads `src/dashboard.py` and `assets/dashboard.css`. The separate `web/` directory is the earlier ReelScope Next.js app, deployed on Vercel. Rebuilding that project does not publish the Streamlit dashboard.

## Streamlit Community Cloud

1. Open https://share.streamlit.io/ and sign in with the GitHub account that can access `adnanf787/content-detective`. Complete any account terms or repository-access prompts yourself.
2. Choose **Create app**, then deploy from GitHub.
3. Set repository to **adnanf787/content-detective**, branch to **main**, and main file path to **app.py**. Do not select `web/`.
4. In advanced settings, select **Python 3.12**. The repository root's `requirements.txt` is used automatically.
5. Deploy and wait for the app to start. The deployed URL will be a Streamlit app URL, separate from the existing Vercel address.

No secrets are needed to view or analyze the included snapshot. Fresh YouTube collection is optional; if enabled, add `YOUTUBE_API_KEY` through the app's private Streamlit secrets settings. Never commit `.env` or a secrets file. Files written during cloud collection are not durable storage; download results before restarting the app.

## Included data

Git includes only these three processed files:

- `data/processed/youtube_posts.csv`: 30 public videos, ten per verified brand.
- `data/processed/youtube_comments.csv`: 279 sampled public comments, without commenter profile fields.
- `data/processed/youtube_collection_report.json`: snapshot timestamps, validation, counts, and limitations.

The snapshot was observed on October 18, 2026. It is saved research data, not continuously refreshed measurements. The app validates the CSVs and loads them automatically. Raw-response lineage paths refer to local acquisition receipts, which are not bundled. Credentials, raw responses, the SQLite database, and generated analysis outputs remain excluded from Git.

## Check after deployment

- The browser title identifies **PakTelco Analytical Observational Workbench · Content Detective**.
- The navigation has **Overview**, **Content**, **Comments**, **Recommendations**, and **Data & methods**.
- The unfiltered overview shows **30 videos**, **279 sampled comments**, and **3 brands**.
- Open all five sections, try a brand filter, and use **Export research** to download the filtered evidence.

Later pushes to `main` update the Streamlit app connected to that branch. Keep Vercel only if the earlier ReelScope app is still useful; its address continues to serve that separate application.

Official instructions: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
