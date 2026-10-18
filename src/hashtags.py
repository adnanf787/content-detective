"""Unicode hashtags, including combining marks used in Urdu."""
import unicodedata
import pandas as pd
from src.metrics import summarize


def extract_hashtags(*texts):
    tags = set()
    for text in texts:
        if text is None or pd.isna(text):
            continue
        current = None
        for char in str(text) + ' ':
            if char == '#':
                if current:
                    tags.add('#' + ''.join(current).casefold())
                current = []
            elif current is not None and (char == '_' or unicodedata.category(char)[0] in 'LMN'):
                current.append(char)
            else:
                if current:
                    tags.add('#' + ''.join(current).casefold())
                current = None
    return sorted(tags)


def hashtag_table(df, metric, min_n=5):
    work = df.copy()
    work['hashtag'] = [extract_hashtags(c, h) for c, h in zip(work.caption, work.hashtags)]
    work = work.explode('hashtag').dropna(subset=['hashtag'])
    return summarize(work, 'hashtag', metric, min_n)
