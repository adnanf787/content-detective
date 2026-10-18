"""Explicit metric definitions and group coverage; never impute absent measurements."""
from dataclasses import dataclass
import numpy as np
import pandas as pd

DEFINITIONS = {
    'available_interactions': 'Sum of observed likes/comments/shares per post; at least one observed component required. Components may differ.',
    'complete_interactions': 'likes + comments + shares, only when all three are valid',
    'visible_interactions': 'Visible interactions (likes + comments), only when both are valid',
    'visible_per_1000_views': '1,000 × (likes + comments) / views; both counts and positive views required; excludes shares; interactions per view, not a percentage of unique people',
    'visible_rate_followers': '100 × (likes + comments) / followers at snapshot; public-interaction-to-audience-size proxy, not a reach-based engagement rate; subscriber counts may be rounded and measured after publication',
    'rate_impressions': '100 × complete interactions / impressions, with positive impressions',
    'rate_reach': '100 × complete interactions / reach, with positive reach',
    'rate_views': 'Per-view interaction rate: 100 × complete interactions / views, with positive views',
    'rate_followers': '100 × complete interactions / follower count; followers must be positive, observation-time caveat applies',
    'likes': 'Observed likes only', 'comments': 'Observed comments only', 'shares': 'Observed shares only',
}


def add_metrics(frame):
    df = frame.copy()
    parts = ['likes', 'comments', 'shares']
    df['available_interactions'] = df[parts].sum(axis=1, min_count=1)
    df['observed_components'] = df.apply(lambda r: ', '.join(c for c in parts if pd.notna(r[c])), axis=1)
    df['complete_interactions'] = df[parts].sum(axis=1, min_count=3)
    df['visible_interactions'] = df[['likes', 'comments']].sum(axis=1, min_count=2)
    for name in ['available_interactions', 'complete_interactions', 'visible_interactions']:
        df[name] = df[name].where(np.isfinite(df[name]))
    visible_rate = 1000 * df.visible_interactions / df.views.where(df.views > 0)
    df['visible_per_1000_views'] = visible_rate.where(np.isfinite(visible_rate))
    follower_proxy = 100 * df.visible_interactions / df.follower_count.where(df.follower_count > 0)
    df['visible_rate_followers'] = follower_proxy.where(np.isfinite(follower_proxy))
    for name, denom in [('impressions', 'impressions'), ('reach', 'reach'), ('views', 'views'), ('followers', 'follower_count')]:
        values = 100 * df.complete_interactions / df[denom].where(df[denom] > 0)
        df[f'rate_{name}'] = values.where(np.isfinite(values))
    publication = pd.to_datetime(df.parsed_datetime, utc=True, errors='coerce', format='mixed').where(df.time_status.eq('known'))
    explicit_observation = df.collection_datetime.str.contains(r'(?:Z|[+-]\d{2}:\d{2})$', na=False)
    observation = pd.to_datetime(df.collection_datetime.where(explicit_observation), utc=True, errors='coerce', format='mixed')
    age = (observation - publication).dt.total_seconds() / 86400
    df['age_days_at_snapshot'] = age.where(age >= 0)
    return df


@dataclass
class MetricChoice:
    name: str
    reason: str


def choose_metric(df):
    order = ['rate_impressions', 'rate_reach', 'rate_views', 'rate_followers',
             'visible_per_1000_views', 'visible_rate_followers', 'complete_interactions', 'visible_interactions', 'likes', 'comments', 'shares']
    for metric in order:
        if len(df) and df[metric].notna().mean() >= .8:
            return MetricChoice(metric, 'First defined metric with at least 80% valid coverage in the active selection.')
    counts = {m: int(df[m].notna().sum()) for m in order}
    best = max(counts, key=counts.get)
    return MetricChoice(best, 'No metric reaches 80% coverage; using the most observed consistent metric. Comparisons are partial.')


def summarize(df, group, metric, min_n=5):
    columns = [group, 'total_posts', 'n', 'coverage_pct', 'mean', 'median', 'small_sample']
    if group not in df or df.empty:
        return pd.DataFrame(columns=columns)
    table = df.dropna(subset=[group]).groupby(group, dropna=True)[metric].agg(
        total_posts='size', n='count', mean='mean', median='median').reset_index()
    table['coverage_pct'] = 100 * table.n / table.total_posts
    table['small_sample'] = table.n < min_n
    return table[columns].sort_values('median', ascending=False, na_position='last')


def metric_coverage(df):
    return pd.DataFrame([{'metric': m, 'definition': d, 'valid_posts': int(df[m].notna().sum()),
                          'total_posts': len(df)} for m, d in DEFINITIONS.items()])


def source_coverage(df):
    rows = []
    for (platform, brand), group in df.groupby(['platform', 'brand'], dropna=False):
        row = {'platform': platform, 'brand': brand, 'posts': len(group)}
        for field in ['likes', 'comments', 'views', 'shares', 'reach', 'impressions', 'follower_count']:
            row[field + '_observed'] = int(group[field].notna().sum())
        row['youngest_days'] = group.age_days_at_snapshot.min()
        row['oldest_days'] = group.age_days_at_snapshot.max()
        rows.append(row)
    return pd.DataFrame(rows)
