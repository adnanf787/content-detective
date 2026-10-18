"""Phase 3 summaries shared by the dashboard, command-line analysis, and evidence exports."""
import pandas as pd

from src.analysis import feasibility
from src.hashtags import hashtag_table
from src.metrics import DEFINITIONS, summarize, source_coverage

MEASURES = {
    'visible_per_1000_views': 'Interactions / 1,000 views',
    'visible_interactions': 'Public interactions',
    'visible_rate_followers': 'Interactions / followers (%)',
    'likes': 'Likes', 'comments': 'Total comments',
}
MEASURE_NOTES = {
    'visible_per_1000_views': 'Likes + comments for every 1,000 observed views. Shares are excluded.',
    'visible_interactions': 'Observed likes + total comments. Both counts must be available.',
    'visible_rate_followers': 'Likes + comments as a share of the follower snapshot. This is a size proxy, not a reach rate.',
    'likes': 'Observed public likes only.', 'comments': 'Observed total comment count, including comments outside the downloaded sample.',
}


def age_comparability(df):
    ranges = df.dropna(subset=['brand', 'age_days_at_snapshot']).groupby('brand').age_days_at_snapshot.agg(
        youngest_days='min', oldest_days='max', known_posts='count').reset_index()
    low = float(ranges.youngest_days.max()) if len(ranges) else None
    high = float(ranges.oldest_days.min()) if len(ranges) else None
    comparable = len(ranges) >= 2 and low <= high
    return {'brands_with_known_ages': len(ranges), 'known_posts': int(ranges.known_posts.sum()),
            'shared_age_range_exists': comparable,
            'shared_min_days': low if comparable else None, 'shared_max_days': high if comparable else None,
            'ranges': ranges}


def brand_benchmarks(df, metric, min_n=5):
    summary = summarize(df, 'brand', metric, min_n)
    if summary.empty:
        return summary
    ranges = age_comparability(df)['ranges']
    summary = summary.merge(ranges, on='brand', how='left')
    summary['eligible_comparison'] = summary.n.ge(min_n) & summary.coverage_pct.ge(80)
    return summary


def relative_to_brand(df, metric, min_n=5):
    """A descriptive index within an account; no predicted views or causal uplift."""
    frame = df.copy()
    groups = frame.groupby(['platform', 'brand'])[metric]
    medians = groups.transform('median')
    counts = groups.transform('count')
    coverage = counts / groups.transform('size')
    frame['brand_relative_index'] = (frame[metric] / medians.where(medians.gt(0))).where(counts.ge(min_n) & coverage.ge(.8))
    return frame


def posting_cells(df, metric, min_n=5):
    timed = df[df.time_status.eq('known') & df.hour.notna() & df.weekday.notna()].copy()
    if timed.empty:
        return pd.DataFrame(columns=['weekday', 'hour', 'videos', 'n', 'median', 'coverage_pct', 'eligible'])
    cells = timed.groupby(['weekday', 'hour'])[metric].agg(videos='size', n='count', median='median').reset_index()
    cells['coverage_pct'] = 100 * cells.n / cells.videos
    cells['eligible'] = cells.n.ge(min_n) & cells.coverage_pct.ge(80)
    return cells


def linked_comments(df, comments):
    if comments is None or comments.empty:
        return pd.DataFrame(columns=[] if comments is None else comments.columns)
    real = df[df.data_status.eq('real (declared)')]
    keys = set(zip(real.platform.astype(str), real.post_id.astype(str)))
    mask = [(str(p), str(i)) in keys for p, i in zip(comments.platform, comments.platform_post_id)]
    return comments[mask].copy()


def analysis_summary(df, comments, metric, manifest, min_n=5):
    sample = linked_comments(df, comments)
    ages = age_comparability(df)
    labels = sample.sentiment_label.value_counts().to_dict() if len(sample) else {}
    return {
        'scope': 'YouTube only; no Instagram comparison', 'posts': len(df), 'brands': int(df.brand.nunique()),
        'platforms': sorted(df.platform.dropna().unique().tolist()), 'comments_sampled': len(sample),
        'metric': metric, 'definition': DEFINITIONS[metric], 'valid_metric_posts': int(df[metric].notna().sum()),
        'minimum_group_n': min_n, 'minimum_group_coverage_pct': 80,
        'age_comparability': {k: v for k, v in ages.items() if k != 'ranges'},
        'comment_cue_counts': {str(k): int(v) for k, v in labels.items()},
        'comment_cues_evaluated': False,
        'supplied_content_label_counts': {f: int(df[f].notna().sum()) for f in ['topic', 'caption_language', 'creative_angle', 'local_context']},
        'question_support': feasibility(df, metric, manifest, min_n).to_dict('records'),
        'limitations': ['A convenience sample of Pakistan-relevant brand posts, not verified Pakistani viewers.',
                        'Video age, paid exposure, account size, and campaigns can confound comparisons.',
                        'Category/language/comment-sentiment rules are unevaluated review suggestions.',
                        'Unavailable reach, impressions, shares, saves, and demographics remain unknown.'],
    }


def analysis_tables(df, metric, min_n=5):
    return {'brands': brand_benchmarks(df, metric, min_n), 'source_coverage': source_coverage(df),
            'hashtags': hashtag_table(df, metric, min_n), 'posting_cells': posting_cells(df, metric, min_n),
            'suggested_categories': summarize(df, 'category_suggested', metric, min_n),
            'suggested_languages': summarize(df, 'language_inferred', metric, min_n),
            'reviewed_topics': summarize(df, 'topic', metric, min_n)}
