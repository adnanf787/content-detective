"""Portable Phase 3 evidence bundle; no credentials or live requests."""
from io import BytesIO
import json
import zipfile

from src.insights import analysis_summary, analysis_tables, linked_comments, relative_to_brand
from src.reporting import markdown_report


def evidence_bundle(df, comments, manifest, quality, metric, min_n=5, filters=None):
    sample = linked_comments(df, comments)
    report = markdown_report(df, quality, metric, manifest, min_n, filters, comments=sample)
    summary = analysis_summary(df, sample, metric, manifest, min_n)
    ages = summary['age_comparability']
    caution = ('Brand video-age ranges do not overlap; brand medians are descriptive and cannot isolate a brand effect.'
               if summary['brands'] > 1 and not ages['shared_age_range_exists']
               else 'Different video ages and promotion histories can confound the observed medians.')
    context = ('## Snapshot comparability\n\n' + caution + '\n\n'
               'Day/hour engagement comparisons require repeated slots, not merely separate day and hour totals. '
               'Comment cue counts are unevaluated and are separate from the caption-tone comparison below.\n\n')
    report = report.replace('## Provenance manifest', context + '## Provenance manifest', 1)
    output = BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr('findings.md', report)
        bundle.writestr('analysis_summary.json', json.dumps(summary, ensure_ascii=False, indent=2, default=str))
        bundle.writestr('manifest.json', json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2))
        bundle.writestr('filters.json', json.dumps(filters or {}, ensure_ascii=False, indent=2, default=str))
        bundle.writestr('quality.json', json.dumps(quality, ensure_ascii=False, indent=2))
        bundle.writestr('analyzed_posts.csv', relative_to_brand(df, metric, min_n).to_csv(index=False))
        if not sample.empty:
            bundle.writestr('sampled_comments.csv', sample.to_csv(index=False))
        for name, table in analysis_tables(df, metric, min_n).items():
            bundle.writestr('tables/' + name + '.csv', table.to_csv(index=False))
    return output.getvalue(), report, summary
