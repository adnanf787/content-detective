"""Portable exports containing provenance, caveats, all seven questions and evidence."""
import json
from src.analysis import QUESTIONS, feasibility, dataset_label, audience_rows
from src.metrics import summarize, metric_coverage, DEFINITIONS, source_coverage
from src.hashtags import hashtag_table
from src.recommendations import date_range, recommend

LIMITATIONS = [
    'Pakistani accounts are a Pakistan-market proxy, not proof of Pakistani viewers. Audience geography requires independent evidence.',
    'Missing measurements are not zero. Complete-interaction rates require likes, comments, and shares. Visible interactions per 1,000 views require likes, comments, and positive views, and exclude shares.',
    'Cross-platform raw counts and differently defined rates are not directly comparable. Means can be driven by outliers; inspect medians, coverage, group dates, and n.',
    'Caption sentiment is separate from the downloaded YouTube comment sample. Caption/comment cue lexicons and language/category rules are unevaluated; no multilingual accuracy or audience-wide sentiment is established.',
    'Timing uses Asia/Karachi only when a source timezone/offset is known. Unknown-zone records and date-only hours are excluded.',
    'Associations are observational, potentially confounded by account size, campaign spend, post age, and paid promotion. No causation or statistical confidence is claimed.',
    'Conflicting source/account/post IDs are retained in cleaned exports but excluded from analysis. Local generated IDs are row references, not verified source IDs.',
]


def summary_tables(df, metric, manifest, min_n=5):
    tables = {field: summarize(df, field, metric, min_n) for field in ['platform', 'content_type', 'topic', 'weekday', 'hour', 'caption_language', 'local_context', 'creative_angle', 'language_inferred', 'category_suggested']}
    tables['hashtags'] = hashtag_table(df, metric, min_n)
    tables['sentiment_label'] = summarize(df[df.sentiment_label.ne('unassessed')], 'sentiment_label', metric, min_n)
    tables['audience_segment'] = summarize(audience_rows(df, manifest), 'audience_segment', metric, min_n)
    tables['source_coverage'] = source_coverage(df)
    for field in ['platform', 'content_type']:
        ranges = df.dropna(subset=[field, 'source_date']).groupby(field).source_date.agg(first_date='min', last_date='max').reset_index()
        tables[field] = tables[field].merge(ranges, on=field, how='left')
    return tables


def table_text(table):
    # Avoid a separate tabulate dependency and preserve Unicode.
    return '```csv\n' + table.to_csv(index=False).strip() + '\n```'


def executive_summary(df, metric, manifest, min_n=5):
    tables = summary_tables(df, metric, manifest, min_n)
    keys = ['platform', 'content_type', 'hashtags', 'sentiment_label', 'weekday', 'audience_segment']
    support = feasibility(df, metric, manifest, min_n)
    answers = []
    for i, key in enumerate(keys):
        status = support.iloc[i]
        table = tables[key]
        valid = table[(table.n >= min_n) & table['median'].notna() & (table.coverage_pct >= 80)]
        if status.support == 'Unavailable':
            answer = 'Not answerable with the current data.'
        elif key == 'hashtags':
            frequent = table.sort_values('total_posts', ascending=False)
            answer = (f'Most frequently used observed hashtag: {frequent.iloc[0]["hashtag"]} '
                      f'({int(frequent.iloc[0].total_posts)} posts). Usage is not audience popularity.') if len(frequent) else 'No Unicode hashtags found; inspect supplied topic groups instead.'
        elif len(valid):
            row = valid.iloc[0]
            answer = f'Highest eligible observed median: {row[key]} ({row["median"]:.2f} {metric}; n={int(row.n)}/{int(row.total_posts)}).'
            if len(valid) < 2:
                answer += ' Only one eligible group: a comparative winner cannot be established.'
        else:
            answer = f'Insufficient groups with n ≥ {min_n} and ≥80% metric coverage for a stable comparison.'
        answers.append(f'### {i+1}. {QUESTIONS[i]}\n{status.support}: {answer} {status.explanation}')
    answers.append(f'### 7. {QUESTIONS[6]}\nPropose a controlled content experiment from the evidence below; collect more data when comparisons are insufficient.')
    return '\n\n'.join(answers)


def markdown_report(df, quality, metric, manifest, min_n=5, filters=None, comments=None):
    pieces = ['# Pakistani Social Media Content Detective', f'**{dataset_label(df)}**',
              'All findings below apply to the active filtered data. Synthetic findings are demonstrations only.',
              f'Posts: {len(df)} | {date_range(df)}',
              '## Provenance manifest', '```json\n' + json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2) + '\n```',
              '## Active filters', '```json\n' + json.dumps(filters or {}, default=str, ensure_ascii=False, indent=2) + '\n```',
              f'## Primary metric\n{metric}: {DEFINITIONS[metric]}. Minimum group n={min_n}. Rankings use medians and ≥80% coverage.',
              '## Executive summary', executive_summary(df, metric, manifest, min_n),
              '## Data quality (whole imported file)', '```json\n' + json.dumps(quality, ensure_ascii=False, indent=2) + '\n```',
              '## Metric coverage (active data)', table_text(metric_coverage(df)), '## Question support',
              table_text(feasibility(df, metric, manifest, min_n)), '## Computed tables']
    for name, table in summary_tables(df, metric, manifest, min_n).items():
        pieces += [f'### {name}', table_text(table)]
    if comments is not None and not comments.empty:
        keys = set(zip(df.platform.astype(str), df.post_id.astype(str)))
        sample = comments[[(str(p), str(i)) in keys for p, i in zip(comments.platform, comments.platform_post_id)]]
        counts = sample.groupby(['brand', 'sentiment_label']).size().reset_index(name='sampled_comments')
        pieces += ['## Downloaded public-comment sample',
                   f'{len(sample)} linked top-level comments; {int(sample.sentiment_label.ne("unassessed").sum())} have exploratory cue labels. '
                   'Recent capped sampling, no replies or author-profile fields. This is separate from caption tone and not representative audience sentiment. '
                   'Multilingual cue rules are unevaluated. Confidence and human-label evaluation scores are unavailable.', table_text(counts)]
    pieces += ['## Offline recommendation studio']
    for card in recommend(df, metric, manifest, min_n):
        pieces += [f'### {card["kind"]}', card['action'], f'Evidence: {card["evidence"]}',
                   f'Confidence: {card["confidence"]}. Limitations: {card["limitations"]}']
        for example in card.get('examples', []):
            pieces.append(f'Source example for {example["group"]}: [{example["post_id"]}]({example["url"]}) '
                          f'— observed {metric}={example["value"]:.2f}. This example is not the group median unless its value matches.')
    pieces += ['## Methodology and limitations', *['- ' + note for note in LIMITATIONS]]
    return '\n\n'.join(pieces)
