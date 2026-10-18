# Canonical data dictionary

All fields can be absent; the app reports which questions become unsupported. Blank measurements remain missing. All count fields must be finite non-negative integers. Unknown counts must not be written as zero.

| Field | Type / purpose |
|---|---|
| post_id | Source-unique string; combined with source_name, platform, brand for duplicate checks. Missing values receive flagged local row IDs. |
| source_url | Original public post URL, if allowed and available. |
| source_name | Publisher, authorized export, or official account. Missing values inherit declared manifest source. |
| source_type | official_export, manual_public_post, third_party, synthetic, unverified, or documented source type. |
| is_synthetic | true/false; blank is unverified unless import status is explicitly declared. Synthetic row/source/import flags take priority. |
| brand | Account/brand identifier, not an audience demographic. |
| platform | Instagram, TikTok, Facebook, YouTube, etc.; explicit aliases are normalized. |
| post_datetime | Conservative ISO YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS with optional timezone offset. |
| timezone_source | IANA timezone (Asia/Karachi, UTC, etc.) when known; unknown otherwise. Explicit timestamp offsets take priority. |
| content_type | reel, image, carousel, video, short-form video, text, promotional, etc. |
| caption | Original Unicode caption text. Whitespace is normalized in working text; original text is preserved in caption_original. |
| hashtags | Optional supplied hashtags with #; combined with caption extraction and deduplicated per post. |
| topic | Optional documented content theme; not inferred audience identity. |
| caption_language | Reviewed Urdu, Roman Urdu, English, Mixed, or Other. Caption language is not viewer identity. |
| creative_angle | Reviewed tutorial, humour, storytelling, product demo, offer, question, or Other. Separate from the media format. |
| local_context | Reviewed Everyday, Eid, Ramadan, PSL/cricket, wedding season, national occasion, or Other. Must be supported by the actual content. |
| likes | Observed like count. |
| comments | Observed comment count; not comment text or sentiment. |
| shares | Observed share count. |
| views | Observed views; repeated views may differ from unique exposure. |
| impressions | Observed impressions, with platform-specific definition. |
| reach | Observed reach, with platform-specific definition. |
| follower_count | Account follower count; document when measured. |
| audience_location | Only genuinely sourced audience geography. Explicit Pakistan is required for Pakistani segment context. |
| audience_segment | Only independently sourced segment. Post-level context is insufficient for segment-specific response rates. |
| caption_sentiment | Optional positive/neutral/negative supplied label. Document method in manifest notes. |
| collection_datetime | ISO date/time when metrics were observed; document consistent observation windows. |

## Derived fields

`data_status`: synthetic, real (declared), or unverified. `is_synthetic` is nullable.

`*_original`: original metric values, preserved for validation review. `caption_original`: original untrimmed caption. `id_generated`, `duplicate_conflict`, `analysis_eligible`: quality flags.

`parsed_datetime`, `local_datetime`, `time_status`, `weekday`, `hour`, `source_date`: transparent date interpretation. Local comparisons require timezone evidence. Source calendar dates are used for the date filter, including unknown-zone dates with qualification.

`available_interactions`, `observed_components`, `complete_interactions`, `visible_interactions`, `rate_impressions`, `rate_reach`, `rate_views`, `rate_followers`: definitions in METHODOLOGY.md and the dashboard.

`sentiment_label`, `sentiment_method`: supplied-label or tiny English baseline result/source; uncertain text is unassessed.

`visible_per_1000_views`: 1,000 × (likes + comments) / positive views, requiring both counts. Shares are excluded. It is not a percentage of unique people and does not measure retention.

YouTube collection also preserves `title`, `description`, `channel_id`, `platform_tags` (JSON array, separate from hashtags), `platform_category_id`, and `duration_iso`. Category IDs are not human topic labels. The API collector labels the media generically as video; duration alone does not establish a Short. Unknown shares, exposure, followers, and audience fields stay blank.

## Import manifest

file_name, source_name, source_type, status, collected_on, geographic_relevance, license_notes, source_timezone, audience_evidence, notes, sha256. It describes provenance rather than verifying truth independently. Row-level synthetic declarations cannot be erased by declaring an import real.

## Official YouTube pilot lineage and comments

`platform_post_id` retains the YouTube video ID; `post_id` is its canonical compatibility field. `brand_id`, `account_id`, `post_url`, `published_at_utc`, `published_at_pakistan`, `native_media_type`, `duration_seconds`, `source_method`, `raw_record_path`, `collection_run_id`, and `access_status` preserve normalization/lineage. `normalized_content_category` identifies live video only with explicit live metadata; otherwise it is unknown, without assuming a Short from duration.

`followers_at_snapshot`, `followers_snapshot_at`, and `follower_count_is_rounded` qualify subscriber measurements. `visible_rate_followers` is 100 × (likes + comments) / positive observed followers, a public-interaction-to-audience-size proxy rather than a reach rate. `age_days_at_snapshot` requires known publication and observation offsets; it is missing for unknown timezones or negative ages.

`language_inferred`, `language_method`, `category_suggested`, `category_evidence`, and `category_method` are unevaluated rule suggestions, separate from reviewed `caption_language` and `topic`. They do not imply viewer language or demographics.

`comment_sample_status` records available, no-public-comments-returned, disabled, unavailable, or incomplete-page-limit states; `downloaded_comment_count` is the actual sample count. Neither replaces the video's observed total `comments` metric.

`youtube_comments.csv` has comment ID, platform/video linkage, brand, text, publication/update/observation timestamps, method, raw lineage, run ID, suggested language, sentiment label/method, and nullable confidence. No author-profile fields or replies are requested. Sentiment confidence is NULL; unassessed labels are not neutral. Human-review sheets supply `human_label` separately and are joined by comment ID for evaluation.

SQLite tables: brands, accounts, posts, post_metric_snapshots, comments, collection_runs. Identity keys and distinct measurement times enforce idempotent snapshot replay. See src/study_storage.py for exact columns and constraints.
