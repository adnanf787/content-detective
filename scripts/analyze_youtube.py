"""Reproduce Phase 3 from the saved real snapshot; no API key or network needed."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.analysis import prepare
from src.insights import analysis_tables, relative_to_brand
from src.metrics import choose_metric
from src.research_outputs import evidence_bundle
from src.study_data import read_saved_study


def main():
    raw, comments, manifest, _ = read_saved_study(ROOT)
    frame, quality = prepare(raw, manifest)
    frame = frame[frame.analysis_eligible].copy()
    metric = choose_metric(frame).name
    bundle, report, summary = evidence_bundle(frame, comments, manifest, quality, metric)
    out = ROOT / 'data/processed'
    relative_to_brand(frame, metric).to_csv(out / 'youtube_analysis_posts.csv', index=False, encoding='utf-8-sig')
    for name, table in analysis_tables(frame, metric).items():
        table.to_csv(out / ('youtube_analysis_' + name + '.csv'), index=False, encoding='utf-8-sig')
    (out / 'youtube_analysis_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
    (out / 'youtube_phase3_report.md').write_text(report)
    (out / 'youtube_phase3_evidence.zip').write_bytes(bundle)
    print(f'Phase 3 analyzed {len(frame)} real videos and {summary["comments_sampled"]} linked comments using {metric}.')
    print('Outputs saved under data/processed/. No API calls were made.')


if __name__ == '__main__':
    main()
