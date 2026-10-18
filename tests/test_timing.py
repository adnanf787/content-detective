import pandas as pd
from src.timing import parse_timestamp


def test_unknown_zone_is_not_assumed_karachi(build):
    df, _, _ = build([{'post_datetime': '2026-10-01T19:00:00'}])
    assert df.time_status.iloc[0] == 'timezone unknown'
    assert pd.isna(df.hour.iloc[0]) and pd.isna(df.weekday.iloc[0])
    assert df.source_date.iloc[0] == '2026-10-01'


def test_known_offset_converts_across_day_boundary(build):
    df, _, _ = build([{'post_datetime': '2026-10-01T22:00:00Z'}])
    assert df.hour.iloc[0] == 3
    assert df.weekday.iloc[0] == 'Friday'


def test_declared_timezone_and_date_only(build):
    df, _, _ = build([{'post_id': '1', 'post_datetime': '2026-10-01T18:00:00'},
                      {'post_id': '2', 'post_datetime': '2026-10-01'}], source_timezone='Asia/Karachi')
    assert df.hour.iloc[0] == 18
    assert df.time_status.iloc[1] == 'date only'
    assert pd.isna(df.hour.iloc[1])
    assert df.weekday.iloc[1] == 'Thursday'


def test_ambiguous_or_invalid_dates_are_flagged(build):
    df, q, _ = build([{'post_id': '1', 'post_datetime': '10/11/2026'},
                      {'post_id': '2', 'post_datetime': '2026-02-30'},
                      {'post_id': '3', 'post_datetime': '2026-10-01T12:00:00', 'timezone_source': 'Not/AZone'}])
    assert q['invalid_timestamps'] == 3
    assert df.local_datetime.isna().all()


def test_dst_ambiguous_and_nonexistent_local_times_do_not_crash(build):
    df, quality, _ = build([{'post_id': '1', 'post_datetime': '2026-11-01T01:30:00'},
                            {'post_id': '2', 'post_datetime': '2026-03-08T02:30:00'}],
                           source_timezone='America/New_York')
    assert quality['invalid_timestamps'] == 2
    assert df.local_datetime.isna().all()


def test_foreign_date_without_hour_cannot_establish_karachi_weekday(build):
    df, _, _ = build([{'post_datetime': '2026-10-01'}], source_timezone='UTC')
    assert df.time_status.iloc[0] == 'date only; local day uncertain'
    assert pd.isna(df.weekday.iloc[0]) and pd.isna(df.hour.iloc[0])
