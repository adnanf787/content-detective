"""Timezone conversion is permitted only with explicit evidence."""
import re
import pandas as pd
from pytz.exceptions import InvalidTimeError

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


def parse_timestamp(value, source_timezone='unknown'):
    if pd.isna(value) or not str(value).strip():
        return pd.NaT, pd.NaT, 'missing'
    text = str(value).strip()
    if not re.match(r'^\d{4}-\d{2}-\d{2}(?:$|[T ])', text):
        return pd.NaT, pd.NaT, 'invalid: use ISO YYYY-MM-DD'
    try:
        stamp = pd.Timestamp(text)
        date_only = len(text) == 10
        if date_only and source_timezone and source_timezone.lower() not in {'unknown', 'asia/karachi'}:
            # A source calendar date spans two possible Karachi dates without a clock time.
            # Validate the declared zone, but never invent midnight as a posting hour.
            stamp.tz_localize(source_timezone)
            return stamp, pd.NaT, 'date only; local day uncertain'
        if stamp.tzinfo is None:
            if not source_timezone or source_timezone.lower() == 'unknown':
                return stamp, pd.NaT, 'timezone unknown'
            stamp = stamp.tz_localize(source_timezone, ambiguous='raise', nonexistent='raise')
        local = stamp.tz_convert('Asia/Karachi')
        # A date-only record cannot support an hourly posting-window comparison.
        return stamp, local.tz_localize(None), 'date only' if date_only else 'known'
    except (ValueError, TypeError, KeyError, OverflowError, InvalidTimeError):
        return pd.NaT, pd.NaT, 'invalid timestamp/timezone'


def add_timing(frame, default_timezone='unknown'):
    df = frame.copy()
    rows = [parse_timestamp(row.post_datetime, row.timezone_source if pd.notna(row.timezone_source)
                            else default_timezone) for row in df.itertuples()]
    df['parsed_datetime'] = [str(r[0]) if pd.notna(r[0]) else None for r in rows]
    df['local_datetime'] = pd.to_datetime([r[1] for r in rows])
    df['time_status'] = [r[2] for r in rows]
    df['weekday'] = df['local_datetime'].dt.day_name()
    df['hour'] = df['local_datetime'].dt.hour.where(df['time_status'].eq('known'))
    # Calendar dates remain useful for filtering unknown-zone observations, labeled as source dates.
    df['source_date'] = [str(r[0])[:10] if pd.notna(r[0]) else None for r in rows]
    return df
