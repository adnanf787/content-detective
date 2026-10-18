"""Read the saved real snapshot without network access or implicit data changes."""
import hashlib
import json
from pathlib import Path
import pandas as pd

from src.content_nlp import annotate_comments
from src.dataset_validation import validate_exports
from src.loader import Manifest, read_csv


def read_saved_study(root):
    folder = Path(root) / 'data/processed'
    content = (folder / 'youtube_posts.csv').read_bytes()
    raw = read_csv(content)
    comments = pd.read_csv(folder / 'youtube_comments.csv', dtype=str, keep_default_na=False)
    report = json.loads((folder / 'youtube_collection_report.json').read_text())
    audit = validate_exports(raw, comments)
    if not audit['valid']:
        raise ValueError('Saved research files failed validation: ' + '; '.join(audit['errors']))
    manifest = Manifest(file_name='youtube_posts.csv', source_name='Verified Jazz, Zong, Ufone YouTube pilot',
                        source_type='official_api', status='real', source_timezone='UTC',
                        collected_on=report['ended_at_utc'], sha256=hashlib.sha256(content).hexdigest(),
                        geographic_relevance='Official Pakistan telecom brands; viewer nationality and demographics are unknown',
                        license_notes='Official YouTube Data API acquisition; subject to YouTube developer terms.',
                        notes=report['sampling_method'] + '\n' + report['limitations'])
    return raw, annotate_comments(comments), manifest, report
