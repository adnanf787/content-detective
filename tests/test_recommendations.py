from src.recommendations import recommend
from src.reporting import markdown_report
from src.analysis import QUESTIONS, feasibility, audience_rows


def test_sparse_data_does_not_invent_winners(build):
    df, q, m = build([{'caption': 'hello'}])
    cards = recommend(df, 'likes', m)
    assert all('Collect more' in card['action'] for card in cards[:4])
    report = markdown_report(df, q, 'likes', m)
    for question in QUESTIONS:
        assert question in report
    assert 'Not answerable with the current data' in report


def test_demo_recommendation_quotes_comparison_evidence(build):
    rows = [{'post_id': str(i), 'content_type': 'reel' if i < 5 else 'image',
             'likes': 50 if i < 5 else 10, 'post_datetime': '2026-10-01T18:00:00+05:00'}
            for i in range(10)]
    df, _, m = build(rows, status='synthetic')
    card = recommend(df, 'likes', m)[0]
    assert 'reel' in card['action'] and 'image' in card['action']
    assert 'n=5/5' in card['evidence'] and '50.00' in card['evidence']
    assert '2026-10-01' in card['evidence'] and 'SYNTHETIC DEMO' in card['evidence']
    assert 'Synthetic demonstration only' in card['limitations']


def test_low_coverage_groups_are_not_recommended(build):
    rows = [{'post_id': str(i), 'content_type': 'reel' if i < 10 else 'image',
             'likes': None if i < 5 else 10} for i in range(20)]
    df, _, m = build(rows)
    assert recommend(df, 'likes', m)[0]['confidence'] == 'Insufficient evidence'


def test_brand_location_does_not_verify_audience(build):
    df, _, m = build([{'brand': 'Karachi brand', 'audience_location': 'Pakistan', 'audience_segment': '18–24', 'likes': 10}], status='real')
    assert audience_rows(df, m).empty
    assert feasibility(df, 'likes', m).iloc[5].support == 'Unavailable'


def test_verified_declared_real_segment_remains_partial(build):
    df, _, m = build([{'audience_location': 'Pakistan', 'audience_segment': '18–24', 'likes': 10}],
                     status='real', audience_evidence='Authorized aggregate segment export, Pakistan audience')
    assert len(audience_rows(df, m)) == 1
    assert feasibility(df, 'likes', m).iloc[5].support == 'Partial'


def test_synthetic_demographics_never_establish_pakistani_audience(build):
    df, _, m = build([{'audience_location': 'Pakistan', 'audience_segment': '18–24', 'likes': 10}],
                     status='synthetic', audience_evidence='invented')
    assert audience_rows(df, m).empty


def test_mixed_data_tracks_do_not_produce_a_pooled_recommendation(build):
    df, _, m = build([{'post_id': '1', 'is_synthetic': True, 'likes': 50},
                      {'post_id': '2', 'is_synthetic': False, 'likes': 10}])
    cards = recommend(df, 'likes', m)
    assert len(cards) == 1 and cards[0]['kind'] == 'Separate data tracks'


def test_tiny_comparisons_are_only_partially_supported(build):
    df, _, m = build([{'post_id': '1', 'platform': 'IG', 'likes': 1},
                      {'post_id': '2', 'platform': 'FB', 'likes': 4}])
    assert feasibility(df, 'likes', m).iloc[0].support == 'Partial'


def test_pakistan_lab_recommendations_and_ai_brief_include_real_comparisons(build):
    from src.recommendations import marketing_prompt
    from src.reporting import summary_tables
    df, _, manifest = build([{'post_id': str(i), 'likes': 30 if i < 5 else 10,
                              'caption_language': 'Roman Urdu' if i < 5 else 'English',
                              'creative_angle': 'Tutorial / how-to' if i < 5 else 'Offer / promotion'} for i in range(10)], status='real')
    card = next(c for c in recommend(df, 'likes', manifest) if c['kind'] == 'Caption language experiment')
    assert 'Roman Urdu' in card['action'] and 'n=5/5' in card['evidence']
    assert 'caption_language' in summary_tables(df, 'likes', manifest)
    prompt = marketing_prompt(df, 'likes', manifest, 'A local brand wants more comments.')
    assert '30.00' in prompt and '10.00' in prompt and 'Do not invent' in prompt
    assert 'A local brand wants more comments.' in prompt


def test_supported_recommendations_cite_actual_source_examples(build):
    df, _, manifest = build([{'post_id': str(i), 'source_url': f'https://www.youtube.com/watch?v=example{i}',
                              'content_type': 'video' if i < 5 else 'reel', 'likes': 30 if i < 5 else 10} for i in range(10)])
    card = recommend(df, 'likes', manifest)[0]
    assert len(card['examples']) == 2
    assert {example['value'] for example in card['examples']} == {30, 10}
    assert all(example['url'] in df.source_url.tolist() for example in card['examples'])
