"""Hosted parity checks: shared computations, isolated workspaces, and linked exports."""
from io import BytesIO, StringIO
import csv
import json
import zipfile

import pytest
from fastapi.testclient import TestClient

from api.index import app
from src.analysis import prepare
from src.insights import brand_benchmarks
from src.settings import ROOT
from src.study_data import read_saved_study


@pytest.fixture
def client():
    return TestClient(app)


def test_hosted_saved_pilot_matches_shared_python_analysis_without_network(client, monkeypatch):
    monkeypatch.setattr('requests.sessions.Session.request', lambda *a, **k: pytest.fail('Saved study must stay offline'))
    response = client.get('/api/study')
    assert response.status_code == 200
    data = response.json()
    assert (len(data['posts']), len(data['comments']), data['summary']['brands']) == (30, 279, 3)
    assert data['summary']['comment_cue_counts'] == {'unassessed': 256, 'positive': 14, 'negative': 9}
    assert data['summary']['comment_cues_evaluated'] is False
    assert all(row['shares'] is None for row in data['posts'])
    raw, _, manifest, _ = read_saved_study(ROOT)
    frame, _ = prepare(raw, manifest)
    expected = brand_benchmarks(frame, 'visible_per_1000_views')
    assert {r['brand']: r['median'] for r in data['tables']['brands']} == pytest.approx(dict(zip(expected.brand, expected['median'])))
    assert response.headers['cache-control'] == 'no-store'


def test_filter_and_zip_export_include_only_selected_videos_and_linked_comments(client):
    filters = {'brands': ['Jazz'], 'metric': 'likes', 'minimum_group_n': 5}
    data = client.post('/api/analyze', json={'filters': filters}).json()
    assert len(data['posts']) == 10 and len(data['comments']) == 31
    ids = {r['post_id'] for r in data['posts']}
    assert {r['platform_post_id'] for r in data['comments']} <= ids
    response = client.post('/api/export', json={'filters': filters, 'format': 'zip'})
    assert response.status_code == 200 and 'zip' in response.headers['content-type']
    with zipfile.ZipFile(BytesIO(response.content)) as bundle:
        posts = list(csv.DictReader(StringIO(bundle.read('analyzed_posts.csv').decode())))
        comments = list(csv.DictReader(StringIO(bundle.read('sampled_comments.csv').decode())))
        assert len(posts) == 10 and len(comments) == 31
        assert {r['brand'] for r in posts + comments} == {'Jazz'}
        assert json.loads(bundle.read('filters.json'))['brands'] == ['Jazz']
        assert json.loads(bundle.read('analysis_summary.json'))['metric'] == 'likes'


def test_empty_sample_keeps_management_available_and_blocks_empty_exports(client):
    filters = {'brands': []}
    response = client.post('/api/analyze', json={'filters': filters})
    assert response.status_code == 200
    assert response.json()['posts'] == [] and response.json()['comments'] == []
    assert response.json()['available_brands'] == ['Jazz', 'Ufone', 'Zong']
    assert client.post('/api/export', json={'filters': filters}).status_code == 400


def test_reviewed_labels_recalculate_without_mutating_snapshot_or_measurements(client):
    source = client.get('/api/study').json()
    workspace = source['workspace']
    labels = [{'topic': 'Offer' if i < 15 else 'Service', 'caption_language': 'English'} for i in range(30)]
    request = {'workspace': workspace, 'labels': labels, 'reviewer': 'Reviewer A; codebook v1'}
    response = client.post('/api/labels', json=request)
    assert response.status_code == 200
    reviewed = response.json()
    assert reviewed['summary']['supplied_content_label_counts']['topic'] == 30
    assert [r['likes'] for r in reviewed['posts']] == [r['likes'] for r in source['posts']]
    assert len(reviewed['comments']) == 279
    assert 'Reviewer A' in reviewed['manifest']['notes']
    assert 'human_label' not in reviewed['comments'][0]
    fresh = client.get('/api/study').json()
    assert fresh['summary']['supplied_content_label_counts']['topic'] == 0
    assert 'Reviewer A' not in fresh['manifest']['notes']
    assert client.post('/api/labels', json={**request, 'reviewer': ''}).status_code == 400


def test_evaluation_requires_actual_human_labels_and_rejects_duplicate_ids(client):
    source = client.get('/api/study').json()
    comment_id = source['comments'][0]['comment_id']
    empty = client.post('/api/evaluate', json={'csv': f'comment_id,human_label\n{comment_id},\n'})
    assert empty.json()['evaluation'] is None
    labeled = client.post('/api/evaluate', json={'csv': f'comment_id,human_label\n{comment_id},positive\n'})
    assert labeled.status_code == 200 and labeled.json()['evaluation']['n'] == 1
    bad = client.post('/api/evaluate', json={'csv': f'comment_id,human_label\n{comment_id},positive\n{comment_id},negative\n'})
    assert bad.status_code == 400


def test_import_mapping_preserves_unknown_counts_and_synthetic_status(client):
    content = 'post_id,platform,account,text,likes_count,comment_count,view_count\nfixture,YouTube,Demo,Example caption,5,,100\n'
    preview = client.post('/api/import/preview', json={'csv': content}).json()
    assert preview['mapping']['brand'] == 'account' and preview['mapping']['likes'] == 'likes_count'
    response = client.post('/api/import', json={'csv': content, 'mapping': preview['mapping'],
                                              'manifest': {'status': 'synthetic', 'source_type': 'synthetic', 'source_name': 'Controlled fixture'}})
    assert response.status_code == 200
    data = response.json()
    assert data['posts'][0]['comments'] is None and data['posts'][0]['visible_interactions'] is None
    assert data['posts'][0]['data_status'] == 'synthetic'
    assert data['comments'] == [] and data['collection_report'] is None
    assert len(client.get('/api/study').json()['posts']) == 30


@pytest.mark.parametrize('filters', [
    {'metric': 'invented_virality_score'}, {'minimum_group_n': 0},
    {'publication_start': '2026-10-02', 'publication_end': '2026-01-01'},
    {'min_age_days': 100, 'max_age_days': 50}, {'brands': 'Jazz'},
])
def test_invalid_filter_inputs_have_actionable_errors(client, filters):
    assert client.post('/api/analyze', json={'filters': filters}).status_code == 400


def test_hosted_collection_does_not_spend_shared_credentials(client, monkeypatch):
    monkeypatch.setenv('YOUTUBE_API_KEY', 'owner-secret-must-not-be-used')
    monkeypatch.setattr('requests.sessions.Session.request', lambda *a, **k: pytest.fail('No supplied visitor key'))
    response = client.post('/api/collect', json={})
    assert response.status_code == 400
    assert 'owner-secret' not in response.text


def test_brief_uses_active_evidence_and_has_no_model_call(client):
    response = client.post('/api/export', json={'filters': {'brands': ['Ufone']}, 'format': 'brief', 'brief': 'Test an Urdu product explanation'})
    assert response.status_code == 200
    assert 'Test an Urdu product explanation' in response.text and 'Active posts: 10' in response.text
    assert 'Human review is required' in response.text
