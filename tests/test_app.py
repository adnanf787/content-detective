from pathlib import Path
import json

import pandas as pd
from streamlit.testing.v1 import AppTest

from src.analysis import prepare
from src.content_nlp import annotate_comments
from src.loader import Manifest

APP = str(Path(__file__).resolve().parents[1] / 'app.py')
NAV = ['Overview', 'Content', 'Comments', 'Recommendations', 'Data & methods']


def fixture_rows():
    return pd.DataFrame([{'post_id': f'testvideo{i:02}', 'platform': 'YouTube', 'brand': 'Brand A' if i < 5 else 'Brand B',
                          'source_url': f'https://www.youtube.com/watch?v=testvideo{i:02}', 'source_type': 'official_api',
                          'title': f'Fixture video {i}', 'caption': 'New offer #Pakistan', 'likes': 20 + i,
                          'comments': 5, 'views': 1000, 'follower_count': 1000,
                          'post_datetime': '2026-06-01T10:00:00Z', 'collection_datetime': '2026-10-01T10:00:00Z'}
                         for i in range(10)])


def fixture_comments():
    return annotate_comments(pd.DataFrame([{'comment_id': f'comment-{i}', 'platform': 'YouTube', 'platform_post_id': f'testvideo{i:02}',
                                             'brand': 'Brand A', 'comment_text': 'Great service thanks' if i == 0 else 'example words',
                                             'published_at_utc': '2026-06-02T10:00:00Z', 'collected_at_utc': '2026-10-01T10:00:00Z'} for i in range(4)]))


def seed_app(tmp_path, monkeypatch, *, incomplete=False):
    monkeypatch.setattr('src.dashboard.ROOT', tmp_path)
    raw = fixture_rows() if not incomplete else pd.DataFrame({'platform': ['YouTube'], 'caption': ['پاکستان']})
    manifest = Manifest(status='real', source_type='official_api')
    frame, quality = prepare(raw, manifest)
    at = AppTest.from_file(APP, default_timeout=20)
    for key, value in {'dataset': frame, 'raw_dataset': raw, 'quality': quality, 'manifest': manifest, 'dataset_version': 1}.items():
        at.session_state[key] = value
    at.session_state['comments_dataset'] = fixture_comments()
    return at.run()


def test_saved_real_study_auto_loads_offline(tmp_path, monkeypatch):
    monkeypatch.setattr('src.dashboard.ROOT', tmp_path)
    folder = tmp_path / 'data/processed'
    folder.mkdir(parents=True)
    fixture_rows().to_csv(folder / 'youtube_posts.csv', index=False)
    fixture_comments().to_csv(folder / 'youtube_comments.csv', index=False)
    (folder / 'youtube_collection_report.json').write_text(json.dumps({'ended_at_utc': '2026-10-01T10:00:00Z',
                                                                    'sampling_method': 'Controlled test fixture', 'limitations': 'Not real research'}))
    at = AppTest.from_file(APP, default_timeout=20).run()
    assert not at.exception
    assert at.radio[0].options == NAV
    assert [metric.value for metric in at.metric] == ['10', '4', '2', '100%']
    assert not any('synthetic demo' in button.label.lower() for button in at.button)


def test_five_sections_filters_and_management_with_empty_sample(tmp_path, monkeypatch):
    at = seed_app(tmp_path, monkeypatch)
    assert not at.exception
    for page in NAV:
        at.radio[0].set_value(page).run()
        assert not at.exception, (page, [e.message for e in at.exception])
    next(button for button in at.button if button.label == 'Export research').click().run()
    assert at.radio[0].value == 'Data & methods' and at.radio[1].value == 'Export'
    at.radio[0].set_value('Content').run()
    next(widget for widget in at.text_input if widget.label == 'Search title or caption').set_value('Fixture video 3').run()
    inspect = next(widget for widget in at.selectbox if widget.label == 'Inspect a video')
    assert inspect.options == ['Fixture video 3']
    at.radio[0].set_value('Overview').run()
    at.multiselect[0].set_value(['Brand A']).run()
    assert at.metric[0].value == '5'
    at.multiselect[0].set_value([]).run()
    assert any('No YouTube videos match' in item.value for item in at.info)
    at.radio[0].set_value('Data & methods').run()
    assert not at.exception
    assert any(header.value == 'Current study' for header in at.subheader)


def test_incomplete_observations_do_not_break_any_section(tmp_path, monkeypatch):
    at = seed_app(tmp_path, monkeypatch, incomplete=True)
    for page in NAV:
        at.radio[0].set_value(page).run()
        assert not at.exception, (page, [e.message for e in at.exception])


def test_review_call_to_action_and_annotation_preserve_observations(tmp_path, monkeypatch):
    at = seed_app(tmp_path, monkeypatch)
    next(button for button in at.button if button.label == 'Review content labels').click().run()
    assert not at.exception and at.radio[0].value == 'Data & methods'
    assert at.radio[1].value == 'Review labels'
    next(widget for widget in at.text_input if widget.label == 'Reviewer / codebook / annotation method').set_value('Reviewer A; codebook v1')
    next(button for button in at.button if button.label == 'Save reviewed labels and recalculate').click().run()
    assert not at.exception
    assert 'Reviewer A; codebook v1' in at.session_state['manifest'].notes
    assert at.session_state['dataset'].likes.tolist() == list(range(20, 30))
    assert len(at.session_state['comments_dataset']) == 4


def test_comment_coverage_is_visible_without_fake_evaluation(tmp_path, monkeypatch):
    at = seed_app(tmp_path, monkeypatch)
    at.radio[0].set_value('Comments').run()
    assert not at.exception
    assert [(m.label, m.value) for m in at.metric][:3] == [('Comments sampled', '4'), ('Cue labels assigned', '1'), ('Needs review', '3')]
    assert any('No evaluation score' in item.value for item in at.info)


def test_upgrade_recalculates_an_older_in_memory_dataset(tmp_path, monkeypatch):
    at = seed_app(tmp_path, monkeypatch)
    at.session_state['dataset'] = at.session_state['dataset'].drop(columns=['age_days_at_snapshot', 'visible_rate_followers', 'language_inferred', 'category_suggested'])
    at.run()
    assert not at.exception and 'age_days_at_snapshot' in at.session_state['dataset']


def test_empty_workspace_has_import_and_no_invented_statistics(tmp_path, monkeypatch):
    monkeypatch.setattr('src.dashboard.ROOT', tmp_path)
    at = AppTest.from_file(APP).run()
    assert not at.exception and not at.metric
    assert any('No dataset is active' in item.value for item in at.markdown)
