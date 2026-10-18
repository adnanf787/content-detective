import json
from urllib.error import HTTPError

import pandas as pd
import pytest

from src.analysis import prepare
from src.collection import CollectionError, api_request, collect_youtube, manual_observation, parse_links, youtube_id
from src.metrics import choose_metric

IDS = [f'pkvideo{i:04}' for i in range(61)]


def item(video=IDS[0]):
    return {'id': video, 'snippet': {'title': 'Summer #پاکستان', 'description': 'A product demo #Style',
                                    'channelTitle': 'Example brand', 'channelId': 'channel-1',
                                    'publishedAt': '2026-10-01T13:00:00Z', 'tags': ['clothes', 'Pakistan']},
            'statistics': {'viewCount': '1000', 'likeCount': '20', 'commentCount': '5'},
            'contentDetails': {'duration': 'PT1M20S'}}


@pytest.mark.parametrize('value', [IDS[0], f'https://youtu.be/{IDS[0]}?t=3',
                                    f'https://www.youtube.com/watch?v={IDS[0]}&utm_source=test',
                                    f'https://youtube.com/shorts/{IDS[0]}', f'https://m.youtube.com/live/{IDS[0]}'])
def test_video_url_forms(value):
    assert youtube_id(value) == IDS[0]


@pytest.mark.parametrize('value', ['https://youtube.com.evil.test/watch?v=' + IDS[0],
                                    'https://example.com/' + IDS[0], 'file:///tmp/secret',
                                    'https://youtube.com/@account', 'https://user:password@youtube.com/watch?v=' + IDS[0]])
def test_rejects_unrelated_and_nonvideo_links(value):
    with pytest.raises(CollectionError):
        youtube_id(value)


def test_link_dedup_and_missing_counts_remain_unknown():
    assert parse_links(f'{IDS[0]}\nhttps://youtu.be/{IDS[0]}') == [IDS[0]]
    calls = []

    def request(endpoint, params, key):
        calls.append((endpoint, params, key))
        video = item()
        del video['statistics']['commentCount']
        return {'items': [video]}

    result = collect_youtube('SECRET_TEST_KEY', links=IDS[0], relevance_note='Selected Pakistani clothing brand', request=request)
    frame, quality = prepare(result.posts, result.manifest)
    assert frame.iloc[0].likes == 20 and pd.isna(frame.iloc[0].comments)
    assert pd.isna(frame.iloc[0].shares) and pd.isna(frame.iloc[0].visible_per_1000_views)
    assert frame.iloc[0].hour == 18
    assert frame.iloc[0].data_status == 'real (declared)'
    assert '#پاکستان' in frame.iloc[0].hashtags
    assert 'clothes' in frame.iloc[0].platform_tags and '#clothes' not in frame.iloc[0].hashtags
    assert pd.isna(frame.iloc[0].audience_location) and pd.isna(frame.iloc[0].topic)
    assert 'SECRET_TEST_KEY' not in json.dumps(result.receipt) + json.dumps(result.manifest.to_dict()) + result.posts.to_csv()
    assert calls[0][0] == 'videos' and quality['invalid_timestamps'] == 0


def test_search_pagination_batching_omitted_ids_and_metrics():
    calls = []

    def request(endpoint, params, key):
        calls.append((endpoint, params.copy()))
        if endpoint == 'search':
            assert params['regionCode'] == 'PK' and params['order'] == 'date'
            page = IDS[50:] if params.get('pageToken') else IDS[:50]
            return {'items': [{'id': {'videoId': v}} for v in page], 'nextPageToken': '' if params.get('pageToken') else 'page2'}
        return {'items': [item(v) for v in params['id'].split(',') if v != IDS[-1]]}

    result = collect_youtube('key', query='Pakistan clothing', limit=61, relevance_note='Market-related query; review accounts', request=request)
    assert len(result.posts) == 60 and result.missing_ids == [IDS[-1]]
    assert [call[0] for call in calls] == ['search', 'search', 'videos', 'videos']
    frame, _ = prepare(result.posts, result.manifest)
    assert choose_metric(frame).name == 'visible_per_1000_views'
    assert frame.visible_per_1000_views.eq(25).all()


def test_no_network_for_invalid_input_and_no_fabricated_empty_search():
    def forbidden(*args):
        pytest.fail('Invalid input reached the network')

    with pytest.raises(CollectionError):
        collect_youtube('', links=IDS[0], relevance_note='Pakistan brand', request=forbidden)
    with pytest.raises(CollectionError):
        collect_youtube('key', links=IDS[0], query='test', relevance_note='Pakistan brand', request=forbidden)
    with pytest.raises(CollectionError):
        collect_youtube('key', query='test', limit=201, relevance_note='Pakistan brand', request=forbidden)
    with pytest.raises(CollectionError):
        collect_youtube('key', query='test', published_after='2026-10-01', relevance_note='Pakistan brand', request=forbidden)
    with pytest.raises(CollectionError, match='No public videos'):
        collect_youtube('key', query='test', relevance_note='Pakistan brand', request=lambda *args: {'items': []})


def test_api_errors_never_echo_key(monkeypatch):
    class FailingOpener:
        def open(self, request, timeout):
            raise HTTPError(request.full_url, 403, 'Secret echoed: EXAMPLE_SECRET', {}, None)

    monkeypatch.setattr('src.collection.build_opener', lambda *args: FailingOpener())
    with pytest.raises(CollectionError) as error:
        api_request('videos', {'part': 'snippet'}, 'EXAMPLE_SECRET')
    assert 'EXAMPLE_SECRET' not in str(error.value) and '403' in str(error.value)


def test_manual_observation_exact_counts_and_unknowns():
    result = manual_observation(url='https://www.instagram.com/p/example/', platform='Instagram',
                                brand='Pakistan brand', caption='آپ کی پسند #پاکستان', relevance_note='Local brand',
                                counts={'likes': '0', 'comments': '12'}, published_at='2026-10-01')
    frame, _ = prepare(result.posts, result.manifest)
    assert frame.likes.iloc[0] == 0 and frame.comments.iloc[0] == 12
    assert pd.isna(frame.shares.iloc[0]) and pd.isna(frame.views.iloc[0])
    assert frame.time_status.iloc[0] == 'timezone unknown'
    with pytest.raises(CollectionError, match='whole number'):
        manual_observation(url='https://www.instagram.com/p/example/', platform='Instagram', brand='brand',
                           caption='', relevance_note='Local', counts={'likes': '1.2K'})
