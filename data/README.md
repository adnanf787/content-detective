# Data status

Real official-API pilot acquired October 18, 2026: **30 YouTube videos (10 each Jazz/Zong/Ufone), 279 sampled public top-level comments, zero API errors, export validation passed**. Corporate account verification lives in config/brands.yml and config/brand_verification.json. The common publication window is October 2025–September 2026, extended with user approval after the original six-month pilot yielded only seven Zong videos.

- `processed/youtube_posts.csv` and `processed/youtube_comments.csv`: validated real exports, with missing measurements kept blank.
- `processed/normalized_posts.csv`: current normalized YouTube observations; no Instagram data is implied.
- `processed/youtube_collection_report.json`: actual counts, missingness, errors, sampling, and cache audit.
- `raw/<run_id>/`: source JSON, snapshot selection, run CSVs, summary, and invocation logs.
- `detective.sqlite`: persistent identities, observations, comments, and collection runs.

Three validated public-pilot files are included in Git so the hosted dashboard can load the same real analysis without making API requests: `processed/youtube_posts.csv`, `processed/youtube_comments.csv`, and `processed/youtube_collection_report.json`. The comment export contains sampled public text and IDs, without author profile fields. Raw snapshots, the local database, and all other processed outputs remain Git-ignored. Transfer raw receipts separately when a full acquisition audit is needed; the exported lineage paths identify those local receipts but do not bundle them in the hosted app. The files below are a separate synthetic demonstration and collection template. No synthetic row is mixed into the real pilot. See docs/YOUTUBE_COLLECTION_LOG.md.

Use the dashboard's **Collect real data** page to stage exact public observations across platforms or optionally retrieve YouTube metadata with your own API key. Download both the CSV and source receipts, then activate and review labels. Collection is session-scoped. Repeated staged IDs keep the latest snapshot. Platform tags are preserved separately from caption hashtags. **Pakistan content lab** uses the new `caption_language`, `creative_angle`, and `local_context` fields; these are reviewed content labels, not viewer demographics.

- `sample_synthetic_posts.csv`: 180 invented observations, generated with Python random seed 42; invented accounts Demo Loom, Demo Kitchen, Demo Cart. All rows have `source_type=synthetic`, `is_synthetic=true`. Missing shares intentionally exercise partial coverage. No audience demographics are generated.
- `demo_manifest.json`: machine-readable fixture provenance.
- `collection_template.csv`: header-only canonical template for authorized real observations. Blank fields mean unknown, not zero. The uploader rejects a template with no records.

See `docs/DATA_DICTIONARY.md` for fields. Use UTF-8 CSV, preserve Urdu and emojis, and use ISO timestamps with known timezone offsets. Record original public post URLs, measurement dates, collection method, and source permissions. A post URL is provenance, not permission to bypass a platform restriction.

For real data, keep an accompanying manifest documenting file name, publisher, collection method/date, geographic relevance, permission/license, timezone, whether synthetic, and any audience evidence. The app captures this at import and exports it with the evidence bundle. It also records the original file's SHA-256 digest.

Store private working files in `data/private/` (Git ignored). Do not join unrelated sentiment datasets to engagement posts. Do not store commenter identities.
