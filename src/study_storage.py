"""SQLite identities and separate observation snapshots; repeat runs are idempotent."""
import json
import sqlite3
from pathlib import Path
import pandas as pd

SCHEMA = '''
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS brands (
 brand_id TEXT PRIMARY KEY, brand_name TEXT NOT NULL, industry TEXT, country_relevance_note TEXT);
CREATE TABLE IF NOT EXISTS accounts (
 platform TEXT, platform_account_id TEXT, brand_id TEXT REFERENCES brands(brand_id),
 handle TEXT, verified_official INTEGER, verification_url TEXT,
 followers_at_snapshot INTEGER, followers_snapshot_at TEXT,
 PRIMARY KEY (platform, platform_account_id));
CREATE TABLE IF NOT EXISTS posts (
 platform TEXT, platform_post_id TEXT, brand_id TEXT REFERENCES brands(brand_id),
 account_id TEXT, post_url TEXT, published_at_utc TEXT, published_at_pakistan TEXT,
 caption_or_title TEXT, description TEXT, native_media_type TEXT,
 normalized_content_category TEXT, duration_seconds REAL, source_method TEXT,
 collected_at_utc TEXT, raw_record_path TEXT, access_status TEXT, record_json TEXT,
 PRIMARY KEY (platform, platform_post_id));
CREATE TABLE IF NOT EXISTS post_metric_snapshots (
 platform TEXT, platform_post_id TEXT, measured_at_utc TEXT,
 views INTEGER, likes INTEGER, comments_count INTEGER, shares INTEGER, saves INTEGER,
 followers_at_snapshot INTEGER, metric_source TEXT,
 PRIMARY KEY (platform, platform_post_id, measured_at_utc),
 FOREIGN KEY (platform, platform_post_id) REFERENCES posts(platform, platform_post_id));
CREATE TABLE IF NOT EXISTS comments (
 platform TEXT, comment_id TEXT, platform_post_id TEXT, comment_text TEXT,
 published_at_utc TEXT, language_inferred TEXT, sentiment_label TEXT, sentiment_confidence REAL,
 collection_method TEXT, collected_at_utc TEXT, raw_record_path TEXT,
 PRIMARY KEY (platform, comment_id),
 FOREIGN KEY (platform, platform_post_id) REFERENCES posts(platform, platform_post_id));
CREATE TABLE IF NOT EXISTS collection_runs (
 run_id TEXT PRIMARY KEY, platform TEXT, started_at_utc TEXT, ended_at_utc TEXT,
 status TEXT, posts_requested INTEGER, posts_collected INTEGER, comments_collected INTEGER,
 fields_missing_json TEXT, api_errors_redacted TEXT, sampling_method TEXT, notes TEXT);
'''


def scalar(value):
    return None if value is None or pd.isna(value) else value


def upsert(connection, table, columns, values, keys):
    updates = ', '.join(f'{name}=excluded.{name}' for name in columns if name not in keys)
    connection.execute(f'INSERT INTO {table} ({", ".join(columns)}) VALUES ({", ".join("?" for _ in columns)}) '
                       f'ON CONFLICT ({", ".join(keys)}) DO UPDATE SET {updates}', [scalar(v) for v in values])


def persist_study(path, config, accounts, posts, comments, summary):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.executescript(SCHEMA)
        for brand in config['brands']:
            upsert(connection, 'brands', ['brand_id', 'brand_name', 'industry', 'country_relevance_note'],
                   [brand['brand_id'], brand['brand_name'], config['industry'], brand['country_relevance_note']], ['brand_id'])
        for row in accounts:
            columns = ['platform', 'platform_account_id', 'brand_id', 'handle', 'verified_official', 'verification_url', 'followers_at_snapshot', 'followers_snapshot_at']
            upsert(connection, 'accounts', columns, [row.get(c) for c in columns], ['platform', 'platform_account_id'])
        for row in posts.to_dict('records'):
            payload = json.loads(pd.DataFrame([row]).to_json(orient='records'))[0]
            record = {**row, 'record_json': json.dumps(payload, ensure_ascii=False), 'caption_or_title': row.get('caption'),
                      'post_url': row.get('source_url'), 'collected_at_utc': row.get('collection_datetime')}
            columns = ['platform', 'platform_post_id', 'brand_id', 'account_id', 'post_url', 'published_at_utc', 'published_at_pakistan',
                       'caption_or_title', 'description', 'native_media_type', 'normalized_content_category', 'duration_seconds',
                       'source_method', 'collected_at_utc', 'raw_record_path', 'access_status', 'record_json']
            upsert(connection, 'posts', columns, [record.get(c) for c in columns], ['platform', 'platform_post_id'])
            columns = ['platform', 'platform_post_id', 'measured_at_utc', 'views', 'likes', 'comments_count', 'shares', 'saves', 'followers_at_snapshot', 'metric_source']
            metric = {**row, 'measured_at_utc': row['collection_datetime'], 'comments_count': row.get('comments'), 'metric_source': row.get('source_method')}
            upsert(connection, 'post_metric_snapshots', columns, [metric.get(c) for c in columns], ['platform', 'platform_post_id', 'measured_at_utc'])
        for row in comments.to_dict('records'):
            columns = ['platform', 'comment_id', 'platform_post_id', 'comment_text', 'published_at_utc', 'language_inferred',
                       'sentiment_label', 'sentiment_confidence', 'collection_method', 'collected_at_utc', 'raw_record_path']
            upsert(connection, 'comments', columns, [row.get(c) for c in columns], ['platform', 'comment_id'])
        columns = ['run_id', 'platform', 'started_at_utc', 'ended_at_utc', 'status', 'posts_requested', 'posts_collected', 'comments_collected',
                   'fields_missing_json', 'api_errors_redacted', 'sampling_method', 'notes']
        record = {**summary, 'platform': 'YouTube', 'fields_missing_json': json.dumps(summary.get('validation', {}).get('missing_fields', {})),
                  'api_errors_redacted': json.dumps(summary.get('api_errors', [])), 'notes': summary.get('limitations', '')}
        upsert(connection, 'collection_runs', columns, [record.get(c) for c in columns], ['run_id'])
