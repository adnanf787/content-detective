# Codex Implementation Brief — Pakistani Social Media Content Detective

**Project type:** university data science assignment + usable research dashboard  
**Prepared:** October 18, 2026  
**Platforms:** YouTube + Instagram  
**Implementation language:** Python 3.11+  
**Preferred user interface:** Streamlit  
**Storage:** raw JSON + curated CSV + SQLite  
**Status:** implementation brief. Do not claim any dataset has been collected before executing and auditing the collectors.

## 0. Role and working agreement

You are Codex, the project's lead engineer and data scientist. Build a genuine, runnable application instead of a synthetic mockup. Ask the student targeted questions when a blocker genuinely requires a credential, a brand-account verification, or a research decision. Do not block on choices you can resolve with sensible defaults. Never fabricate API results, numeric metrics, user demographics, engagement values, comments, or model evaluation scores.

Build in **working, independently testable milestones**. First prove that each platform's acquisition approach works on 5–10 real posts. Do not build an elaborate dashboard around unverified Instagram access. Keep secrets in `.env`, excluded from version control, and provide `.env.example` with placeholders only.

## 1. Business story and research questions

The user is a junior digital-marketing data scientist helping Pakistani brands answer: **"What type of social media content gets Pakistani audiences to engage?"**

Answer these questions with evidence and transparent limitations:

1. How does measurable engagement compare between YouTube and Instagram for the same brands?
2. Which observed content formats, campaign types, topics, and hashtags are associated with higher engagement?
3. What language, caption style, sentiment, posting day, and posting hour are associated with the observed results?
4. Which *observable content-interest/language segments* appear responsive? **Never claim verified viewer age, gender, city, or nationality from public API data.**
5. What should a Pakistani brand post next, supported by cited post examples and analysis?

The label **Pakistan-relevant brands/posts** is a sampling proxy; it is **not** evidence that every viewer is Pakistani.

## 2. Initial sampling design

- Initial industry: Pakistan telecom; research targets: **Jazz, Zong, Ufone**.
- Manually verify each official YouTube channel ID and Instagram handle, recording the verification URL and status in `config/brands.yml`.
- Preferred research posting window: **2026-04-01 through 2026-09-30 inclusive (Asia/Karachi for display)**.
- Target **50 YouTube posts + 50 Instagram posts per brand = up to 300 total** when sources genuinely support that count. This is a **target, not a promise**.
- If content or Instagram access is insufficient, do not pad the dataset. Report actual counts and reason for shortfall; propose extending the window to 12 months, or reducing the target evenly, only after explaining the effect on comparability.
- Prefer a census of all eligible posts in the interval if the number is manageable; otherwise use an explicitly documented, reproducible stratified sample (brand, platform, month, content format). Avoid selecting only viral posts.
- Create a timestamped acquisition snapshot so posts of different ages can be evaluated consistently. Where feasible, require posts to be at least 7 days old before comparing engagement. Preserve age-at-snapshot; one snapshot cannot establish causal best posting times.

## 3. YouTube collector — official Data API v3

**Authentication:** `YOUTUBE_API_KEY` stored in `.env`, restricted to YouTube Data API where feasible.

Implementation:

1. Validate verified official channel IDs. `channels.list(part=contentDetails,statistics,snippet)` supplies each channel's uploads playlist ID and follower/subscriber snapshot if public.
2. Use `playlistItems.list` to enumerate uploads rather than repeated search. Handle pagination and stop/skip according to the study time window. Do not assume a search result proves official affiliation.
3. Call `videos.list(part=snippet,statistics,contentDetails)` for batches of video IDs (up to 50) to collect `title`, `description`, `publishedAt`, `duration`, `tags` when available, `viewCount`, `likeCount`, `commentCount` and canonical URL. Retain NULL when absent.
4. Collect top-level public comments via `commentThreads.list` for a documented and consistent sampling rule (e.g., first 30 most recent per eligible video or all up to an agreed cap); save individual comment IDs, language/text, timestamps, and video linkage. Record comments-disabled/unavailable states. Replies require separate handling if used; do not equate total comment count with downloaded comment sample count.
5. Store responses in timestamped raw JSON before normalization; implement backoff/retry for transient failures, pagination, API quota tracking, deduplication and resumability.
6. Classify `short`, `long_video`, `live`, or `unknown` only with defensible metadata; YouTube Shorts identification from duration alone is not a guaranteed official classification. Document the heuristic, including changes to Shorts maximum lengths.
7. Where subscriber counts are hidden, do not create subscriber-normalized engagement figures.

**Current quota caveat (verified October 2026):** Google documentation identifies separate `search.list` daily quotas and a shared daily quota for other methods. Do not use stale blog assumptions about search costs; inspect actual Console limits for this project. Prefer upload-playlist enumeration for known channels.

Official resources:
- https://developers.google.com/youtube/data/reference/rest/v3/playlistItems/list
- https://developers.google.com/youtube/v3/docs/videos/list
- https://developers.google.com/youtube/v3/docs/commentThreads/list
- https://developers.google.com/youtube/v3/getting-started

## 4. Instagram collector — gated official access

**Critical:** A YouTube API key alone cannot access Instagram data.

**First attempt: Meta Instagram API with Facebook Login and Business Discovery**, the supported approach for examining other eligible Instagram professional accounts where permissions permit. A Meta app and an authenticated **Instagram Business/Professional account linked to a Facebook Page** are typically needed for this login flow; use current Meta documentation to determine exact permissions, app review requirements, access mode, and any fields that are allowed. Do not assume the user's personal Instagram login, or an Instagram-Login-only integration, provides Business Discovery.

Phase A: implement an Instagram capability probe before collecting a large dataset:

1. Obtain `META_APP_ID`, any necessary `META_APP_SECRET`, the authorized token, linked-page/Instagram account identification, and approved scopes by the **official Meta OAuth setup**. Do not ask for the user's Instagram password or embed secrets in scripts or chat.
2. Make a single documented Business Discovery request against one verified competitor professional-account handle, asking only for minimally necessary public profile/media fields supported by the API/version.
3. Inspect real responses for: `id`, `username`, `followers_count`, `media`, `caption`, `media_type`, `media_product_type`, `timestamp`, `permalink`, `like_count`, `comments_count` and format-related fields **only if actually returned/allowed**. The field list is conditional, not a guaranteed contract.
4. Test pagination and limits on recent media. Store what was supported, denied, or missing. For each account, determine whether any returned media falls inside the common sampling window.
5. Never assert public availability of comment **text**, reach, impressions, shares, saves, demographics, or competitor account insights. These often require ownership or account-specific authorization; collect them only when genuinely authorized and available.
6. Apply rate limiting, token expiry handling, redaction of tokens in logs, secure storage, and resumable retrieval.

**Phase B, if Meta access fails:** preserve Instagram in the assignment via **documented, manual collection of publicly visible metrics** into a strict CSV import template. Design a Streamlit import/upload panel and data validator so that the student can record URLs, verified handle, caption, date/time, media format, visible like count, visible comment count, snapshot time, and a `source_method=manual_public` marker. Allow blank data; do not assume like counts are visible. Do not use login circumvention, private endpoints, stealth scraping, or fake engagement data. Manual records should include source URLs and an audit trail.

The Instagram path must gracefully handle `unavailable`, `restricted`, `manual_only`, and `official_api` states without breaking the whole app.

Resources:
- https://developers.facebook.com/documentation/instagram-platform/instagram-api-with-facebook-login/business-discovery
- https://www.postman.com/meta/instagram/folder/u4g5a2a/instagram-api-with-facebook-login

## 5. Harmonized schema and lineage

Create normalized SQLite tables with CSV exports and suitable unique constraints:

### `brands`
- `brand_id`, `brand_name`, `industry`, `country_relevance_note`

### `accounts`
- `account_id`, `brand_id`, `platform`, `handle`, `platform_account_id`, `verified_official`, `verification_url`, `followers_at_snapshot`, `followers_snapshot_at`

### `posts`
- `post_id` (internal), `platform`, `platform_post_id`, `account_id`, `post_url`, `published_at_utc`, `published_at_pakistan`, `caption_or_title`, `description`, `hashtags_json`, `language_inferred`, `native_media_type`, `normalized_content_category`, `duration_seconds`, `campaign_topic`, `sentiment_of_post_text`, `collected_at_utc`, `source_method`, `raw_record_path`, `access_status`

### `post_metric_snapshots`
- `platform_post_id`, `platform`, `measured_at_utc`, `views` (nullable), `likes` (nullable), `comments_count` (nullable), `shares` (nullable), `saves` (nullable), `followers_at_snapshot` (nullable), `metric_source`

### `comments`
- `comment_id`, `platform`, `platform_post_id`, `comment_text`, `published_at_utc`, `language_inferred`, `sentiment_label`, `sentiment_confidence`, `collection_method` and `collected_at_utc`. Avoid exporting account handles and personally identifying author details unless strictly necessary for analysis; anonymize or omit.

### `collection_runs`
- `run_id`, `platform`, `started_at_utc`, `ended_at_utc`, `status`, `posts_requested`, `posts_collected`, `fields_missing_json`, `api_errors_redacted`, `sampling_method`, `notes`

Preserve missing metrics as SQL NULL/Pandas NA rather than zeros. Record timezone conversion correctly; the same timestamp must not be interpreted as both UTC and Pakistani local time.

## 6. Data quality and comparisons

- Validate uniqueness `(platform, platform_post_id)` and valid URLs, dates, counts >= 0, valid account mappings, and chronological plausibility.
- Mark Instagram manually collected values and available API values separately. Add transparent per-platform/brand coverage tables and missingness summaries.
- Use **like + comment count** as *observed public interactions*, not full-platform engagement (shares, saves, watch time may be missing).
- Compare **posts within the same platform** first: median interactions per post, content-format differences, and age-adjusted or comparable-age subsets. Report sample counts.
- For tentative cross-platform comparisons, use within-brand/per-platform distributions or `(likes + comments)/followers_at_snapshot * 100` **only where follower counts are observed**. Label as a *public-interaction-to-audience-size proxy*, not a true reach-based engagement rate; platforms have different viewing and metric definitions.
- Views: YouTube views and Instagram Reel plays/views are not necessarily defined equivalently. Do not directly rank platforms by these raw numbers.
- Report confidence intervals or uncertainty where useful. Correlation != causation, and observational posting-time effects are confounded by campaigns and audience size.
- If a platform's field is unavailable, show **N/A**. No ungrounded winner labels.

## 7. NLP and research analysis

- Language detection for English, Urdu script, and Roman Urdu, with an `unknown`/mixed bucket and a spot-check evaluation.
- Extract hashtags and frequently occurring terms; normalize spelling and transliterations carefully.
- Categorize content: promotional, educational, product/service update, entertainment/humor, customer support, seasonal/cultural, other/uncertain. Begin with transparent rules and optionally train a classifier using a small labeled dataset.
- Sentiment of **user comments** is separate from tone/sentiment of **brand caption text**. Never call caption sentiment a measurement of audience sentiment.
- Train/choose a model that addresses multilingual content and Roman Urdu. Evaluate against manually labeled, stratified samples. Show evaluation metrics, including macro-F1/confusion matrix, and document small-sample limits.
- Where Instagram comment text isn't accessible, show `Instagram comment sentiment: unavailable` rather than assigning it fake labels. Instagram caption tone and YouTube comment sentiment may still be analyzed, but **not compared as equivalent variables**.
- Analyze posting day/hour in `Asia/Karachi`, content types, topic groups, sentiment, and hashtags with sample sizes and context.
- Optional recommendation engine can be rules/analytics-first; use an LLM only if a separate provider key is available and user authorizes it. Avoid incurring hidden costs.

## 8. Interactive Streamlit interface

Build pages or tabs:

1. **Overview** — counts, date coverage, brands, platform split, collection status and data-source quality indicators.
2. **Data Collection** — verify accounts, test credentials, run/refresh collectors, progress/error log with secrets redacted, import/validate Instagram CSV.
3. **Compare Platforms** — transparent metrics and missing data; brand filters and content category controls; avoid invalid apples-to-oranges graphs.
4. **Content Intelligence** — topic/hashtag ranks, content formats, language distribution, day/hour heatmaps, supporting post links.
5. **Sentiment Lab** — independently labeled caption sentiment vs downloaded comment sentiment; evaluation, limitations, examples with privacy protections.
6. **Recommendations** — suggested platform + format + topic + posting window, with sample size, supporting examples, caveats and uncertainty.
7. **Methods & Export** — full methodology, sampling and collection dates, dictionaries, CSV download, known restrictions and research caveats.

Do not show invented charts. If fewer records exist than a useful threshold, surface an honest 'insufficient data' explanation instead.

## 9. Tech stack and project structure

Suggested packages: `requests` or official Google client library, `pandas`, `numpy`, `sqlalchemy`, `streamlit`, `plotly`, `scikit-learn`, `python-dotenv`, `pydantic`, `pytest`. NLP packages are optional and must be documented. Pin reproducible package versions in requirements/lockfile.

Suggested layout:

```
pakistan-social-media-detective/
  .env.example
  .gitignore
  README.md
  requirements.txt
  config/brands.yml
  src/collectors/youtube.py
  src/collectors/instagram_business_discovery.py
  src/collectors/instagram_csv_import.py
  src/storage/schema.py
  src/etl/normalize.py
  src/analysis/engagement.py
  src/analysis/topics.py
  src/analysis/sentiment.py
  src/analysis/recommendations.py
  app.py
  tests/
  data/raw/.gitkeep
  data/processed/.gitkeep
  docs/data_dictionary.md
  docs/methodology.md
  docs/limitations.md
  docs/collection_log.md
```

`.env.example`:

```
YOUTUBE_API_KEY=
META_APP_ID=
META_APP_SECRET=
META_ACCESS_TOKEN=
META_IG_USER_ID=
META_GRAPH_API_VERSION=
```

Never commit `.env`, raw access tokens, or private credentials. Handle Meta OAuth/refresh as appropriate for the current official flow rather than assuming a permanent token.

## 10. Build phases and acceptance gates

**Milestone 0: feasible sample/credential audit**  
Deliver verified brand account handles/IDs, source access matrix, app configuration instructions, and a decision on Instagram official access vs CSV fallback.

**Milestone 1: YouTube extraction**  
With a supplied valid key, retrieve **10 real videos** and associated available metadata and comments; save raw plus normalized data; demonstrate repeat runs do not duplicate records.

**Milestone 2: Instagram proof of access**  
Either retrieve **5–10 real professional-account posts** via a properly authorized Business Discovery call and print actual returned fields, **or** prove the manual CSV validator/import on 5–10 manually verified real rows. Document permissions and failure reasons. Do not suggest the other brand's account credentials are necessary or accessible.

**Milestone 3: full collection and ETL**  
Collect eligible samples within scope; preserve lineage, missingness, snapshot times, and collection logs. Print truthful final counts by platform and brand.

**Milestone 4: analytics and evaluation**  
Produce reproducible Python functions/tests and exploratory notebook/report; evaluate a multilingual sentiment baseline on manually labeled samples; describe known measurement limitations.

**Milestone 5: dashboard, recommendation engine and academic submission**  
Make the Streamlit app easy to launch and include README, setup guide, sample data templates, methodology, schema, limitations, tests, evidence-backed screenshots if genuinely generated, and report-ready plots.

## 11. Questions Codex may ask the student

Ask these only when they are unresolved and needed:

1. Can the student supply a **YouTube API key via their local `.env`**?
2. Can they create a Meta developer app, and do they **own/control an Instagram Professional account linked to a Facebook Page** for the Facebook Login Business Discovery flow? If not, use a manual Instagram CSV pathway; do not demand credentials for competitors' accounts.
3. Are Jazz, Zong, and Ufone acceptable target brands, and have their channel handles been verified?
4. Does the lecturer require a particular minimum sample size or a date interval?
5. May the tool analyze **public comments** (YouTube) using privacy-minimizing, documented procedures?

## 12. Final success definition

The deliverable is not just pretty charts. The student must be able to demonstrate: **how actual public data was sourced, cleaned, normalized, evaluated, visualized, and used to reach defendable marketing recommendations**, while candidly explaining which Instagram and demographic questions the available data cannot answer.
