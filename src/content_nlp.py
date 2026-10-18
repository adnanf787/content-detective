"""Transparent exploratory language/category/sentiment cues; no trained accuracy claim."""
import re
import pandas as pd

ROMAN = set('hai hain hy ha hein ap aap ka ki ke ko se aur mein main hum ham aaj kya kyun acha achi bohat bahut nahi nahin mujhe mera meri karo kar dein'.split())
ENGLISH = set('the this that is are your you my our and for with please network service good bad great love best thanks thank internet speed new offer'.split())
POSITIVE = set('love great excellent good best amazing fantastic awesome thanks thank acha achi achay behtareen zabardast shukriya شکریہ اچھا اچھی بہترین زبردست عمدہ'.split())
NEGATIVE = set('bad poor worst hate terrible disappointed useless pathetic slow bakwas bakwaas bura buri ghatiya بیکار خراب برا بری بدترین بکواس سست'.split())
NEGATION = set('not never no nahi nahin نہیں نہ'.split())
RULES = [
    ('customer support', ['complaint', 'helpline', 'customer support', 'شکایت']),
    ('seasonal / cultural', ['eid', 'ramadan', 'ramzan', 'independence', 'psl', 'cricket', 'عید', 'رمضان']),
    ('educational', ['how to', 'tutorial', 'guide', 'step by step', 'tips', 'طریقہ']),
    ('promotional', ['offer', 'bundle', 'discount', 'subscribe', 'package', 'super card', 'آفر', 'پیکج']),
    ('product / service update', ['launch', 'introducing', '5g', '4g', 'coverage', 'network', 'اپڈیٹ']),
    ('entertainment / humour', ['comedy', 'funny', 'humour', 'humor']),
]


def tokens(text):
    return re.findall(r'[^\W\d_]+', str(text).casefold(), flags=re.UNICODE)


def language_cue(text):
    text = str(text)
    terms = set(tokens(text))
    urdu_script = bool(re.search(r'[\u0600-\u06ff]', text))
    if urdu_script:
        return 'Mixed candidate' if len(terms & (ROMAN | ENGLISH)) >= 2 else 'Urdu-script candidate'
    if len(terms & ROMAN) >= 2:
        return 'Roman Urdu candidate'
    if len(terms & ENGLISH) >= 2:
        return 'English candidate'
    return 'unknown'


def sentiment_cue(text):
    terms = set(tokens(text))
    method = 'Exploratory English/Urdu/Roman Urdu cue lexicon; unevaluated; not audience-wide sentiment'
    if terms & NEGATION:
        return 'unassessed', method + '; negation requires review'
    positive, negative = terms & POSITIVE, terms & NEGATIVE
    if bool(positive) == bool(negative):
        return 'unassessed', method + '; absent or conflicting cues'
    return ('positive' if positive else 'negative'), method + '; cues: ' + ', '.join(sorted(positive | negative))


def category_cue(text):
    lowered = str(text).casefold()
    matches = [(category, [word for word in words if re.search(r'(?<!\w)' + re.escape(word) + r'(?!\w)', lowered)]) for category, words in RULES]
    matched = [(category, words) for category, words in matches if words]
    if len(matched) != 1:
        return 'other / uncertain', '; '.join(category + ': ' + ', '.join(words) for category, words in matched)
    return matched[0][0], ', '.join(matched[0][1])


def annotate_comments(frame):
    df = frame.copy()
    df['language_inferred'] = df.comment_text.map(language_cue)
    results = df.comment_text.map(sentiment_cue)
    df['sentiment_label'] = [r[0] for r in results]
    df['sentiment_method'] = [r[1] for r in results]
    df['sentiment_confidence'] = pd.NA
    return df


def annotate_posts(frame):
    df = frame.copy()
    df['language_inferred'] = df.caption.map(language_cue)
    categories = df.caption.map(category_cue)
    df['category_suggested'] = [value[0] for value in categories]
    df['category_evidence'] = [value[1] for value in categories]
    return df


def evaluation_table(labeled):
    """Only evaluate genuinely supplied human labels; blanks never become ground truth."""
    labels = ['positive', 'neutral', 'negative']
    work = labeled[labeled.human_label.isin(labels)].copy()
    if work.empty:
        return None
    table = pd.crosstab(pd.Categorical(work.human_label, categories=labels),
                        pd.Categorical(work.sentiment_label, categories=[*labels, 'unassessed']), dropna=False)
    scores = []
    for label in labels:
        tp = ((work.human_label == label) & (work.sentiment_label == label)).sum()
        fp = ((work.human_label != label) & (work.sentiment_label == label)).sum()
        fn = ((work.human_label == label) & (work.sentiment_label != label)).sum()
        scores.append(float(2 * tp / (2 * tp + fp + fn)) if 2 * tp + fp + fn else 0.0)
    return {'n': len(work), 'coverage': float(work.sentiment_label.ne('unassessed').mean()),
            'macro_f1': sum(scores) / 3, 'confusion_matrix': table}
