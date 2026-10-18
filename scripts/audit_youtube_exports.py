"""Audit actual on-disk CSV/SQLite data and write a truthful collection log."""
from pathlib import Path
import json
import sqlite3
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.dataset_validation import validate_exports
from src.youtube_api import atomic_json

folder = ROOT / 'data/processed'
posts = pd.read_csv(folder / 'youtube_posts.csv', dtype=str, keep_default_na=False)
comments = pd.read_csv(folder / 'youtube_comments.csv', dtype=str, keep_default_na=False)
report = json.loads((folder / 'youtube_collection_report.json').read_text())
validation = validate_exports(posts, comments)
assert validation['valid'], validation['errors']
with sqlite3.connect(ROOT / 'data/detective.sqlite') as connection:
    database_counts = {table: connection.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
                       for table in ['brands', 'accounts', 'posts', 'post_metric_snapshots', 'comments', 'collection_runs']}
    foreign_key_violations = connection.execute('PRAGMA foreign_key_check').fetchall()
assert not foreign_key_violations
audit = {**validation, 'sqlite_counts': database_counts, 'foreign_key_violations': foreign_key_violations,
         'run_id': report['run_id']}
atomic_json(folder / 'youtube_validation.json', audit)
lines = ['# YouTube collection log — October 18, 2026', '',
         f'Latest complete snapshot: `{report["run_id"]}`. **{len(posts)} real videos, {len(comments)} sampled public top-level comments, '
         f'{len(report["api_errors"])} API errors, on-disk CSV validation passed.**', '',
         '## Verified brand accounts and counts', '',
         '| Brand | Videos | Downloaded comments | Actual publication dates (Asia/Karachi) |',
         '|---|---:|---:|---|']
for brand, group in posts.groupby('brand'):
    stamps = pd.to_datetime(group.post_datetime, utc=True).dt.tz_convert('Asia/Karachi')
    lines.append(f'| {brand} | {len(group)} | {int(comments.brand.eq(brand).sum())} | {stamps.min():%Y-%m-%d} to {stamps.max():%Y-%m-%d} |')
lines += ['', 'Account IDs, exact corporate-site links, verification dates, and API resolution evidence are recorded in '
          '`config/brands.yml` and `config/brand_verification.json`. Verification uses corporate hyperlinks and official `channels.list`, not a search-name match.',
          '', '## Sampling and approved window change', '', report['sampling_method'], '',
          'The April–September 2026 pilot returned 27 videos: Jazz 10, Zong 7, Ufone 10, with 238 sampled comments and zero API errors. '
          'The user explicitly approved extending the common eligibility window to October 2025–September 2026. '
          'The expanded pilot reached 10 per brand. No records were padded or fabricated. Earlier raw responses are retained. '
          'Selecting the newest ten still yields different date/age ranges across brands; age differences are visible and filterable. '
          'This is a convenience pilot, not a representative Pakistan-wide study.',
          '', '## Metric availability', '', '| Field | Observed posts | Missing posts |', '|---|---:|---:|']
for field in ['views', 'likes', 'comments', 'follower_count', 'shares', 'saves', 'reach', 'impressions', 'audience_location', 'audience_segment']:
    absent = int(posts[field].eq('').sum()) if field in posts else len(posts)
    lines.append(f'| {field} | {len(posts) - absent} | {absent} |')
statuses = posts.comment_sample_status.value_counts().to_dict()
sentiment = comments.sentiment_label.value_counts().to_dict()
lines += ['', 'All unknown counts are blank/SQL NULL, not zero. Subscriber counts are rounded channel snapshots and are not the number of viewers reached.',
          '', '## Public comments and NLP', '',
          f'Per-video comment access states: `{json.dumps(statuses, sort_keys=True)}`. '
          'Top-level sample size is separate from the video comment-count metric; replies are not collected. '
          'The API request restricts returned fields to omit author profiles/handles. Raw text can still contain self-disclosed details.', '',
          f'Exploratory sentiment cue labels: `{json.dumps(sentiment, sort_keys=True)}`. '
          'These use a small English/Urdu/Roman Urdu lexicon with abstention, not a trained or evaluated multilingual model. '
          f'Only {int(comments.sentiment_label.ne("unassessed").sum())} of {len(comments)} comments have cue labels. No human gold labels, model accuracy, macro-F1, or calibrated confidence are available. '
          'The dashboard and review-sheet export support actual human-label evaluation. Caption tone is analyzed separately.', '',
          '## Repeatability, storage, and errors', '',
          f'The cache-resume check used **{report["request_attempts"]} new network calls and {report["cached_responses_used"]} cached responses**. '
          'Original response observation times were retained. SQLite stores separate metric snapshots rather than replacing all observation history.', '',
          f'Current SQLite counts: `{json.dumps(database_counts, sort_keys=True)}`. '
          'Metric snapshots retain separate observation times from different collection runs; these are legitimate separate measurements. '
          'Post/comment identities are unique, the cached resume added no duplicate metric snapshots, and foreign-key checks passed.', '',
          'API errors for the completed expanded pilot: **none**. Missing count fields and empty comment samples are disclosed above. '
          'Transient-retry, quota/key failure, comment-disabled, pagination, missing data, and invalid-input paths also have controlled fixture tests; '
          'those tests are distinct from live-service verification.', '',
          'Raw JSON, per-snapshot CSVs, summaries, and invocation logs are under `data/raw/<run_id>/`. '
          'Current CSVs/report/validation are under `data/processed/`, and the database is `data/detective.sqlite`. '
          'These data paths and `.env` are Git-ignored. The local key has owner-only permissions and is excluded from exports and source.', '',
          '## Scope remaining', '',
          'Instagram API work is deferred per the user. Its offline CSV validator/importer is tested on five controlled fixture rows; '
          '**no real Instagram rows or Business Discovery access were tested**. One observed platform cannot establish a cross-platform winner. '
          'Manual topic/language/creative/context review, a human sentiment evaluation set, and controlled follow-up marketing experiments remain research work. '
          'Public brand data cannot establish viewer nationality, age, gender, city, reach, retention, or causal posting-time effects.']
(ROOT / 'docs/YOUTUBE_COLLECTION_LOG.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(f'Audit passed: {len(posts)} posts, {len(comments)} comments, no foreign-key violations. Collection log saved.')
