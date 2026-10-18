from io import BytesIO
import json
import zipfile

import pandas as pd
import pytest

from src.insights import age_comparability, linked_comments, posting_cells, relative_to_brand
from src.analysis import feasibility
from src.research_outputs import evidence_bundle


def test_brand_relative_index_is_descriptive_and_requires_supported_groups(build):
    frame, _, _ = build([{'post_id': str(i), 'platform': 'YouTube', 'brand': 'A', 'likes': i} for i in range(1, 6)])
    assert relative_to_brand(frame, 'likes').brand_relative_index.tolist() == pytest.approx([1/3, 2/3, 1, 4/3, 5/3])
    assert relative_to_brand(frame.iloc[:3], 'likes').brand_relative_index.isna().all()
    zero, _, _ = build([{'post_id': str(i), 'brand': 'A', 'likes': 0} for i in range(5)])
    assert relative_to_brand(zero, 'likes').brand_relative_index.isna().all()


def test_age_comparability_does_not_claim_overlap_when_ranges_differ(build):
    frame, _, _ = build([{'post_id': 'a', 'brand': 'A', 'post_datetime': '2026-09-01T00:00:00Z', 'collection_datetime': '2026-10-01T00:00:00Z'},
                          {'post_id': 'b', 'brand': 'B', 'post_datetime': '2026-06-01T00:00:00Z', 'collection_datetime': '2026-10-01T00:00:00Z'}])
    ages = age_comparability(frame)
    assert not ages['shared_age_range_exists'] and ages['shared_min_days'] is None
    assert ages['known_posts'] == 2


def test_posting_cells_do_not_recommend_sparse_or_unknown_times(build):
    frame, _, _ = build([{'post_id': str(i), 'post_datetime': '2026-06-01T12:00:00Z', 'likes': 10} for i in range(4)] +
                         [{'post_id': 'unknown', 'post_datetime': '2026-06-01T12:00:00', 'likes': 100}])
    cells = posting_cells(frame, 'likes')
    assert cells.videos.sum() == 4 and not cells.eligible.any()
    # Marginal day/hour totals can be large while every joint slot is sparse.
    grid, _, manifest = build([{'post_id': f'{day}-{hour}-{i}', 'post_datetime': f'2026-06-{day:02}T{hour:02}:00:00Z', 'likes': 10}
                               for day in [1, 2, 3] for hour in [9, 10, 11] for i in range(3)])
    assert feasibility(grid, 'likes', manifest).iloc[4].support == 'Partial'


def test_bundle_and_summary_preserve_real_comment_linkage_and_filters(build):
    frame, quality, manifest = build([{'post_id': 'a', 'brand': 'A', 'platform': 'YouTube', 'likes': 10}], status='real')
    comments = pd.DataFrame({'comment_id': ['c1', 'c2'], 'platform': ['YouTube', 'YouTube'], 'platform_post_id': ['a', 'other'],
                             'brand': ['A', 'B'], 'sentiment_label': ['unassessed', 'positive']})
    selected = linked_comments(frame, comments)
    assert selected.comment_id.tolist() == ['c1']
    bundle, report, summary = evidence_bundle(frame, comments, manifest, quality, 'likes', filters={'brands': ['A']})
    assert summary['comments_sampled'] == 1 and summary['comment_cue_counts'] == {'unassessed': 1}
    assert not summary['comment_cues_evaluated']
    with zipfile.ZipFile(BytesIO(bundle)) as archive:
        assert json.loads(archive.read('filters.json')) == {'brands': ['A']}
        assert 'c2' not in archive.read('sampled_comments.csv').decode()
        assert 'analyzed_posts.csv' in archive.namelist()
    assert '1 linked top-level comments' in report
