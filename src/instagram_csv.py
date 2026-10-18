"""Strict, offline Instagram fallback. No Instagram API or login requests are made."""
import hashlib
from urllib.parse import urlparse
import pandas as pd

from src.dataset_validation import validate_exports
from src.loader import Manifest, read_csv

INSTAGRAM_COLUMNS = ['platform_post_id', 'brand', 'verified_handle', 'verification_url', 'post_url',
                     'caption', 'published_at', 'media_type', 'likes', 'comments_count',
                     'views', 'followers_at_snapshot', 'collected_at', 'source_method']


def instagram_template():
    return ','.join(INSTAGRAM_COLUMNS) + '\n'


def import_instagram_csv(content):
    raw = read_csv(content)
    required = ['brand', 'verified_handle', 'verification_url', 'post_url', 'published_at', 'collected_at', 'source_method']
    missing = [f for f in required if f not in raw]
    if missing:
        raise ValueError('Missing Instagram CSV columns: ' + ', '.join(missing))
    for field in required:
        if raw[field].str.strip().eq('').any():
            raise ValueError(f'Each Instagram row needs {field}; keep unavailable measurements blank.')
    if not raw.source_method.eq('manual_public').all():
        raise ValueError('This fallback accepts source_method=manual_public; use the generic importer for other documented sources.')
    for value in raw.verification_url:
        parsed = urlparse(value)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError('Verification URLs must be public HTTPS source references.')
    posts = pd.DataFrame(index=raw.index)
    posts['platform'] = 'Instagram'
    posts['brand'] = raw.brand.str.strip()
    posts['source_url'] = raw.post_url.str.strip()
    posts['post_url'] = posts.source_url
    extracted = posts.source_url.map(lambda value: urlparse(value).path.strip('/').split('/'))
    if extracted.map(lambda parts: len(parts) != 2 or parts[0] not in {'p', 'reel', 'tv'} or not parts[1]).any():
        raise ValueError('Each Instagram URL must reference a public post, reel, or legacy tv item.')
    ids = extracted.map(lambda parts: parts[1])
    supplied_ids = raw.get('platform_post_id', pd.Series('', index=raw.index)).str.strip()
    posts['post_id'] = supplied_ids.where(supplied_ids.ne(''), ids)
    posts['platform_post_id'] = posts.post_id
    posts['verified_handle'] = raw.verified_handle.str.strip()
    posts['verification_url'] = raw.verification_url
    posts['caption'] = raw.get('caption', '')
    posts['post_datetime'] = raw.published_at
    posts['collection_datetime'] = raw.collected_at
    posts['content_type'] = raw.get('media_type', '')
    for source, target in [('likes', 'likes'), ('comments_count', 'comments'), ('views', 'views'), ('followers_at_snapshot', 'follower_count')]:
        posts[target] = raw.get(source, '')
    for field in ['shares', 'saves', 'reach', 'impressions']:
        posts[field] = pd.NA
    posts['source_type'] = 'manual_public_post'
    posts['source_method'] = 'manual_public'
    posts['source_name'] = 'Documented Instagram public observation CSV'
    posts['is_synthetic'] = False
    posts['timezone_source'] = 'unknown'
    posts['access_status'] = 'manual_only'
    # Keys identify the supplied handle; public CSV does not verify an official API account ID.
    posts['account_id'] = posts.verified_handle
    quality = validate_exports(posts)
    if not quality['valid']:
        raise ValueError('Instagram CSV validation failed: ' + '; '.join(quality['errors']))
    manifest = Manifest(file_name='instagram_posts.csv', source_name='Documented Instagram public observations',
                        source_type='manual_public_post', status='real',
                        geographic_relevance='User-documented Pakistan-relevant accounts; viewer geography is unknown',
                        notes='Manual public metrics. Handle and official-affiliation evidence are supplied by the collector, not independently verified by this importer. Counts and URLs require source review. No comment text or private insights are available.',
                        sha256=hashlib.sha256(content).hexdigest())
    return posts, manifest, quality
