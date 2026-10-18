import math
import pandas as pd
from src.metrics import choose_metric, summarize


def test_missing_shares_are_never_zero(build):
    df, _, _ = build([{'likes': 10, 'comments': 2, 'impressions': 100}])
    row = df.iloc[0]
    assert pd.isna(row.shares)
    assert row.available_interactions == 12
    assert row.observed_components == 'likes, comments'
    assert row.visible_interactions == 12
    assert pd.isna(row.complete_interactions)
    assert pd.isna(row.rate_impressions)
    assert choose_metric(df).name == 'visible_interactions'


def test_all_absent_interactions_remain_unknown(build):
    df, _, _ = build([{'post_id': 'a', 'impressions': 500}])
    assert pd.isna(df.iloc[0].available_interactions)
    assert not df.rate_impressions.notna().any()


def test_rate_denominators_require_positive_and_complete_counts(build):
    rows = [{'post_id': str(i), 'likes': 10, 'comments': 3, 'shares': 2, 'impressions': v}
            for i, v in enumerate([100, 0, None, -10])]
    df, q, _ = build(rows)
    assert df.rate_impressions.iloc[0] == 15
    assert df.rate_impressions.iloc[1:].isna().all()
    assert q['invalid_counts']['impressions'] == 1


def test_valid_observed_zero_counts_are_preserved(build):
    df, _, _ = build([{'likes': 0, 'comments': 0, 'shares': 0, 'reach': 20}])
    assert df.complete_interactions.iloc[0] == 0
    assert df.rate_reach.iloc[0] == 0


def test_group_mean_median_and_coverage(build):
    df, _, _ = build([{'post_id': str(i), 'platform': 'IG', 'likes': n}
                      for i, n in enumerate([1, 2, 100, None])])
    row = summarize(df, 'platform', 'likes').iloc[0]
    assert row.n == 3 and row.total_posts == 4
    assert row['mean'] == 103 / 3 and row['median'] == 2
    assert row.coverage_pct == 75 and bool(row.small_sample)


def test_rate_overflow_is_not_ranked(build):
    df, _, _ = build([{'likes': '1e308', 'comments': 0, 'shares': 0, 'impressions': 1}])
    assert not math.isinf(df.rate_impressions.iloc[0])


def test_visible_per_view_metric_uses_two_observed_components(build):
    df, _, _ = build([{'post_id': str(i), 'likes': likes, 'comments': comments, 'views': views}
                      for i, (likes, comments, views) in enumerate([(20, 5, 1000), (0, 0, 100), (20, None, 100), (20, 5, 0)])])
    assert df.visible_per_1000_views.iloc[:2].tolist() == [25, 0]
    assert df.visible_per_1000_views.iloc[2:].isna().all()
    assert df.complete_interactions.isna().all()


def test_follower_proxy_and_post_age_require_observed_inputs(build):
    df, _, _ = build([{'post_id': 'known', 'likes': 20, 'comments': 5, 'follower_count': 1000,
                      'post_datetime': '2026-06-01T10:00:00+05:00', 'collection_datetime': '2026-06-11T05:00:00Z'},
                     {'post_id': 'missing', 'likes': 20, 'comments': 5, 'post_datetime': '2026-06-01T10:00:00',
                      'collection_datetime': '2026-06-11T05:00:00Z'}])
    assert df.visible_rate_followers.iloc[0] == 2.5
    assert df.age_days_at_snapshot.iloc[0] == 10
    assert pd.isna(df.visible_rate_followers.iloc[1]) and pd.isna(df.age_days_at_snapshot.iloc[1])
