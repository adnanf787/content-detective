"""Local configuration; no credential values are logged or exported."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]


def youtube_key():
    load_dotenv(ROOT / '.env', override=False)
    return os.getenv('YOUTUBE_API_KEY', '').strip()
