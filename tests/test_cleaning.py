import pandas as pd
import pytest
from src.schema import suggest_mapping, apply_mapping
from src.loader import read_csv
from src.analysis import dataset_label, filter_posts


def test_aliases_and_conflicting_mapping():
    raw = pd.DataFrame({'likes_count': ['4'], 'post_timestamp': ['2026-10-01']})
    mapping = suggest_mapping(raw.columns)
    assert set(apply_mapping(raw, mapping)) == {'likes', 'post_datetime'}
    with pytest.raises(ValueError, match='two canonical'):
        apply_mapping(raw, {'likes': 'likes_count', 'shares': 'likes_count'})


def test_invalid_metrics_preserve_original_and_report(build):
    df, q, _ = build([{'post_id': str(i), 'likes': value}
                      for i, value in enumerate(['bad', '-2', 'inf', '1.5', '', '2000000'])])
    assert q['invalid_counts']['likes'] == 4
    assert df.likes.iloc[:5].isna().all()
    assert df.likes.iloc[5] == 2000000
    assert df.likes_original.iloc[0] == 'bad'


def test_identical_vs_conflicting_duplicate_handling(build):
    rows = [{'post_id': 'a', 'source_name': 'export', 'platform': 'Instagram', 'likes': 10}]
    df, q, _ = build([rows[0], rows[0], {**rows[0], 'likes': 12}])
    assert q['exact_duplicates_removed'] == 1
    assert q['conflicting_rows_excluded'] == 2
    assert len(df) == 2 and not df.analysis_eligible.any()
    assert filter_posts(df).empty


def test_platform_and_account_namespace_prevents_false_duplicate(build):
    df, q, _ = build([{'post_id': '1', 'brand': 'A', 'platform': 'IG'},
                      {'post_id': '1', 'brand': 'B', 'platform': 'IG'},
                      {'post_id': '1', 'brand': 'A', 'platform': 'FB'}])
    assert q['conflicting_rows_excluded'] == 0
    assert set(df.platform) == {'Instagram', 'Facebook'}


def test_unknown_synthetic_status_never_becomes_real(build):
    df, _, _ = build([{'caption': 'hello'}])
    assert pd.isna(df.is_synthetic.iloc[0])
    assert dataset_label(df) == 'UNVERIFIED DATA'


def test_synthetic_flag_overrides_real_manifest(build):
    df, _, _ = build([{'is_synthetic': 'true'}], status='real')
    assert dataset_label(df) == 'SYNTHETIC DEMO'


def test_synthetic_source_overrides_false_flag(build):
    df, _, _ = build([{'is_synthetic': 'false', 'source_type': 'synthetic'}])
    assert df.data_status.iloc[0] == 'synthetic'


def test_utf8_roundtrip_and_empty_errors():
    df = read_csv('caption,likes\n"پاکستان 🇵🇰",\n'.encode())
    assert df.caption.iloc[0] == 'پاکستان 🇵🇰'
    assert df.likes.iloc[0] == ''
    with pytest.raises(ValueError):
        read_csv(b'')
    with pytest.raises(ValueError, match='no post records'):
        read_csv(b'caption,likes\n')


def test_filters_and_date_exclusions(build):
    df, _, _ = build([{'post_id': '1', 'platform': 'IG', 'post_datetime': '2026-10-01'},
                      {'post_id': '2', 'platform': 'FB'},
                      {'post_id': '3', 'platform': 'IG', 'post_datetime': '2026-10-03'}])
    assert len(filter_posts(df, {'platform': ['Instagram']})) == 2
    assert len(filter_posts(df, start='2026-10-02')) == 1
    assert filter_posts(df, {'platform': []}).empty


def test_preserves_original_caption_whitespace(build):
    df, _, _ = build([{'caption': '  پاکستان 🇵🇰  '}])
    assert df.caption.iloc[0] == 'پاکستان 🇵🇰'
    assert df.caption_original.iloc[0] == '  پاکستان 🇵🇰  '
