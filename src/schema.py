"""Canonical fields and explicit import aliases; mapping is always reviewable."""
METRICS = ['likes', 'comments', 'shares', 'views', 'impressions', 'reach', 'follower_count']
FIELDS = [
    'post_id', 'source_url', 'source_name', 'source_type', 'is_synthetic', 'brand',
    'platform', 'post_datetime', 'timezone_source', 'content_type', 'caption',
    'hashtags', 'topic', 'caption_language', 'creative_angle', 'local_context', *METRICS, 'audience_location', 'audience_segment',
    'caption_sentiment', 'collection_datetime',
]
ALIASES = {
    'post_datetime': ['post_timestamp', 'post_date', 'timestamp', 'date'],
    'likes': ['likes_count', 'like_count'], 'comments': ['comments_count', 'comment_count'],
    'shares': ['shares_count', 'share_count'], 'views': ['views_count', 'view_count'],
    'brand': ['account', 'account_name'], 'caption': ['text', 'post_text'],
    'content_type': ['post_type', 'format'], 'follower_count': ['followers'],
}


def suggest_mapping(columns):
    lookup = {str(c).strip().lower(): c for c in columns}
    return {field: next((lookup[n] for n in [field, *ALIASES.get(field, [])] if n in lookup), None)
            for field in FIELDS}


def apply_mapping(raw, mapping):
    selected = {target: source for target, source in mapping.items() if source is not None}
    if len(set(selected.values())) != len(selected):
        raise ValueError('A source column cannot map to two canonical fields.')
    result = raw[list(selected.values())].rename(columns={v: k for k, v in selected.items()}).copy()
    if not selected:
        raise ValueError('Map at least one source column before importing.')
    # Unmapped fields remain in the original preview, never guessed as measurements.
    return result
