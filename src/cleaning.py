"""Conservative cleaning. Unknown values remain unknown; conflicts stay inspectable."""
import numpy as np
import pandas as pd
from src.schema import FIELDS, METRICS
from src.timing import add_timing

PLATFORMS = {'ig': 'Instagram', 'instagram': 'Instagram', 'fb': 'Facebook',
             'facebook': 'Facebook', 'tiktok': 'TikTok', 'tik tok': 'TikTok',
             'youtube': 'YouTube', 'twitter': 'X', 'x': 'X', 'linkedin': 'LinkedIn'}
FORMATS = {'reels': 'reel', 'photo': 'image', 'picture': 'image', 'photos': 'image',
           'short': 'short-form video', 'short video': 'short-form video'}


def clean_posts(raw, manifest):
    if raw.columns.duplicated().any():
        raise ValueError('Duplicate canonical column names are not allowed.')
    df = raw.copy()
    original_rows = len(df)
    exact = int(df.duplicated().sum())
    df = df.drop_duplicates().reset_index(drop=True)
    original_columns = list(df.columns)
    for field in FIELDS:
        if field not in df:
            df[field] = pd.NA
    caption_original = df['caption'].copy()
    for field in FIELDS:
        if field not in METRICS:
            df[field] = df[field].astype('string').str.strip().replace('', pd.NA)
    df['caption_original'] = caption_original
    df['platform'] = df['platform'].map(lambda x: PLATFORMS.get(str(x).lower(), x))
    df['content_type'] = df['content_type'].str.lower().replace(FORMATS)
    invalid_counts = {}
    for field in METRICS:
        original = df[field].astype('string').str.strip().replace('', pd.NA)
        numeric = pd.to_numeric(original, errors='coerce').astype(float)
        invalid = original.notna() & (numeric.isna() | ~np.isfinite(numeric) | (numeric < 0) | (numeric % 1 != 0))
        invalid_counts[field] = int(invalid.sum())
        df[f'{field}_original'] = original.astype('string')
        df[field] = numeric.mask(invalid)
    for field, value in [('source_name', manifest.source_name), ('source_type', manifest.source_type)]:
        df[field] = df[field].fillna(value)
    supplied = df['is_synthetic'].str.lower().map({'true': True, '1': True, 'yes': True,
                                                'false': False, '0': False, 'no': False})
    synthetic = supplied.eq(True) | df['source_type'].str.lower().eq('synthetic') | (manifest.status == 'synthetic')
    declared_real = (supplied.eq(False) | (manifest.status == 'real')) & ~synthetic
    df['data_status'] = np.select([synthetic.to_numpy(dtype=bool, na_value=False),
                                  declared_real.to_numpy(dtype=bool, na_value=False)],
                                 ['synthetic', 'real (declared)'], default='unverified')
    df['is_synthetic'] = pd.array([True if s == 'synthetic' else False if s == 'real (declared)' else pd.NA
                                  for s in df.data_status], dtype='boolean')
    missing_ids = df['post_id'].isna()
    df['id_generated'] = missing_ids
    df.loc[missing_ids, 'post_id'] = [f'local-row-{i+1}' for i in df.index[missing_ids]]
    keys = ['source_name', 'platform', 'brand', 'post_id']
    df['duplicate_conflict'] = df.duplicated(keys, keep=False) & ~missing_ids
    df['analysis_eligible'] = ~df['duplicate_conflict']
    df = add_timing(df, manifest.source_timezone)
    report = {
        'input_rows': original_rows, 'cleaned_rows': len(df), 'exact_duplicates_removed': exact,
        'conflicting_rows_excluded': int(df.duplicate_conflict.sum()),
        'generated_local_ids': int(missing_ids.sum()), 'invalid_counts': invalid_counts,
        'invalid_timestamps': int(df.time_status.str.startswith('invalid').sum()),
        'timezone_unknown': int(df.time_status.eq('timezone unknown').sum()),
        'original_columns': original_columns,
        'missingness': {f: int(df[f].isna().sum()) for f in FIELDS},
    }
    return df, report
