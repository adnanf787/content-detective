"""Validate collected post and comment exports without filling missing measurements."""
import re
from urllib.parse import urlparse
import pandas as pd

COUNT_FIELDS = ['likes', 'comments', 'views', 'shares', 'saves', 'impressions', 'reach', 'follower_count']


def validate_exports(posts, comments=None):
    errors = []
    required = ['platform', 'brand', 'post_id', 'source_url', 'post_datetime', 'collection_datetime', 'source_type']
    for field in required:
        if field not in posts:
            errors.append(f'Missing post column: {field}')
    if errors:
        return {'valid': False, 'errors': errors, 'posts': len(posts), 'comments': 0 if comments is None else len(comments)}
    if posts.duplicated(['platform', 'post_id']).any():
        errors.append('Duplicate platform/post IDs')
    if posts[['platform', 'brand', 'post_id', 'source_url', 'collection_datetime']].fillna('').eq('').any().any():
        errors.append('Missing required identity/provenance values')
    for row in posts.itertuples():
        url = urlparse(str(row.source_url))
        allowed = {'YouTube': {'youtube.com', 'www.youtube.com', 'youtu.be'},
                   'Instagram': {'instagram.com', 'www.instagram.com'}}.get(row.platform)
        if url.scheme != 'https' or (allowed and url.hostname not in allowed) or url.username or url.password:
            errors.append('Invalid or platform-mismatched public source URL')
            break
    for field in COUNT_FIELDS:
        if field in posts:
            original = posts[field].astype('string').str.strip().replace('', pd.NA)
            numeric = pd.to_numeric(original, errors='coerce')
            bad = original.notna() & (numeric.isna() | numeric.lt(0) | numeric.mod(1).ne(0))
            if bad.any():
                errors.append(f'Invalid non-negative whole counts: {field}')
    published = pd.to_datetime(posts.post_datetime, utc=True, errors='coerce')
    observed = pd.to_datetime(posts.collection_datetime, utc=True, errors='coerce')
    supplied_dates = posts.post_datetime.astype('string').str.strip().fillna('').ne('')
    if (supplied_dates & published.isna()).any() or observed.isna().any():
        errors.append('Invalid publication/collection timestamps')
    if (published > observed).any():
        errors.append('Publication occurs after collection')
    # Collectors must provide offsets, rather than silently interpreting naive local clocks as UTC.
    for field in ['post_datetime', 'collection_datetime']:
        values = posts[field].astype('string').fillna('')
        if values[values.ne('')].map(lambda v: not bool(re.search(r'(Z|[+-]\d{2}:\d{2})$', v))).any():
            errors.append(f'Timezone offset required: {field}')
    if comments is not None and not comments.empty:
        comment_required = ['comment_id', 'platform', 'platform_post_id', 'comment_text', 'published_at_utc', 'collected_at_utc']
        if any(f not in comments for f in comment_required):
            errors.append('Missing comment columns')
        else:
            if comments.duplicated(['platform', 'comment_id']).any():
                errors.append('Duplicate comment IDs')
            keys = set(zip(posts.platform.astype(str), posts.post_id.astype(str)))
            if any((str(r.platform), str(r.platform_post_id)) not in keys for r in comments.itertuples()):
                errors.append('Comments reference unknown posts')
            dates = pd.to_datetime(comments.published_at_utc, utc=True, errors='coerce')
            measured = pd.to_datetime(comments.collected_at_utc, utc=True, errors='coerce')
            if dates.isna().any() or measured.isna().any() or (dates > measured).any():
                errors.append('Invalid comment timestamps')
    missing = {field: int(posts[field].isna().sum() + posts[field].astype('string').eq('').fillna(False).sum())
               for field in posts.columns}
    return {'valid': not errors, 'errors': list(dict.fromkeys(errors)), 'posts': len(posts),
            'comments': 0 if comments is None else len(comments), 'missing_fields': missing}
