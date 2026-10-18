"""Prove corporate-site affiliation before resolving YouTube IDs; never use search as proof."""
from html.parser import HTMLParser
from pathlib import Path
import sys
from urllib.parse import urlparse

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.settings import youtube_key
from src.youtube_api import APIError, YouTubeAPI, atomic_json, utcnow


class YouTubeLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = set()

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name != 'href' or not value:
                continue
            parsed = urlparse(value)
            if parsed.scheme in {'https', 'http'} and parsed.hostname in {'youtube.com', 'www.youtube.com', 'youtu.be'}:
                self.links.add(value)


def verify():
    path = ROOT / 'config/brands.yml'
    config = yaml.safe_load(path.read_text())
    stamp = utcnow()
    api = YouTubeAPI(youtube_key(), ROOT / 'data/raw' / ('verify_' + stamp.replace(':', '').replace('.', '')))
    checks = []
    for brand in config['brands']:
        entry = brand['youtube']
        check = {'brand': brand['brand_name'], 'verification_url': entry['verification_url'], 'checked_at_utc': stamp}
        checks.append(check)
        try:
            response = requests.get(entry['verification_url'], timeout=(10, 30))
            check['corporate_http_status'] = response.status_code
            response.raise_for_status()
            parser = YouTubeLinks()
            parser.feed(response.text)
            check['corporate_youtube_links'] = sorted(parser.links)
            if not any(link.rstrip('/') == entry['verification_link'].rstrip('/') for link in parser.links):
                raise ValueError('Expected corporate channel link was not present.')
            payload = api.get('channels', {'part': 'snippet,contentDetails,statistics', **entry['lookup']})
            if len(payload['items']) != 1:
                raise ValueError('API channel identity did not resolve uniquely.')
            channel = payload['items'][0]
            entry.update(channel_id=channel['id'], verified_official=True, channel_title=channel['snippet']['title'],
                         handle=channel['snippet'].get('customUrl', ''), verified_at_utc=api.last_time,
                         verification_raw_record=str(Path(api.last_path).relative_to(ROOT)),
                         verification_method='Exact official corporate homepage hyperlink, resolved by YouTube channels.list')
            check.update(status='verified', channel_id=channel['id'])
            print(brand['brand_name'], channel['id'], 'verified from corporate link and official API', flush=True)
        except (requests.RequestException, APIError, ValueError):
            entry['verified_official'] = False
            check['status'] = 'unresolved'
            print(brand['brand_name'], 'verification unresolved; inspect local verification log', flush=True)
    path.write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True))
    atomic_json(ROOT / 'config/brand_verification.json', {'checked_at_utc': stamp, 'checks': checks})
    return all(c['status'] == 'verified' for c in checks)


if __name__ == '__main__':
    raise SystemExit(0 if verify() else 1)
