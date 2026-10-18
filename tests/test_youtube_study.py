import copy
import json
from pathlib import Path
import sqlite3

import pandas as pd
import pytest

from src.content_nlp import category_cue, evaluation_table, language_cue, sentiment_cue
from src.dataset_validation import validate_exports
from src.instagram_csv import import_instagram_csv, instagram_template
from src.youtube_api import APIError, YouTubeAPI
from src.youtube_study import duration_seconds, get_comments, run_study, window_bounds


class Response:
    def __init__(self, data, status=200):
        self.status_code, self.data = status, data

    def iter_content(self, size):
        yield json.dumps(self.data).encode()

    def close(self):
        pass


class Session:
    def __init__(self, handler):
        self.handler, self.calls = handler, []

    def get(self, url, params, **kwargs):
        endpoint = url.rsplit('/', 1)[-1]
        self.calls.append((endpoint, params.copy()))
        return self.handler(endpoint, params)


def fixture_config():
    return {'industry': 'Pakistan telecom',
            'study': {'publication_start': '2026-04-01', 'publication_end': '2026-09-30',
                      'timezone': 'Asia/Karachi', 'videos_per_brand': 2, 'comments_per_video': 2, 'minimum_post_age_days': 7},
            'brands': [{'brand_id': 'test', 'brand_name': 'Test brand', 'country_relevance_note': 'Test fixture only',
                        'youtube': {'channel_id': 'channel-test', 'verified_official': True, 'verification_url': 'https://example.org'}}]}


def fixture_handler(endpoint, params):
    if endpoint == 'channels':
        return Response({'items': [{'id': 'channel-test', 'snippet': {'customUrl': '@test'},
                                     'statistics': {'subscriberCount': '1000', 'hiddenSubscriberCount': False},
                                     'contentDetails': {'relatedPlaylists': {'uploads': 'uploads-test'}}}]})
    if endpoint == 'playlistItems':
        if params.get('pageToken'):
            return Response({'items': [{'contentDetails': {'videoId': 'testvideo02', 'videoPublishedAt': '2026-06-02T10:00:00Z'}}]})
        return Response({'items': [{'contentDetails': {'videoId': 'testvideo01', 'videoPublishedAt': '2026-06-01T10:00:00Z'}}], 'nextPageToken': 'next'})
    if endpoint == 'videos':
        return Response({'items': [{'id': video, 'snippet': {'title': 'New bundle offer', 'description': '#Pakistan',
                                                            'channelId': 'channel-test', 'channelTitle': 'Test',
                                                            'publishedAt': f'2026-06-0{i+1}T10:00:00Z'},
                                    'statistics': {'viewCount': '1000', 'likeCount': '20', 'commentCount': '10'},
                                    'contentDetails': {'duration': 'PT30S'}} for i, video in enumerate(params['id'].split(','))]})
    assert endpoint == 'commentThreads'
    assert 'author' not in params['fields'] and params['order'] == 'time'
    video = params['videoId']
    return Response({'items': [{'id': 'thread-' + video, 'snippet': {'videoId': video, 'topLevelComment': {
        'id': 'comment-' + video, 'snippet': {'textOriginal': 'Great service thanks', 'publishedAt': '2026-06-10T10:00:00Z',
                                            'updatedAt': '2026-06-10T10:00:00Z', 'authorDisplayName': 'Must not persist'}}}}]})


def test_complete_snapshot_cache_resume_and_sqlite_idempotence(tmp_path):
    session = Session(fixture_handler)
    clients = []

    def client(key, path):
        api = YouTubeAPI(key, path, session=session, sleep=lambda _: None)
        clients.append(api)
        return api

    config = fixture_config()
    posts, comments, report = run_study(root=tmp_path, config=config, key='TEST_SECRET', run_id='fixture', client_factory=client)
    assert len(posts) == 2 and len(comments) == 2 and report['status'] == 'complete'
    assert report['validation']['valid']
    assert posts.shares.eq('').all() and posts['normalized_content_category'].eq('unknown').all()
    assert posts.followers_at_snapshot.eq(1000).all()
    assert posts.age_days_at_snapshot.gt(7).all()
    for path in (tmp_path / 'data/raw').rglob('*.json'):
        assert 'TEST_SECRET' not in path.read_text() and 'Must not persist' not in path.read_text()
    before = len(session.calls)
    config['brands'][0]['youtube']['verified_at_utc'] = 'new evidence timestamp'
    again, _, repeated = run_study(root=tmp_path, config=config, key='TEST_SECRET', run_id='fixture', client_factory=client)
    assert len(session.calls) == before and repeated['request_attempts'] == 0
    assert again.collection_datetime.tolist() == posts.collection_datetime.tolist()
    with sqlite3.connect(tmp_path / 'data/detective.sqlite') as db:
        assert db.execute('SELECT COUNT(*) FROM posts').fetchone()[0] == 2
        assert db.execute('SELECT COUNT(*) FROM post_metric_snapshots').fetchone()[0] == 2
        assert db.execute('SELECT COUNT(*) FROM comments').fetchone()[0] == 2
    config['study']['publication_start'] = '2025-10-01'
    with pytest.raises(ValueError, match='Resume configuration changed'):
        run_study(root=tmp_path, config=config, key='TEST_SECRET', run_id='fixture', client_factory=client)


def test_transient_retry_and_redacted_terminal_error(tmp_path):
    attempts = []

    def handler(endpoint, params):
        attempts.append(1)
        if len(attempts) == 1:
            return Response({'error': {'errors': [{'reason': 'backendError'}]}}, 503)
        return Response({'items': []})

    api = YouTubeAPI('secret', tmp_path / 'transient', session=Session(handler), sleep=lambda _: None)
    assert api.get('channels', {'part': 'snippet', 'id': 'channel'}) == {'items': []}
    assert len(attempts) == 2 and not api.errors
    bad = YouTubeAPI('secret', tmp_path / 'invalid', session=Session(lambda *args: Response({'error': {'errors': [{'reason': 'keyInvalid'}], 'message': 'secret'}}, 400)), sleep=lambda _: None)
    with pytest.raises(APIError) as error:
        bad.get('channels', {'id': 'channel'})
    assert bad.halted and 'secret' not in str(error.value) + json.dumps(bad.errors)


def test_comments_disabled_is_not_observed_zero_and_does_not_halt_other_videos(tmp_path):
    api = YouTubeAPI('secret', tmp_path, session=Session(lambda *args: Response({'error': {'errors': [{'reason': 'commentsDisabled'}]}}, 403)), sleep=lambda _: None)
    comments, status = get_comments(api, 'testvideo01', fixture_config()['brands'][0], 30, 'test')
    assert comments == [] and status == 'comments_disabled' and not api.halted
    assert api.errors[0]['reason'] == 'commentsDisabled'


def test_no_silent_window_extension_or_padding_when_brand_has_fewer_posts(tmp_path):
    def handler(endpoint, params):
        response = fixture_handler(endpoint, params)
        if endpoint == 'videos':
            response.data['items'][0]['snippet']['publishedAt'] = '2025-01-01T00:00:00Z'
        return response

    factory = lambda key, path: YouTubeAPI(key, path, session=Session(handler), sleep=lambda _: None)
    posts, _, report = run_study(root=tmp_path, config=fixture_config(), key='key', run_id='shortfall', client_factory=factory)
    assert len(posts) == 1 and report['status'] == 'partial'
    assert report['brands'][0]['status'] == 'shortfall_or_incomplete_enumeration'


def test_time_window_and_duration_are_explicit():
    start, end = window_bounds(fixture_config()['study'])
    assert start.isoformat() == '2026-03-31T19:00:00+00:00'
    assert end.isoformat() == '2026-09-30T19:00:00+00:00'
    assert duration_seconds('P1DT1H2M3S') == 90123
    assert duration_seconds('PT0S') == 0
    assert duration_seconds('unknown') is None


def test_instagram_csv_missing_metrics_strict_dates_and_source_method():
    rows = [{'brand': 'Fixture brand', 'verified_handle': 'testhandle', 'verification_url': 'https://example.org',
             'post_url': f'https://www.instagram.com/p/test{i}/', 'caption': 'Example',
             'published_at': '2026-06-01T10:00:00+05:00', 'collected_at': '2026-06-10T10:00:00+05:00',
             'source_method': 'manual_public', 'likes': '', 'comments_count': '2'} for i in range(5)]
    posts, manifest, quality = import_instagram_csv(pd.DataFrame(rows).to_csv(index=False).encode())
    assert len(posts) == 5 and quality['valid'] and posts.likes.eq('').all()
    assert posts.shares.isna().all() and manifest.source_type == 'manual_public_post'
    assert posts.access_status.eq('manual_only').all() and 'platform_post_id' in instagram_template()
    rows[0]['published_at'] = '2026-06-01T10:00:00'
    with pytest.raises(ValueError, match='Timezone offset'):
        import_instagram_csv(pd.DataFrame(rows).to_csv(index=False).encode())


def test_export_validation_rejects_duplicate_posts_or_orphan_comments(tmp_path):
    factory = lambda key, path: YouTubeAPI(key, path, session=Session(fixture_handler), sleep=lambda _: None)
    posts, comments, _ = run_study(root=tmp_path, config=fixture_config(), key='key', client_factory=factory)
    assert not validate_exports(pd.concat([posts, posts]), comments)['valid']
    comments.loc[0, 'platform_post_id'] = 'not-in-posts'
    assert 'Comments reference unknown posts' in validate_exports(posts, comments)['errors']


def test_nlp_cues_and_evaluation_never_invent_human_ground_truth():
    assert language_cue('Aap ka network acha hai') == 'Roman Urdu candidate'
    assert language_cue('زبردست نیٹ ورک') == 'Urdu-script candidate'
    assert sentiment_cue('not good')[0] == 'unassessed'
    assert sentiment_cue('Great service')[0] == 'positive'
    assert sentiment_cue('bohat bakwas network')[0] == 'negative'
    assert category_cue('An Eid offer')[0] == 'other / uncertain'
    blank = pd.DataFrame({'sentiment_label': ['positive'], 'human_label': ['']})
    assert evaluation_table(blank) is None
    labeled = pd.DataFrame({'sentiment_label': ['positive', 'unassessed', 'negative'], 'human_label': ['positive', 'neutral', 'negative']})
    assert evaluation_table(labeled)['n'] == 3
    assert evaluation_table(labeled)['macro_f1'] == pytest.approx(2 / 3)
