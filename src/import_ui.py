"""Reviewed CSV import and quality screen, preserved from the original dashboard."""
from pathlib import Path
import hashlib
import pandas as pd
import streamlit as st
from src.loader import Manifest, read_csv
from src.schema import FIELDS, suggest_mapping, apply_mapping
ROOT = Path(__file__).resolve().parents[1]


def import_screen(activate):
    st.header('Bring your evidence')
    st.write('Import a post-level UTF-8 CSV. Review the mapping and provenance before applying it. Unknown counts stay blank.')
    uploaded = st.file_uploader('Upload post data (CSV, up to 25 MB)', type=['csv'])
    st.download_button('Download collection template', (ROOT / 'data/collection_template.csv').read_bytes(),
                       file_name='collection_template.csv', mime='text/csv')
    if uploaded is not None:
        try:
            content = uploaded.getvalue()
            raw = read_csv(content)
        except ValueError as exc:
            st.error(str(exc))
            return
        digest = hashlib.sha256(content).hexdigest()
        st.caption(f'{len(raw):,} original rows · {len(raw.columns)} columns · no data has been sent to an API')
        st.dataframe(raw.head(10), hide_index=True, width='stretch')
        st.caption('Original column types: ' + ', '.join(f'{c}: {raw[c].dtype}' for c in raw.columns))
        suggestion = suggest_mapping(raw.columns)
        with st.form('import_' + digest):
            with st.expander('Column mapping: review aliases and map missing fields', expanded=True):
                options = ['(not provided)', *raw.columns]
                mapping = {}
                cols = st.columns(3)
                for i, field in enumerate(FIELDS):
                    with cols[i % 3]:
                        choice = st.selectbox(field, options, index=options.index(suggestion[field]) if suggestion[field] else 0,
                                              key=digest + field)
                        mapping[field] = None if choice == '(not provided)' else choice
            st.subheader('Import manifest')
            left, right = st.columns(2)
            with left:
                source = st.text_input('Publisher / account / export name', value='Unspecified source')
                method = st.selectbox('Collection method', ['unverified', 'official_export', 'manual_public_post', 'third_party', 'synthetic'])
                status = st.selectbox('Dataset status (your declaration)', ['unverified', 'real', 'synthetic'])
                collected = st.text_input('Collection date (if known, ISO YYYY-MM-DD)')
            with right:
                geo = st.text_input('Geographic relevance', value='Unknown; no verified Pakistani audience geography')
                tz = st.text_input('Source timezone for naive timestamps', value='unknown', help='Use an IANA zone such as Asia/Karachi or UTC only if known. Explicit offsets take priority.')
                license_note = st.text_input('Permission / terms / license notes', value='Not documented')
                audience_evidence = st.text_input('Verified audience segment evidence (leave blank if absent)', help='Document the export/source confirming actual Pakistani segment data. A brand location is insufficient.')
            notes = st.text_area('Source notes, sentiment-label method, collection limitations')
            st.caption('Real is a user declaration, not independent verification. Row-level synthetic flags always persist.')
            submitted = st.form_submit_button('Validate and activate dataset', type='primary')
        if submitted:
            try:
                manifest = Manifest(file_name=uploaded.name, source_name=source, source_type=method,
                                    status=status, collected_on=collected, geographic_relevance=geo,
                                    license_notes=license_note, source_timezone=tz, audience_evidence=audience_evidence,
                                    notes=notes, sha256=digest)
                activate(apply_mapping(raw, mapping), manifest)
                st.rerun()
            except (ValueError, TypeError) as exc:
                st.error(f'Import could not be applied: {exc}')
    if 'dataset' in st.session_state:
        df, quality = st.session_state.dataset, st.session_state.quality
        st.subheader('Quality scorecard · entire imported file')
        cols = st.columns(4)
        cols[0].metric('Input rows', quality['input_rows'])
        cols[1].metric('Identical duplicates removed', quality['exact_duplicates_removed'])
        cols[2].metric('Conflicting rows excluded', quality['conflicting_rows_excluded'])
        cols[3].metric('Invalid numeric entries', sum(quality['invalid_counts'].values()))
        st.write(f'Invalid timestamps: {quality["invalid_timestamps"]}. Timezone unknown: {quality["timezone_unknown"]}. '
                 f'Generated local row IDs: {quality["generated_local_ids"]}. Conflicts remain in cleaned exports.')
        if quality['conflicting_rows_excluded']:
            st.dataframe(df[df.duplicate_conflict], width='stretch')
        score = pd.DataFrame({'field': list(quality['missingness']), 'missing': list(quality['missingness'].values())})
        score['coverage_pct'] = 100 * (1 - score.missing / max(len(df), 1))
        st.dataframe(score, hide_index=True, width='stretch')
        st.json(st.session_state.manifest.to_dict(), expanded=False)
        st.subheader('Cleaned preview')
        st.dataframe(df.head(20), hide_index=True, width='stretch')
