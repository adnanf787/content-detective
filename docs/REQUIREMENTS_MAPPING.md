# Assignment questions mapped to implementation

Current data milestone: 30 official-API YouTube videos and 279 sampled top-level comments from verified Jazz/Zong/Ufone channels. The UI adds real-pilot collection, source coverage and post-age filtering, Content intelligence rule suggestions, a separate linked Comment sentiment page with abstention/review evaluation, and source post examples in recommendation evidence. The real notebook is notebooks/youtube_pilot_analysis.ipynb. One observed platform and missing audience data leave corresponding questions unsupported. Instagram has a fixture-tested manual CSV fallback; no real Instagram/API access is claimed. See YOUTUBE_COLLECTION_LOG.md for actual availability.

| Exact assignment question | Dashboard / computation | Honest unsupported state |
|---|---|---|
| Which platform performs better? | Platforms & formats: group mean, median, n, coverage, distribution, source-date range. Metric definition/selection. | Fewer than two measured platforms cannot establish a comparison; raw counts need qualification. |
| Which content type gets more engagement? | Content formats with shared metric, mean/median/n, outlier boxplot. | Missing formats or sparse observations trigger insufficient evidence. |
| What topics and hashtags are popular? | Unicode hashtag frequencies, engagement associations, supplied topic groups. | No captions/tags/topics means unavailable. Observed usage is explicitly not audience popularity. |
| What sentiment is associated with engagement? | Caption sentiment distribution, per-label engagement, supplied-label sources and abstaining baseline. | No assessable captions/labels means unavailable. Audience-comment sentiment remains unavailable without linked comments. |
| What posting time/day appears better? | Karachi weekday/hour groups and timestamp status counts. | Unknown timezone excluded; date-only rows have no posting hour; small slots flagged. |
| Which Pakistani audience segment seems more responsive? | Audience evidence screen; source-evidenced, declared-real Pakistan segment context only. | Demo has insufficient audience-demographic data. Segment-specific rates require appropriate grain and denominators. |
| What should a Pakistani brand post next? | Offline studio: format, themes, hashtags, timing, experiment, success metric; evidence and limitations on every card. | Insufficient comparison data yields collection suggestions, never invented winners. |

All seven appear in Overview support indicators and the export executive summary. Shared functions reside in src/ and are reused by notebooks/assignment_analysis.ipynb.

## Practical deliverables

CSV importer with reviewable mapping; quality and provenance; filters; charts; deterministic recommendations; Markdown/CSV/ZIP exports; reproducible notebook; generated demo and collection template; analytical and UI tests; setup and screenshot guidance.

The corrected assignment workflow also includes a project story/study design, manual public observations across platforms, optional bounded YouTube API collection from links/search, downloadable source receipts, a reviewed-label editor, and Pakistan Content Lab comparisons for caption language, creative approach, and local context. These comparisons also appear in report tables and, with adequate evidence, recommendation cards. Recommendation studio exports an optional AI writing prompt with computed evidence; it does not invoke a model. The main deliverable is the Python dashboard. The earlier web video/fact-checking experiment is preserved separately.
