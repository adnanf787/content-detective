"""Run: .venv/bin/python scripts/collect_youtube.py [--resume RUN_ID]."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.youtube_study import run_study


def main():
    parser = argparse.ArgumentParser(description='Collect the verified Pakistan telecom YouTube pilot.')
    parser.add_argument('--resume', help='Reuse a snapshot and its successful raw-response cache.')
    args = parser.parse_args()
    try:
        posts, comments, report = run_study(run_id=args.resume, progress=lambda value: print(value, flush=True))
    except ValueError:
        print('Cannot start: check local YOUTUBE_API_KEY, brand configuration, and resume ID. No credentials printed.')
        return 1
    print(f'Run: {report["run_id"]}; status: {report["status"]}; posts: {len(posts)}; comments: {len(comments)}; API errors: {len(report["api_errors"])}; validation: {report["validation"]["valid"]}')
    if len(posts) and report['validation']['valid']:
        print('Exports: data/processed/youtube_posts.csv and data/processed/youtube_comments.csv')
    else:
        print('No validated dataset published. See the run summary under data/raw/<run_id>/.')
    return 0 if report['status'].startswith('complete') else 1


if __name__ == '__main__':
    raise SystemExit(main())
