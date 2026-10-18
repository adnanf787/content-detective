"""Stateless web access to the same analysis used by the Streamlit assignment.

The browser sends its workspace with each request. Visitor imports and reviewed
labels never modify the bundled snapshot or another visitor's workspace.
"""
from dataclasses import fields, replace
from datetime import date
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response

from src.analysis import dataset_label, feasibility, filter_posts, prepare
from src.content_nlp import annotate_comments, evaluation_table
from src.insights import (MEASURES, MEASURE_NOTES, analysis_summary, analysis_tables,
                          linked_comments, relative_to_brand)
from src.loader import Manifest, read_csv
from src.metrics import metric_coverage, summarize
from src.recommendations import marketing_prompt, recommend
from src.research_outputs import evidence_bundle
from src.schema import FIELDS, apply_mapping, suggest_mapping
from src.study_data import read_saved_study
from src.youtube_study import COMMENT_COLUMNS, load_config, run_study

ROOT = Path(__file__).resolve().parents[1]
LABEL_FIELDS = {'content_type', 'topic', 'caption_sentiment', 'caption_language', 'creative_angle', 'local_context'}
app = FastAPI(title='Content Detective research API', docs_url=None, redoc_url=None)


@app.middleware('http')
async def bounded_request(request: Request, call_next):
    # Leave room beneath Vercel's request/response payload limit.
    content = await request.body()
    if len(content) > 3_500_000:
        return JSONResponse({'detail': 'Workspace exceeds the hosted 3.5 MB request limit. Import a smaller sample.'}, status_code=413)
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


@app.exception_handler(ValueError)
async def bad_input(request, exc):
    return JSONResponse({'detail': str(exc)}, status_code=400)


def clean(value):
    if isinstance(value, pd.DataFrame):
        return json.loads(value.to_json(orient='records', date_format='iso'))
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [clean(v) for v in value]
    if isinstance(value, np.generic):
        return clean(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, (date, pd.Timestamp)):
        return value.isoformat()
    return value


@lru_cache(maxsize=1)
def saved_workspace():
    raw, comments, manifest, report = read_saved_study(ROOT)
    return clean({'raw': raw, 'comments': comments, 'manifest': manifest.to_dict(), 'collection_report': report})


def workspace(payload):
    source = payload.get('workspace') or saved_workspace()
    if not isinstance(source, dict) or not isinstance(source.get('raw'), list) or not source['raw']:
        raise ValueError('Supply a nonempty post workspace.')
    if len(source['raw']) > 5000 or len(source.get('comments', [])) > 10000:
        raise ValueError('Hosted workspace limit: 5,000 posts and 10,000 sampled comments.')
    raw = pd.DataFrame(source['raw'])
    allowed = {field.name for field in fields(Manifest)}
    manifest = Manifest(**{k: str(v or '') for k, v in source.get('manifest', {}).items() if k in allowed})
    comments = pd.DataFrame(source.get('comments', []))
    if comments.empty:
        comments = pd.DataFrame(columns=COMMENT_COLUMNS)
    else:
        required = {'comment_id', 'platform', 'platform_post_id', 'brand', 'comment_text'}
        if not required.issubset(comments):
            raise ValueError('Comment rows are missing identifiers, source linkage, brand, or text.')
        comments = annotate_comments(comments)
    frame, quality = prepare(raw, manifest)
    return raw, comments, manifest, frame, quality, source


def selected(payload):
    raw, comments, manifest, frame, quality, source = workspace(payload)
    filters = payload.get('filters') or {}
    metric = filters.get('metric', 'visible_per_1000_views')
    if metric not in MEASURES:
        raise ValueError('Choose a supported comparison measure.')
    minimum = int(filters.get('minimum_group_n', 5))
    if not 2 <= minimum <= 100:
        raise ValueError('Minimum group size must be between 2 and 100.')
    brands = filters.get('brands', sorted(frame.brand.dropna().unique().tolist()))
    if not isinstance(brands, list) or any(not isinstance(b, str) for b in brands):
        raise ValueError('Brands must be a list of names.')
    start, end = filters.get('publication_start') or None, filters.get('publication_end') or None
    for value in (start, end):
        if value:
            date.fromisoformat(value)
    if start and end and start > end:
        raise ValueError('Publication start must not follow the end date.')
    df = filter_posts(frame, {'brand': brands}, start, end)
    df = df[df.platform.eq('YouTube')].copy()
    low, high = filters.get('min_age_days'), filters.get('max_age_days')
    if low is not None or high is not None:
        lower, upper = float(low or 0), float(high) if high is not None else float('inf')
        if lower < 0 or lower > upper:
            raise ValueError('Choose a valid nonnegative video-age range.')
        df = df[df.age_days_at_snapshot.between(lower, upper)]
    sample = linked_comments(df, comments)
    active = {**filters, 'brands': brands, 'metric': metric, 'minimum_group_n': minimum, 'platform': 'YouTube'}
    return df, sample, manifest, quality, metric, minimum, active, frame, source


def analyze(payload, *, include_workspace=False):
    df, sample, manifest, quality, metric, minimum, filters, all_df, source = selected(payload)
    mixed = df.data_status.nunique() > 1
    tables = analysis_tables(df, metric, minimum)
    tables.update({field: summarize(df, field, metric, minimum) for field in
                   ['language_inferred', 'caption_language', 'creative_angle', 'local_context', 'content_type', 'sentiment_label']})
    result = {'posts': relative_to_brand(df, metric, minimum), 'comments': sample,
              'tables': tables, 'summary': analysis_summary(df, sample, metric, manifest, minimum),
              'questions': feasibility(df, metric, manifest, minimum), 'quality': quality,
              'manifest': manifest.to_dict(), 'metric_coverage': metric_coverage(df), 'filters': filters,
              'recommendations': recommend(df, metric, manifest, minimum) if len(df) and not mixed else [],
              'available_brands': sorted(all_df[all_df.platform.eq('YouTube')].brand.dropna().unique().tolist()),
              'measures': MEASURES, 'measure_notes': MEASURE_NOTES, 'data_label': dataset_label(df),
              'mixed_tracks': mixed, 'collection_report': source.get('collection_report'),
              'verification': json.loads((ROOT / 'config/brand_verification.json').read_text()),
              'collection_config': load_config()['study']}
    if include_workspace:
        result['workspace'] = source
    return clean(result)


@app.get('/api/health')
def health():
    return {'status': 'ok', 'application': 'content-detective', 'version': 'youtube-dashboard-v1'}


@app.get('/api/study')
def study():
    return analyze({}, include_workspace=True)


@app.get('/api/template')
def template():
    return Response((ROOT / 'data/collection_template.csv').read_bytes(), media_type='text/csv',
                    headers={'Content-Disposition': 'attachment; filename="collection_template.csv"'})


@app.post('/api/analyze')
def analyze_request(payload: dict):
    return analyze(payload)


@app.post('/api/export')
def export(payload: dict):
    df, sample, manifest, quality, metric, minimum, filters, _, _ = selected(payload)
    if df.empty:
        raise ValueError('No videos match the active filters.')
    if df.data_status.nunique() > 1:
        raise ValueError('Export one data-status track at a time; synthetic and empirical rows cannot be pooled.')
    kind = payload.get('format', 'zip')
    if kind == 'posts':
        content, name, mime = relative_to_brand(df, metric, minimum).to_csv(index=False).encode('utf-8-sig'), 'youtube_analyzed_posts.csv', 'text/csv'
    elif kind in ('comments', 'review'):
        table = sample
        if kind == 'review':
            table = sample.reindex(columns=['comment_id', 'brand', 'comment_text', 'language_inferred', 'sentiment_label']).assign(human_label='')
        content, name, mime = table.to_csv(index=False).encode('utf-8-sig'), f'youtube_{kind}.csv', 'text/csv'
    elif kind == 'brief':
        brief = str(payload.get('brief', '')).strip()
        if not brief:
            raise ValueError('Describe the brand and creative objective first.')
        content, name, mime = marketing_prompt(df, metric, manifest, brief[:10000], minimum), 'ai_marketing_brief.md', 'text/markdown'
    elif kind in ('zip', 'report', 'summary'):
        bundle, report, summary = evidence_bundle(df, sample, manifest, quality, metric, minimum, filters)
        content, name, mime = {
            'zip': (bundle, 'youtube_research_evidence.zip', 'application/zip'),
            'report': (report, 'youtube_findings.md', 'text/markdown'),
            'summary': (json.dumps(clean(summary), ensure_ascii=False, indent=2), 'youtube_analysis_summary.json', 'application/json'),
        }[kind]
    else:
        raise ValueError('Choose a supported export format.')
    return Response(content, media_type=mime, headers={'Content-Disposition': f'attachment; filename="{name}"'})


@app.post('/api/labels')
def labels(payload: dict):
    raw, comments, manifest, _, _, source = workspace(payload)
    method = str(payload.get('reviewer', '')).strip()
    if not method:
        raise ValueError('Document the reviewer and codebook before saving labels.')
    edits = payload.get('labels') or []
    if len(edits) != len(raw):
        raise ValueError('Supply labels for every row in the loaded dataset.')
    for field in LABEL_FIELDS:
        raw[field] = [str(row.get(field, '') or '')[:1000] for row in edits]
    manifest = replace(manifest, notes=manifest.notes + '\nContent label review: ' + method[:1000])
    updated = clean({**source, 'raw': raw, 'manifest': manifest.to_dict()})
    return analyze({**payload, 'workspace': updated}, include_workspace=True)


@app.post('/api/evaluate')
def evaluate(payload: dict):
    _, sample, *_ = selected(payload)
    labels = read_csv(str(payload.get('csv', '')).encode('utf-8'))
    if not {'comment_id', 'human_label'}.issubset(labels) or labels.comment_id.duplicated().any():
        raise ValueError('Supply unique comment_id values and a human_label column.')
    if not labels.human_label.isin(['', 'positive', 'neutral', 'negative']).all():
        raise ValueError('Human labels must be positive, neutral, negative, or blank.')
    joined = sample.merge(labels[['comment_id', 'human_label']], on='comment_id', how='inner')
    result = evaluation_table(joined)
    if result:
        result['confusion_matrix'] = result['confusion_matrix'].rename_axis('human_label').reset_index()
    return clean({'evaluation': result})


@app.post('/api/import/preview')
def import_preview(payload: dict):
    raw = read_csv(str(payload.get('csv', '')).encode('utf-8'))
    if len(raw) > 5000:
        raise ValueError('Hosted imports support up to 5,000 posts.')
    return clean({'rows': len(raw), 'columns': raw.columns.tolist(), 'preview': raw.head(5),
                  'mapping': suggest_mapping(raw.columns), 'fields': FIELDS})


@app.post('/api/import')
def import_posts(payload: dict):
    content = str(payload.get('csv', '')).encode('utf-8')
    raw = read_csv(content)
    mapped = apply_mapping(raw, payload.get('mapping') or suggest_mapping(raw.columns))
    manifest_data = {**payload.get('manifest', {}), 'sha256': hashlib.sha256(content).hexdigest()}
    allowed = {field.name for field in fields(Manifest)}
    manifest = Manifest(**{k: str(v or '') for k, v in manifest_data.items() if k in allowed})
    updated = clean({'raw': mapped, 'comments': [], 'manifest': manifest.to_dict()})
    return analyze({'workspace': updated}, include_workspace=True)


@app.post('/api/collect')
def collect(payload: dict):
    # A visitor supplies their own key per request. Never expose a shared owner's
    # quota to anonymous visitors, save a visitor key, or mutate the saved pilot.
    key = str(payload.get('api_key', '')).strip()
    if not key or len(key) > 200:
        raise ValueError('Supply your own YouTube Data API key to collect a fresh snapshot.')
    with TemporaryDirectory(prefix='detective-collection-') as folder:
        root = Path(folder)
        config = load_config()
        posts, comments, report = run_study(root=root, config=config, key=key)
        if not len(posts) or not report['validation']['valid']:
            raise HTTPException(status_code=400, detail='Collection did not return a valid sample. Check your key, quota, and channel availability; the saved pilot is unchanged.')
        _, _, manifest, _ = read_saved_study(root)
        updated = clean({'raw': posts, 'comments': comments, 'manifest': manifest.to_dict(), 'collection_report': report})
    return analyze({'workspace': updated}, include_workspace=True)
