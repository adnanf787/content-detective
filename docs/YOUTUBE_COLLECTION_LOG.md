# YouTube collection log — October 18, 2026

Latest complete snapshot: `20261018T070121103737Z`. **30 real videos, 279 sampled public top-level comments, 0 API errors, on-disk CSV validation passed.**

## Verified brand accounts and counts

| Brand | Videos | Downloaded comments | Actual publication dates (Asia/Karachi) |
|---|---:|---:|---|
| Jazz | 10 | 31 | 2026-09-01 to 2026-09-30 |
| Ufone | 10 | 108 | 2026-05-01 to 2026-08-29 |
| Zong | 10 | 140 | 2026-03-24 to 2026-09-21 |

Account IDs, exact corporate-site links, verification dates, and API resolution evidence are recorded in `config/brands.yml` and `config/brand_verification.json`. Verification uses corporate hyperlinks and official `channels.list`, not a search-name match.

## Sampling and approved window change

Newest 10 eligible uploads per verified brand in 2025-10-01–2026-09-30 Asia/Karachi; minimum age 7 days; up to 30 newest top-level comments/video; no replies.

The April–September 2026 pilot returned 27 videos: Jazz 10, Zong 7, Ufone 10, with 238 sampled comments and zero API errors. The user explicitly approved extending the common eligibility window to October 2025–September 2026. The expanded pilot reached 10 per brand. No records were padded or fabricated. Earlier raw responses are retained. Selecting the newest ten still yields different date/age ranges across brands; age differences are visible and filterable. This is a convenience pilot, not a representative Pakistan-wide study.

## Metric availability

| Field | Observed posts | Missing posts |
|---|---:|---:|
| views | 30 | 0 |
| likes | 30 | 0 |
| comments | 30 | 0 |
| follower_count | 30 | 0 |
| shares | 0 | 30 |
| saves | 0 | 30 |
| reach | 0 | 30 |
| impressions | 0 | 30 |
| audience_location | 0 | 30 |
| audience_segment | 0 | 30 |

All unknown counts are blank/SQL NULL, not zero. Subscriber counts are rounded channel snapshots and are not the number of viewers reached.

## Public comments and NLP

Per-video comment access states: `{"no_public_comments_returned": 3, "sample_available": 27}`. Top-level sample size is separate from the video comment-count metric; replies are not collected. The API request restricts returned fields to omit author profiles/handles. Raw text can still contain self-disclosed details.

Exploratory sentiment cue labels: `{"negative": 9, "positive": 14, "unassessed": 256}`. These use a small English/Urdu/Roman Urdu lexicon with abstention, not a trained or evaluated multilingual model. Only 23 of 279 comments have cue labels. No human gold labels, model accuracy, macro-F1, or calibrated confidence are available. The dashboard and review-sheet export support actual human-label evaluation. Caption tone is analyzed separately.

## Repeatability, storage, and errors

The cache-resume check used **0 new network calls and 115 cached responses**. Original response observation times were retained. SQLite stores separate metric snapshots rather than replacing all observation history.

Current SQLite counts: `{"accounts": 3, "brands": 3, "collection_runs": 2, "comments": 279, "post_metric_snapshots": 57, "posts": 30}`. Metric snapshots retain separate observation times from different collection runs; these are legitimate separate measurements. Post/comment identities are unique, the cached resume added no duplicate metric snapshots, and foreign-key checks passed.

API errors for the completed expanded pilot: **none**. Missing count fields and empty comment samples are disclosed above. Transient-retry, quota/key failure, comment-disabled, pagination, missing data, and invalid-input paths also have controlled fixture tests; those tests are distinct from live-service verification.

Raw JSON, per-snapshot CSVs, summaries, and invocation logs are under `data/raw/<run_id>/`. Current CSVs/report/validation are under `data/processed/`, and the database is `data/detective.sqlite`. These data paths and `.env` are Git-ignored. The local key has owner-only permissions and is excluded from exports and source.

## Scope remaining

Instagram API work is deferred per the user. Its offline CSV validator/importer is tested on five controlled fixture rows; **no real Instagram rows or Business Discovery access were tested**. One observed platform cannot establish a cross-platform winner. Manual topic/language/creative/context review, a human sentiment evaluation set, and controlled follow-up marketing experiments remain research work. Public brand data cannot establish viewer nationality, age, gender, city, reach, retention, or causal posting-time effects.
