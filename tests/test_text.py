from src.hashtags import extract_hashtags, hashtag_table
from src.sentiment import classify


def test_unicode_hashtags_and_deduplication():
    assert extract_hashtags('Love #Pakistan #پاکستان #خُوبصورت #Pakistan 🇵🇰', '#ROMAN_urdu') == [
        '#pakistan', '#roman_urdu', '#خُوبصورت', '#پاکستان']


def test_tag_coverage_counts_posts_once(build):
    df, _, _ = build([{'post_id': '1', 'caption': '#Tag #tag', 'hashtags': '#TAG', 'likes': 5},
                      {'post_id': '2', 'caption': '#Tag'}])
    row = hashtag_table(df, 'likes').iloc[0]
    assert row.total_posts == 2 and row.n == 1


def test_sentiment_abstains_on_urdu_roman_and_negation():
    for text in ['یہ بہت اچھا ہے', 'aaj ki nayi collection bohat achi', 'not good']:
        assert classify(text)[0] == 'unassessed'
    assert classify('Our collection is beautiful')[0] == 'positive'
    assert classify('the service is terrible')[0] == 'negative'


def test_supplied_labels_have_explicit_source(build):
    df, _, _ = build([{'caption': 'اردو', 'caption_sentiment': 'Positive'}])
    assert df.sentiment_label.iloc[0] == 'positive'
    assert 'Dataset-supplied' in df.sentiment_method.iloc[0]
