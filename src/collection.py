"""Bounded public YouTube collection; credentials never enter records or manifests."""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler

import pandas as pd

from src.hashtags import extract_hashtags
from src.loader import Manifest

MAX_VIDEOS = 200
VIDEO_ID = re.compile(r'[A-Za-z0-9_-]{11}\Z')


class CollectionError(ValueError):
    pass


@dataclass
class Collection:
    posts: pd.DataFrame
    manifest: Manifest
    receipt: dict
    missing_ids: list[str]


def youtube_id(value):
    """Accept IDs and known watch/shorts/embed URL forms, never arbitrary hosts."""
    value = value.strip()
    if VIDEO_ID.fullmatch(value):
        return value
    parsed = urlparse(value if '://' in value else 'https://' + value)
    if parsed.scheme not in {'http', 'https'} or parsed.username or parsed.password:
        raise CollectionError('Use a public YouTube video URL or an 11-character video ID.')
    host = (parsed.hostname or '').lower()
    parts = parsed.path.strip('/').split('/')
    candidate = ''
    if host == 'youtu.be' and len(parts) == 1:
        candidate = parts[0]
    elif host in {'youtube.com', 'www.youtube.com', 'm.youtube.com', 'music.youtube.com'}:
        if parsed.path == '/watch':
            candidate = parse_qs(parsed.query).get('v', [''])[0]
        elif len(parts) == 2 and parts[0] in {'shorts', 'embed', 'live'}:
            candidate = parts[1]
    if not VIDEO_ID.fullmatch(candidate):
        raise CollectionError('Unsupported link. Paste a YouTube watch, Shorts, youtu.be link, or video ID.')
    return candidate


def parse_links(text):
    links = [line.strip() for line in text.splitlines() if line.strip()]
    if not links or len(links) > MAX_VIDEOS:
        raise CollectionError(f'Paste 1–{MAX_VIDEOS} video links, one per line.')
    return list(dict.fromkeys(youtube_id(link) for link in links))


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def api_request(endpoint, params, key):
    if endpoint not in {'search', 'videos'}:
        raise CollectionError('Unsupported collection endpoint.')
    url = 'https://www.googleapis.com/youtube/v3/' + endpoint + '?' + urlencode({**params, 'key': key})
    try:
        with build_opener(NoRedirect).open(Request(url, headers={'Accept': 'application/json'}), timeout=25) as response:
            content = response.read(8 * 1024 * 1024 + 1)
        if len(content) > 8 * 1024 * 1024:
            raise CollectionError('API response exceeded the collection limit. Try fewer videos.')
        payload = json.loads(content)
    except HTTPError as exc:
        # Do not include exception URLs or server messages: either can contain the key.
        raise CollectionError(f'YouTube API returned HTTP {exc.code}. Check that your key, API access, and quota are valid.') from None
    except (URLError, TimeoutError, OSError, ValueError):
        raise CollectionError('YouTube could not be reached or returned unreadable data. Retry the batch later.') from None
    if not isinstance(payload, dict) or not isinstance(payload.get('items'), list):
        raise CollectionError('YouTube returned an unexpected response. The dataset was not activated.')
    return payload


def video_row(item, collected_at):
    snippet = item.get('snippet', {})
    stats = item.get('statistics', {})
    title, description = snippet.get('title', ''), snippet.get('description', '')
    caption = title + '\n' + description
    video = item['id']
    return {
        'post_id': video, 'source_url': f'https://www.youtube.com/watch?v={video}',
        'source_name': 'YouTube Data API v3', 'source_type': 'official_api', 'is_synthetic': False,
        'platform': 'YouTube', 'brand': snippet.get('channelTitle', ''),
        'channel_id': snippet.get('channelId', ''), 'post_datetime': snippet.get('publishedAt', ''),
        'timezone_source': 'UTC', 'title': title, 'description': description, 'caption': caption,
        'hashtags': ' '.join(extract_hashtags(caption)),
        'platform_tags': json.dumps(snippet.get('tags', []), ensure_ascii=False),
        'platform_category_id': snippet.get('categoryId', ''),
        'duration_iso': item.get('contentDetails', {}).get('duration', ''),
        # Duration alone cannot establish whether YouTube classified a clip as a Short.
        'content_type': 'video', 'topic': '', 'caption_sentiment': '',
        'likes': stats.get('likeCount', ''), 'comments': stats.get('commentCount', ''),
        'views': stats.get('viewCount', ''), 'shares': '', 'reach': '', 'impressions': '',
        'follower_count': '', 'audience_location': '', 'audience_segment': '',
        'collection_datetime': collected_at,
    }


def collect_youtube(key, *, links='', query='', limit=50, published_after='', published_before='',
                    relevance_note='', request=api_request):
    key = key.strip()
    if not key:
        raise CollectionError('Add your YouTube Data API key locally, or use manual public observations.')
    if bool(links.strip()) == bool(query.strip()):
        raise CollectionError('Choose either video links or a search query.')
    if not isinstance(limit, int) or not 1 <= limit <= MAX_VIDEOS:
        raise CollectionError(f'Collection limit must be between 1 and {MAX_VIDEOS}.')
    if not relevance_note.strip():
        raise CollectionError('Document why these accounts or search terms relate to the Pakistan market.')
    if len(query) > 200:
        raise CollectionError('Keep the search query within 200 characters.')
    for value in (published_after, published_before):
        if value:
            try:
                parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                raise CollectionError('Search dates must be ISO timestamps with a timezone.') from None
            if parsed.tzinfo is None:
                raise CollectionError('Search dates must include a timezone.')
    if published_after and published_before:
        if datetime.fromisoformat(published_after.replace('Z', '+00:00')) >= datetime.fromisoformat(published_before.replace('Z', '+00:00')):
            raise CollectionError('Search start must be earlier than its end.')

    collected_at = datetime.now(timezone.utc).isoformat()
    receipts = []

    def fetch(endpoint, params):
        response = request(endpoint, params, key)
        if not isinstance(response, dict) or not isinstance(response.get('items'), list):
            raise CollectionError('Unexpected YouTube response; no observations were staged.')
        receipts.append({'endpoint': endpoint, 'parameters': params.copy(), 'response': response})
        return response

    ids = parse_links(links) if links.strip() else []
    if query.strip():
        token = ''
        for _ in range((limit + 49) // 50):
            params = {'part': 'snippet', 'type': 'video', 'q': query.strip(), 'order': 'date',
                      'regionCode': 'PK', 'maxResults': min(50, limit - len(ids))}
            if published_after:
                params['publishedAfter'] = published_after
            if published_before:
                params['publishedBefore'] = published_before
            if token:
                params['pageToken'] = token
            response = fetch('search', params)
            ids.extend(item.get('id', {}).get('videoId', '') for item in response['items'])
            ids = list(dict.fromkeys(i for i in ids if isinstance(i, str) and VIDEO_ID.fullmatch(i)))[:limit]
            token = response.get('nextPageToken', '')
            if not token or len(ids) >= limit:
                break
    if not ids:
        raise CollectionError('No public videos matched. Try another query or paste selected video links.')
    rows = {}
    for offset in range(0, len(ids), 50):
        response = fetch('videos', {'part': 'snippet,statistics,contentDetails', 'id': ','.join(ids[offset:offset + 50])})
        for item in response['items']:
            if isinstance(item, dict) and item.get('id') in ids:
                rows[item['id']] = video_row(item, collected_at)
    if not rows:
        raise CollectionError('No accessible video metadata was returned. Private or deleted videos may be omitted.')
    posts = pd.DataFrame([rows[i] for i in ids if i in rows])
    receipt = {'collected_at': collected_at, 'method': 'official_api', 'requests': receipts,
               'requested_ids': ids, 'missing_ids': [i for i in ids if i not in rows]}
    manifest = Manifest(file_name='youtube_collection.csv', source_name='YouTube Data API v3',
                        source_type='official_api', status='real', collected_on=collected_at,
                        source_timezone='UTC', geographic_relevance=relevance_note.strip(),
                        license_notes='Collected through YouTube Data API; review YouTube developer terms before redistribution.',
                        notes=('Public metadata snapshot. Search selection is not representative sampling. '
                               'PK means available in Pakistan, not verified Pakistani viewers. '
                               'Hidden counts remain missing; no private audience analytics or shares retrieved. '
                               'Platform tags are separate from caption hashtags. Format/topic/tone require review. '
                               f'Selection: {query.strip() or "explicit video IDs"}. '
                               f'Publication bounds: {published_after or "none"} to {published_before or "none"}.'),
                        sha256=hashlib.sha256(posts.to_csv(index=False).encode()).hexdigest())
    return Collection(posts, manifest, receipt, receipt['missing_ids'])


def manual_observation(*, url, platform, brand, caption, relevance_note, counts, published_at=''):
    parsed = urlparse(url.strip())
    if parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username or parsed.password:
        raise CollectionError('Record a full public post URL, beginning with https:// or http://.')
    if not brand.strip() or not relevance_note.strip():
        raise CollectionError('Record the account name and its Pakistan-market relevance.')
    observed = {}
    for field in ('likes', 'comments', 'shares', 'views'):
        value = str(counts.get(field, '')).strip()
        if value and not re.fullmatch(r'[0-9]+', value):
            raise CollectionError(f'{field.title()} must be a whole number without commas, or blank if unknown. Do not expand rounded counts such as 1.2K.')
        observed[field] = value
    if not any(observed.values()):
        raise CollectionError('Record at least one exact public count; unknown counts must stay blank.')
    if published_at:
        try:
            datetime.fromisoformat(published_at.replace('Z', '+00:00'))
        except ValueError:
            raise CollectionError('Use an ISO publication date or timestamp, or leave it blank.') from None
    collected_at = datetime.now(timezone.utc).isoformat()
    post_id = youtube_id(url) if platform == 'YouTube' else hashlib.sha256(url.strip().encode()).hexdigest()[:20]
    row = {'post_id': post_id, 'source_url': url.strip(), 'platform': platform, 'brand': brand.strip(),
           'source_name': 'Manual public-post observation', 'source_type': 'manual_public_post',
           'is_synthetic': False, 'caption': caption.strip(), 'hashtags': ' '.join(extract_hashtags(caption)),
           'post_datetime': published_at, 'collection_datetime': collected_at, **observed}
    posts = pd.DataFrame([row])
    manifest = Manifest(file_name='manual_observations.csv', source_name=row['source_name'],
                        source_type=row['source_type'], status='real', collected_on=collected_at,
                        geographic_relevance=relevance_note.strip(),
                        notes='User-recorded public counts; source accuracy is not independently verified. Unknown fields remain blank.')
    return Collection(posts, manifest, {'method': 'manual_public_post', 'collected_at': collected_at,
                                       'source_url': url.strip(), 'relevance_note': relevance_note.strip()}, [])
