"""An intentionally limited, offline English baseline with explicit abstention."""
import re
import pandas as pd

POSITIVE = {'love', 'great', 'happy', 'amazing', 'excellent', 'beautiful', 'best', 'enjoy', 'good', 'awesome'}
NEGATIVE = {'bad', 'hate', 'awful', 'poor', 'worst', 'broken', 'terrible', 'disappointed', 'sad'}
# Conservative allowlist: unseen vocabulary abstains, including most Roman Urdu.
ENGLISH = POSITIVE | NEGATIVE | set('the a an and or our your this that is are we you i new collection shop today now summer winter for with in on at of to from available discover product offer sale free delivery not never no very really so it was quality service'.split())


def classify(text):
    if pd.isna(text) or not str(text).strip():
        return 'unassessed', 'No caption'
    text = str(text)
    if re.search(r'[\u0600-\u06ff]', text):
        return 'unassessed', 'Urdu/Arabic-script text: unsupported by English baseline'
    without_tags = re.sub(r'#[\w\u0600-\u06ff]+|https?://\S+', '', text)
    words = re.findall(r"[a-z]+", without_tags.lower())
    if not words or sum(w in ENGLISH for w in words) / len(words) < .85:
        return 'unassessed', 'Language/vocabulary uncertain; Roman Urdu is not validated'
    if any(w in {'not', 'no', 'never'} for w in words):
        return 'unassessed', 'Negation requires review'
    score = sum(w in POSITIVE for w in words) - sum(w in NEGATIVE for w in words)
    return ('positive' if score > 0 else 'negative' if score < 0 else 'neutral'), 'Tiny English lexicon baseline (unvalidated)'


def add_sentiment(df):
    frame = df.copy()
    results = []
    for row in frame.itertuples():
        label = str(row.caption_sentiment).strip().lower()
        if label in {'positive', 'neutral', 'negative'}:
            results.append((label, 'Dataset-supplied label (method/accuracy unverified)'))
        else:
            results.append(classify(row.caption))
    frame['sentiment_label'] = [r[0] for r in results]
    frame['sentiment_method'] = [r[1] for r in results]
    return frame
