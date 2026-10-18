"""One shared pipeline for UI, reports, notebook, and tests."""
import pandas as pd
from src.cleaning import clean_posts
from src.metrics import add_metrics
from src.sentiment import add_sentiment
from src.content_nlp import annotate_posts

QUESTIONS = [
    'Which platform performs better?',
    'Which content type gets more engagement?',
    'What topics and hashtags are popular?',
    'What sentiment is associated with engagement?',
    'What posting time/day appears better?',
    'Which Pakistani audience segment seems more responsive?',
    'What should a Pakistani brand post next?',
]


def prepare(raw, manifest):
    cleaned, quality = clean_posts(raw, manifest)
    return annotate_posts(add_sentiment(add_metrics(cleaned))), quality


def dataset_label(df):
    statuses = set(df.data_status.dropna())
    if not statuses:
        return 'NO ROWS'
    if statuses == {'synthetic'}:
        return 'SYNTHETIC DEMO'
    if 'synthetic' in statuses:
        return 'MIXED DATA: INCLUDES SYNTHETIC'
    if statuses == {'real (declared)'}:
        return 'REAL (USER-DECLARED; NOT INDEPENDENTLY VERIFIED)'
    return 'UNVERIFIED DATA' if len(statuses) == 1 else 'MIXED REAL / UNVERIFIED'


def audience_rows(df, manifest):
    if not manifest.audience_evidence.strip():
        return df.iloc[0:0]
    # Synthetic or unverified observations never establish Pakistani audience findings.
    return df[df.data_status.eq('real (declared)') & df.audience_location.str.strip().str.casefold().eq('pakistan').fillna(False)]


def feasibility(df, metric, manifest, min_n=5):
    from src.metrics import summarize
    measured = df[df[metric].notna()]
    audience = audience_rows(measured, manifest)

    def comparable(field):
        groups = summarize(df, field, metric, min_n)
        return len(groups[(groups.n >= min_n) & (groups.coverage_pct >= 80)]) >= 2

    timed = df[df.time_status.eq('known') & df.weekday.notna() & df.hour.notna()]
    slots = timed.groupby(['weekday', 'hour'])[metric].agg(n='count', total='size')
    repeated_slots = int((slots.n.ge(min_n) & (slots.n / slots.total).ge(.8)).sum()) >= 2

    cases = [
        (measured.platform.notna().any(), comparable('platform'),
         'Requires at least two platforms with valid measurements; rates and raw counts have comparability limits.'),
        (measured.content_type.notna().any(), comparable('content_type'),
         'Content type and valid measurements required; compare sample sizes and coverage.'),
        ((df.caption.notna() | df.hashtags.notna() | df.topic.notna()).any(), False,
         'Observed caption/tag/topic usage only; frequency is not audience popularity.'),
        (measured.sentiment_label.ne('unassessed').any(), False,
         'Caption sentiment only. Supplied labels/baseline accuracy is unverified; available linked comment samples are analyzed separately.'),
        (measured.local_datetime.notna().any(), repeated_slots,
         'Known timezone and at least two repeated day/hour slots with sufficient measurements are required; date-only rows cannot support hours.'),
        (audience.audience_segment.notna().any(), False,
         'Requires documented segment evidence, declared-real data, and explicit Pakistan audience location. Post-level context is not demographic response rate.'),
        (len(measured) > 0, False,
         'Descriptive experiments only; no causal or predictive claim.'),
    ]
    rows = []
    for q, (some, full, reason) in zip(QUESTIONS, cases):
        rows.append({'question': q, 'support': 'Supported' if full else 'Partial' if some else 'Unavailable',
                     'explanation': reason})
    return pd.DataFrame(rows)


def filter_posts(df, selections=None, start=None, end=None):
    work = df[df.analysis_eligible].copy()
    for field, selected in (selections or {}).items():
        work = work[work[field].isin(selected)]
    if start:
        work = work[work.source_date.notna() & work.source_date.ge(str(start))]
    if end:
        work = work[work.source_date.notna() & work.source_date.le(str(end))]
    return work
