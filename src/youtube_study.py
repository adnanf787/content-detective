"""Verified-channel pilot: uploads playlists → 10 videos/brand → bounded public comments."""
from datetime import datetime, time, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

import pandas as pd
import yaml

from src.collection import video_row
from src.content_nlp import annotate_comments, category_cue, language_cue
from src.dataset_validation import validate_exports
from src.settings import ROOT, youtube_key
from src.study_storage import persist_study
from src.youtube_api import APIError, YouTubeAPI, atomic_json, utcnow

COMMENT_COLUMNS = ['comment_id', 'platform', 'platform_post_id', 'post_id', 'brand_id', 'brand', 'comment_text',
                   'published_at_utc', 'updated_at_utc', 'collected_at_utc', 'collection_method', 'source_method',
                   'raw_record_path', 'collection_run_id', 'language_inferred', 'sentiment_label', 'sentiment_method', 'sentiment_confidence']


def load_config(path=None):
    return yaml.safe_load(Path(path or ROOT / 'config/brands.yml').read_text(encoding='utf-8'))


def duration_seconds(value):
    match = re.fullmatch(r'P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?)?', value or '')
    if not match or not any(v is not None for v in match.groups()):
        return None
    days, hours, minutes, seconds = [float(v or 0) for v in match.groups()]
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def window_bounds(study):
    zone = ZoneInfo(study.get('timezone', 'Asia/Karachi'))
    start = datetime.combine(datetime.fromisoformat(study['publication_start']).date(), time.min, zone)
    end = datetime.combine(datetime.fromisoformat(study['publication_end']).date() + timedelta(days=1), time.min, zone)
    if start >= end:
        raise ValueError('Publication start must not follow the end date.')
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


def enumerate_uploads(api, playlist, start, end, *, max_pages=40):
    """Enumerate the bounded playlist, then sort by actual video publication timestamps.

    Do not assume playlist insertion timestamps or search order equal publication order.
    A page cap is disclosed as incomplete enumeration, not an implicit census.
    """
    ids, token, seen_tokens = [], '', set()
    for _ in range(max_pages):
        params = {'part': 'contentDetails', 'playlistId': playlist, 'maxResults': 50}
        if token:
            params['pageToken'] = token
        response = api.get('playlistItems', params)
        for item in response['items']:
            detail = item.get('contentDetails', {})
            video = detail.get('videoId')
            published = detail.get('videoPublishedAt')
            if video and published:
                try:
                    stamp = datetime.fromisoformat(published.replace('Z', '+00:00'))
                    if start <= stamp < end:
                        ids.append(video)
                except (ValueError, TypeError):
                    continue
        token = response.get('nextPageToken', '')
        if not token:
            return list(dict.fromkeys(ids)), True
        if token in seen_tokens:
            raise ValueError('Repeated playlist page token; enumeration stopped rather than looping.')
        seen_tokens.add(token)
    return list(dict.fromkeys(ids)), False


def get_comments(api, video_id, brand, limit, run_id):
    rows, token, seen_tokens = {}, '', set()
    if limit == 0:
        return [], 'not_requested'
    try:
        for _ in range(10):
            params = {'part': 'snippet', 'videoId': video_id, 'maxResults': min(100, limit - len(rows)),
                      'order': 'time', 'textFormat': 'plainText'}
            if token:
                params['pageToken'] = token
            response = api.get('commentThreads', params)
            for item in response['items']:
                top = item.get('snippet', {}).get('topLevelComment', {})
                snippet = top.get('snippet', {})
                if top.get('id') and snippet.get('publishedAt'):
                    rows[top['id']] = {'comment_id': top['id'], 'platform': 'YouTube', 'platform_post_id': video_id,
                                       'post_id': video_id, 'brand_id': brand['brand_id'], 'brand': brand['brand_name'],
                                       'comment_text': snippet.get('textOriginal', snippet.get('textDisplay', '')),
                                       'published_at_utc': snippet['publishedAt'], 'updated_at_utc': snippet.get('updatedAt', ''),
                                       'collected_at_utc': api.last_time, 'raw_record_path': api.last_path,
                                       'collection_run_id': run_id, 'collection_method': 'newest top-level public comments, capped per video; no replies',
                                       'source_method': 'youtube_data_api_v3.commentThreads.list'}
            token = response.get('nextPageToken', '')
            if not token or len(rows) >= limit:
                break
            if token in seen_tokens:
                raise ValueError('Repeated comments page token.')
            seen_tokens.add(token)
        status = 'sample_available' if rows else 'no_public_comments_returned'
        if token and len(rows) < limit:
            status = 'sample_incomplete_page_limit'
        return list(rows.values())[:limit], status
    except APIError as exc:
        status = 'comments_disabled' if exc.reason == 'commentsDisabled' else 'comments_unavailable'
        return list(rows.values())[:limit], status


def normalize_video(item, account, brand, api, run_id):
    row = video_row(item, api.last_time)
    published = datetime.fromisoformat(row['post_datetime'].replace('Z', '+00:00'))
    category, evidence = category_cue(row['caption'])
    live = item.get('snippet', {}).get('liveBroadcastContent') in {'live', 'upcoming'} or bool(item.get('liveStreamingDetails', {}).get('actualStartTime'))
    row.update(brand=brand['brand_name'], brand_id=brand['brand_id'], platform_post_id=item['id'],
               account_id=account['platform_account_id'], source_method='youtube_data_api_v3',
               post_url=row['source_url'], published_at_utc=published.astimezone(timezone.utc).isoformat(),
               published_at_pakistan=published.astimezone(ZoneInfo('Asia/Karachi')).isoformat(),
               native_media_type='YouTube video', normalized_content_category='live' if live else 'unknown',
               content_type='live video' if live else 'video', duration_seconds=duration_seconds(row['duration_iso']),
               format_method='Live status uses explicit live metadata; Shorts/long-video classification is unknown, not inferred from duration.',
               language_inferred=language_cue(row['caption']), language_method='Script and small token lexicons; candidate only, needs human review',
               category_suggested=category, category_evidence=evidence, category_method='Transparent overlapping keyword rules; unevaluated',
               followers_at_snapshot=account['followers_at_snapshot'], follower_count=account['followers_at_snapshot'],
               followers_snapshot_at=account['followers_snapshot_at'], follower_count_is_rounded=True,
               saves=None, raw_record_path=api.last_path, collection_run_id=run_id, access_status='official_api',
               age_days_at_snapshot=(datetime.fromisoformat(api.last_time) - published).total_seconds() / 86400)
    return row


def write_csv(path, frame):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    frame.to_csv(temporary, index=False, encoding='utf-8-sig')
    temporary.replace(path)


def selection_digest(config):
    selection = {'study': config['study'], 'brands': [
        {key: b[key] for key in ('brand_id', 'brand_name')} | {'channel_id': b['youtube'].get('channel_id'),
                                                            'verified_official': b['youtube'].get('verified_official')}
        for b in config['brands']]}
    return hashlib.sha256(json.dumps(selection, sort_keys=True, default=str).encode()).hexdigest()


def run_study(*, root=ROOT, config=None, key=None, run_id=None, progress=None, client_factory=YouTubeAPI):
    root = Path(root)
    config = config or load_config(root / 'config/brands.yml')
    study = config['study']
    target, comment_limit = int(study['videos_per_brand']), int(study['comments_per_video'])
    if not 1 <= target <= 200 or not 0 <= comment_limit <= 100:
        raise ValueError('Pilot limits: 1–200 videos/brand and 0–100 comments/video.')
    start, end = window_bounds(study)
    run_id = run_id or datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', run_id):
        raise ValueError('Invalid run identifier.')
    run_dir = root / 'data/raw' / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    state_path = run_dir / 'state.json'
    selection_hash = selection_digest(config)
    if state_path.exists():
        state = json.loads(state_path.read_text())
        if selection_digest(state['config']) != selection_hash:
            raise ValueError('Resume configuration changed; start a new snapshot instead.')
    else:
        state = {'run_id': run_id, 'started_at_utc': utcnow(), 'selection_hash': selection_hash, 'config': config}
        atomic_json(state_path, state)
    api = client_factory(key if key is not None else youtube_key(), run_dir)
    snapshot = datetime.fromisoformat(state['started_at_utc'])
    cutoff = snapshot - timedelta(days=int(study.get('minimum_post_age_days', 7)))
    rows, comments, accounts, brand_results = [], [], [], []
    failure_notes = []
    for brand in config['brands']:
        record = {'brand': brand['brand_name'], 'requested': target, 'posts_collected': 0, 'comments_collected': 0, 'status': 'not_started'}
        brand_results.append(record)
        if api.halted:
            record['status'] = 'skipped_after_credential_or_quota_failure'
            continue
        if progress:
            progress(f'{brand["brand_name"]}: checking channel and enumerating eligible uploads…')
        try:
            entry = brand['youtube']
            if not entry.get('verified_official') or not entry.get('channel_id'):
                raise ValueError('Official channel must be verified in config/brands.yml before collection.')
            response = api.get('channels', {'part': 'snippet,contentDetails,statistics', 'id': entry['channel_id']})
            if len(response['items']) != 1 or response['items'][0]['id'] != entry['channel_id']:
                raise ValueError('Verified channel ID did not resolve uniquely.')
            channel = response['items'][0]
            stats = channel.get('statistics', {})
            followers = None if stats.get('hiddenSubscriberCount', False) else stats.get('subscriberCount')
            account = {'brand_id': brand['brand_id'], 'platform': 'YouTube', 'platform_account_id': channel['id'],
                       'handle': channel['snippet'].get('customUrl', ''), 'verified_official': True,
                       'verification_url': entry['verification_url'], 'followers_at_snapshot': int(followers) if followers is not None else None,
                       'followers_snapshot_at': api.last_time}
            accounts.append(account)
            ids, complete = enumerate_uploads(api, channel['contentDetails']['relatedPlaylists']['uploads'], start, min(end, cutoff))
            record.update(eligible_playlist_ids=len(ids), enumeration_complete=complete)
            candidates = []
            for offset in range(0, len(ids), 50):
                response = api.get('videos', {'part': 'snippet,statistics,contentDetails,liveStreamingDetails', 'id': ','.join(ids[offset:offset + 50])})
                for item in response['items']:
                    snippet = item.get('snippet', {})
                    if snippet.get('channelId') != channel['id'] or not snippet.get('publishedAt'):
                        continue
                    stamp = datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00'))
                    if start <= stamp < end and stamp <= cutoff:
                        candidates.append(normalize_video(item, account, brand, api, run_id))
            selected = sorted({r['post_id']: r for r in candidates}.values(), key=lambda r: (r['post_datetime'], r['post_id']), reverse=True)[:target]
            for row in selected:
                sample, status = get_comments(api, row['post_id'], brand, comment_limit, run_id)
                row.update(comment_sample_status=status, downloaded_comment_count=len(sample))
                rows.append(row)
                comments.extend(sample)
            record.update(posts_collected=len(selected), comments_collected=sum(r['brand_id'] == brand['brand_id'] for r in comments),
                          unavailable_video_ids=len(ids) - len(candidates),
                          status='complete' if len(selected) == target and complete else 'shortfall_or_incomplete_enumeration')
            if progress:
                progress(f'{brand["brand_name"]}: {len(selected)} videos, {record["comments_collected"]} sampled comments.')
        except (APIError, ValueError, KeyError, TypeError) as exc:
            # Exceptions from API transport are already redacted. Avoid printing foreign messages.
            record['status'] = 'failed'
            record['error'] = str(exc) if isinstance(exc, APIError) else 'Invalid channel configuration or unexpected source data; inspect raw records.'
            failure_notes.append({'brand': brand['brand_name'], 'error': record['error']})
            if progress:
                progress(f'{brand["brand_name"]}: {record["error"]}')
    posts = pd.DataFrame(rows).drop_duplicates(['platform', 'post_id']) if rows else pd.DataFrame(columns=['platform', 'brand', 'post_id', 'source_url', 'post_datetime', 'collection_datetime', 'source_type'])
    comment_frame = pd.DataFrame(comments).drop_duplicates(['platform', 'comment_id']) if comments else pd.DataFrame(columns=COMMENT_COLUMNS)
    comment_frame = annotate_comments(comment_frame).reindex(columns=COMMENT_COLUMNS)
    validation = validate_exports(posts, comment_frame)
    summary = {**{k: state[k] for k in ('run_id', 'started_at_utc')}, 'ended_at_utc': utcnow(),
               'posts_requested': target * len(config['brands']), 'posts_collected': len(posts), 'comments_collected': len(comment_frame),
               'brands': brand_results, 'validation': validation, 'api_errors': api.errors, 'collection_errors': failure_notes,
               'request_attempts': sum(not r.get('cache_hit', False) for r in api.requests),
               'cached_responses_used': sum(r.get('cache_hit', False) for r in api.requests),
               'estimated_quota_units_this_invocation': sum(not r.get('cache_hit', False) for r in api.requests),
               'quota_note': 'These list endpoints are documented at 1 unit per request. Cache reads make no request. Console project limits are authoritative.',
               'sampling_method': f'Newest {target} eligible uploads per verified brand in {study["publication_start"]}–{study["publication_end"]} Asia/Karachi; minimum age {study.get("minimum_post_age_days", 7)} days; up to {comment_limit} newest top-level comments/video; no replies.',
               'limitations': 'Pakistan-relevant brands, not verified Pakistani viewers. No audience demographics, reach, impressions, shares, saves, retention, or causal posting-time effects. Subscriber counts are rounded snapshots. Comment sample is recent, capped, moderated, self-selected, and not representative. NLP uses unevaluated cue rules; confidence and human evaluation remain unavailable.'}
    summary['status'] = 'complete' if len(posts) == summary['posts_requested'] and validation['valid'] and not failure_notes else 'partial' if len(posts) and validation['valid'] else 'failed'
    if any(r.get('status') != 'complete' for r in brand_results) or api.errors:
        if summary['status'] == 'complete':
            summary['status'] = 'complete_with_limitations'
    # Every run is auditable, including failed attempts; successful prior exports survive failures.
    write_csv(run_dir / 'youtube_posts.csv', posts)
    write_csv(run_dir / 'youtube_comments.csv', comment_frame)
    atomic_json(run_dir / 'summary.json', summary)
    invocation = {'invoked_at_utc': utcnow(), 'requests': api.requests, 'api_errors': api.errors}
    atomic_json(run_dir / 'request_log.json', invocation)
    atomic_json(run_dir / 'invocations' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json'), invocation)
    persist_study(root / 'data/detective.sqlite', config, accounts, posts if validation['valid'] else posts.iloc[:0],
                  comment_frame if validation['valid'] else comment_frame.iloc[:0], summary)
    if len(posts) and validation['valid']:
        out = root / 'data/processed'
        write_csv(out / 'youtube_posts.csv', posts)
        write_csv(out / 'youtube_comments.csv', comment_frame)
        write_csv(out / 'normalized_posts.csv', posts)
        write_csv(out / 'sentiment_review_template.csv', comment_frame.assign(human_label='')[['comment_id', 'brand', 'comment_text', 'language_inferred', 'sentiment_label', 'human_label']])
        atomic_json(out / 'youtube_collection_report.json', summary)
        atomic_json(out / 'youtube_accounts.json', accounts)
    return posts, comment_frame, summary
