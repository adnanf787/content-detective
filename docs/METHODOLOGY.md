# Reproducible methodology

## Current YouTube acquisition milestone

The user-approved publication window is October 1, 2025–September 30, 2026 inclusive in Asia/Karachi, converted once to UTC API bounds. Official Jazz/Zong/Ufone channel affiliation is documented through corporate-site links plus `channels.list`. Upload playlists are enumerated with pagination, bounded to 40 pages per channel and explicitly marked if incomplete. Actual video publication timestamps are checked again before choosing the newest 10 eligible videos per brand, all at least seven days old at the snapshot. Duration alone does not establish a YouTube Short.

`videos.list` supplies available public metrics and metadata. `commentThreads.list(order=time,textFormat=plainText)` supplies up to 30 newest top-level comments per selected video, bounded pagination, without replies or author-profile fields. Raw JSON is persisted before normalization. Disabled, restricted, empty, and partial states are explicit. Recent comment sampling is moderated, capped, and self-selected; total video comment metrics differ from the downloaded sample.

The original six-month run yielded only seven Zong videos, triggering an explicit user-approved common-window expansion rather than padding. Thirty videos and 279 public comments were collected with zero API errors and validated. Separate real source snapshots, CSVs, SQLite measurement history, and a replay cache support audit and resumability. The real-pilot notebook uses the same modules as the dashboard. `docs/YOUTUBE_COLLECTION_LOG.md` records actual counts and coverage.

Automatic caption language and content-category rules produce review candidates, not ground truth. A separate English/Urdu/Roman Urdu comment cue lexicon abstains on unsupported/conflicting/negated text. Its 23 assigned sentiment cues among 279 comments are unevaluated. Confidence is NULL. Human-label upload supports a confusion matrix and macro-F1 only when real review labels are supplied; no score is manufactured. Caption tone remains a distinct variable.

Post-age ranges and a similar-age filter accompany within-platform comparisons. A separate `visible_rate_followers` proxy uses 100 × observed likes-plus-comments / positive observed follower snapshot; subscriber snapshots are rounded. This is not a reach-based rate, and cross-platform definitions still differ. Only one real platform is currently observed; no platform winner or demographic response rate is established.

The generic import/analysis rules below remain applicable. Notes describing the initial manual/search-only collection UI refer to that separate staging route; the verified telecom collector persists research data locally.

1. Read UTF-8 CSV as strings to preserve IDs and text. Suggest explicit aliases; user reviews canonical mapping. No metric is guessed from unrelated fields.
2. Remove exact original duplicate records and report count. Trim working fields, normalize documented platform/format aliases, retain originals. Convert invalid counts to missing and report each field's count. Keep outliers.
3. Flag conflicting source/platform/account/post IDs; retain in cleaned exports and exclude from analysis. Assign marked local row IDs where source IDs are missing.
4. Honor synthetic flags across row, source, and import declaration. Real means user-declared, not independently verified. Dataset labels persist into CSV fields, reports, and filenames.
5. Parse conservative ISO timestamps. Convert explicit/declared known timezones to Asia/Karachi. Unknown-zone rows retain source calendar dates but no local timing groups. Date-only rows have no hour. Bad timestamps are counted.
6. Apply conflict exclusion and user filters. Dataset-level quality remains separate from active-data coverage. Require one data status for dashboard analysis; never pool synthetic and empirical tracks into recommendations.
7. Compute metrics without imputation:
   - Available interactions = observed likes/comments/shares sum with ≥1 observed value. This may include different components across posts and is not a ranking metric.
   - Complete interactions = likes + comments + shares only with 3 valid values.
   - Visible interactions = likes + comments only with 2 valid values.
   - Visible interactions per 1,000 views = 1,000 × (likes + comments) / positive views. Requires both counts, excludes shares, and does not count unique engaged people.
   - Impressions/reach/views/followers rates = 100 × complete interactions / the separately named positive denominator. Nonfinite results are missing.
8. Select the first metric with ≥80% active-post coverage in this order: impressions rate, reach rate, complete per-view rate, complete followers rate, visible interactions per 1,000 views, visible follower proxy, complete interactions, visible interactions, likes, comments, shares. Otherwise choose highest coverage and show partial-data caveat. User can override the metric explicitly. The two follower formulas use different numerators and are labeled separately.
9. Group summaries show total posts, valid metric n, coverage, mean, median, and small-sample flag. Medians are preferred for comparisons; distributions expose outliers. Show platform/format date ranges so users can restrict to a common window.
10. Extract Unicode hashtags from captions/supplied tags, preserving combining marks; casefold and count once per post. Topic groups use supplied annotations only. Hashtag usage is not population popularity.
11. Analyze supplied caption labels separately from an abstaining English lexicon baseline. No comment sentiment is fabricated. No trained NLP accuracy is claimed.
12. For audience context require declared-real rows, explicit Pakistan audience_location, segment field, and provenance note. Even then post-level groups are only partial evidence; true segment response comparisons require segment-specific numerators and exposures.
13. Recommendations require at least two measured groups each with n ≥ configurable threshold (default 5) and coverage ≥80%. Compare highest observed medians and quote means, n/total, date range, dataset status, and exact metric. Ties are disclosed. Otherwise recommend data collection. Timing recommendations require repeated weekday/hour slots with known timezone.
14. Export manifest, filters, quality, seven-question support, tables, evidence, and limitations. The notebook uses these same Python modules.

There is no hypothesis-test confidence interval, causal model, trained predictor, or external AI call. Default n=5 is an exploratory guardrail, not a power calculation or statistical guarantee.

## Collection and Pakistan content lab

The collection workspace records exact manual public observations or fetches official YouTube metadata. API batches are bounded to 200 videos, paginated in at most four search requests and four metadata requests. Explicit links do not need search. Search results are newest-first within the chosen publication range and available in Pakistan; neither selection nor region establishes representative Pakistani audiences. Source receipts preserve responses and selection parameters without credentials. The staging area keeps the latest observation per platform/post ID; it is not a time-series store. Download the CSV and receipts before ending a session.

Review caption language, creative approach, local context, topic, format, and caption tone using a documented codebook. Recalculation uses the same source observations and all existing quality checks. Group comparisons quote coverage and n, with the same recommendation thresholds as other fields. Narrow to one platform/account and a comparable publication window; observed age/spend differences can still confound results. The AI brief is an exported prompt containing computed evidence, not an AI-generated or validated recommendation.
