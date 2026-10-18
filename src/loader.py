"""UTF-8 CSV loader and serializable provenance metadata."""
from dataclasses import dataclass, asdict
from io import BytesIO
import pandas as pd


@dataclass
class Manifest:
    file_name: str = 'unknown'
    source_name: str = 'Unspecified source'
    source_type: str = 'unverified'
    status: str = 'unverified'
    collected_on: str = ''
    geographic_relevance: str = 'Unknown; no verified Pakistani audience geography'
    license_notes: str = 'Not documented'
    source_timezone: str = 'unknown'
    audience_evidence: str = ''
    notes: str = ''
    sha256: str = ''

    def to_dict(self):
        return asdict(self)


def read_csv(data: bytes):
    if len(data) > 25 * 1024 * 1024:
        raise ValueError('CSV exceeds the 25 MB import limit.')
    try:
        frame = pd.read_csv(BytesIO(data), dtype=str, encoding='utf-8-sig', keep_default_na=False)
    except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError) as exc:
        raise ValueError(f'Cannot read CSV. Use a UTF-8 file with a header row. {exc}') from exc
    if frame.empty:
        raise ValueError('The CSV has a header but no post records.')
    if len(frame.columns) > 200:
        raise ValueError('CSV has more than 200 columns; select the post-level fields first.')
    return frame
