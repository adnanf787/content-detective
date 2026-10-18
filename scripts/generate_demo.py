"""Regenerate the openly synthetic fixture with a fixed random seed."""
from pathlib import Path
import csv
import json
import random
import sys
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.schema import FIELDS


def generate():
    rng = random.Random(42)
    records = []
    themes = [
        ('new collection', 'Discover our beautiful new collection #StyleDemo #پاکستان'),
        ('product guide', 'Our product quality is great #GuideDemo #StyleDemo'),
        ('promotion', 'Shop our summer sale today #SaleDemo #StyleDemo'),
        ('community', 'آپ کی پسند کیا ہے؟ #پاکستان #CommunityDemo'),
        ('behind the scenes', 'Aaj hamari nayi collection dekhein #CraftDemo'),
        ('service update', 'We are disappointed with the poor service #ServiceDemo'),
    ]
    start = datetime(2026, 8, 1, 9, tzinfo=timezone(timedelta(hours=5)))
    for i in range(180):
        platform = ['Instagram', 'Facebook', 'TikTok'][i % 3]
        content = ['reel', 'image', 'carousel'][rng.randrange(3)]
        topic, caption = themes[rng.randrange(len(themes))]
        likes = round(rng.lognormvariate(5.4, .65) * (1.5 if content == 'reel' else 1))
        comments = rng.randint(2, 65)
        shares = rng.randint(1, 80)
        stamp = start + timedelta(days=i // 3, hours=rng.choice([0, 4, 10]))
        records.append(dict(post_id=f'DEMO-{i+1:04}', source_url='',
                            source_name='Fixed-seed synthetic generator; NOT real posts',
                            source_type='synthetic', is_synthetic='true',
                            brand=['Demo Loom', 'Demo Kitchen', 'Demo Cart'][rng.randrange(3)],
                            platform=platform, post_datetime=stamp.isoformat(), timezone_source='Asia/Karachi',
                            content_type=content, caption=caption, hashtags='', topic=topic,
                            caption_language='Urdu' if topic == 'community' else 'Roman Urdu' if topic == 'behind the scenes' else 'English',
                            local_context='Everyday',
                            creative_angle={'product guide': 'Tutorial / how-to', 'promotion': 'Offer / promotion',
                                            'community': 'Question / conversation', 'behind the scenes': 'Storytelling'}.get(topic, 'Other'),
                            likes=likes, comments=comments, shares='' if i % 7 == 0 else shares,
                            views=rng.randint(1000, 12000), impressions=rng.randint(1500, 18000),
                            reach=rng.randint(1000, 14000), follower_count='',
                            audience_location='', audience_segment='', caption_sentiment='',
                            collection_datetime=(stamp + timedelta(days=7)).isoformat()))
    with (ROOT / 'data/sample_synthetic_posts.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)
    with (ROOT / 'data/collection_template.csv').open('w', encoding='utf-8', newline='') as f:
        csv.writer(f).writerow(FIELDS)
    manifest = dict(file_name='sample_synthetic_posts.csv', source_name='Fixed-seed demo generator',
                    source_type='synthetic', status='synthetic', collected_on='',
                    geographic_relevance='Fictional Pakistan-market scenario; no verified audience',
                    license_notes='Generated project fixture; not scraped from platforms',
                    source_timezone='Asia/Karachi', audience_evidence='', notes='Seed 42. All 180 observations and accounts are invented.')
    (ROOT / 'data/demo_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')


if __name__ == '__main__':
    generate()
