"""Student-facing collection and annotation workflow for the assignment dashboard."""
from dataclasses import replace
from datetime import datetime, time, timedelta, timezone
import hashlib
import json

import pandas as pd
import streamlit as st

from src.collection import CollectionError, collect_youtube, manual_observation
from src.loader import Manifest
from src.settings import youtube_key
from src.study_ui import telecom_collection_panel, instagram_import_panel

LANGUAGES = ['Urdu', 'Roman Urdu', 'English', 'Mixed', 'Other']
ANGLES = ['Tutorial / how-to', 'Humour', 'Storytelling', 'Product demo', 'Offer / promotion', 'Question / conversation', 'Other']
CONTEXTS = ['Everyday', 'Eid', 'Ramadan', 'PSL / cricket', 'Wedding season', 'National occasion', 'Other']
LABELS = ['content_type', 'topic', 'caption_sentiment', 'caption_language', 'creative_angle', 'local_context']


def project_brief():
    st.header('Project 1 · Junior digital-marketing data scientists')
    st.write('Help a Pakistani brand decide what to post next by collecting social-media observations and finding engagement patterns.')
    st.markdown('''Your evidence should answer the seven assignment questions: platform, content type,
topics/hashtags, caption sentiment, posting day/time, audience segments, and the next content experiment.

**Our distinctive angle: Pakistan Content Lab.** Compare reviewed Urdu, Roman Urdu, English,
and mixed-language captions alongside local context (Eid, Ramadan, PSL, wedding season)
and creative approaches (tutorials, humour, offers, stories). Caption language describes the
content; it does not identify the people who viewed it.

**Current study:** Pakistan telecom, with verified Jazz, Zong, and Ufone YouTube channels.
The saved official-API pilot contains 10 videos per brand and a capped public-comment sample.
The common eligibility window is October 2025–September 2026, extended with user approval
because the original April–September interval contained only seven eligible Zong videos.
The actual source dates/post ages still differ across brands. Add a second platform when
comparable observations are available; one platform cannot answer the platform comparison.

**Workflow:** Collect real data → Label content → check Overview coverage → explore patterns
→ build a controlled recommendation → export evidence. The demo only shows how the tool works.

**Later add-on:** paste a video link, retrieve its available caption/tags/counts through a
supported source, review labels, and compare it with relevant posts in your real dataset.
Use those comparisons to propose edits, hooks, captions, and an A/B test. Views cannot be guaranteed.
''')
    st.info('Audience segment responsiveness needs an authorized audience analytics export. Public post metadata cannot establish Pakistani age, gender, or city response rates.')


def stage_collection(result):
    existing = st.session_state.get('collection_buffer', pd.DataFrame())
    combined = pd.concat([existing, result.posts], ignore_index=True)
    # This is a single latest snapshot per post, not a longitudinal dataset.
    combined = combined.drop_duplicates(['platform', 'post_id'], keep='last').reset_index(drop=True)
    st.session_state['collection_buffer'] = combined
    batches = st.session_state.get('collection_batches', [])
    st.session_state['collection_batches'] = [*batches, {'manifest': result.manifest.to_dict(), 'receipt': result.receipt}]


def collected_manifest(posts, batches):
    relevance = list(dict.fromkeys(b['manifest']['geographic_relevance'] for b in batches))
    return Manifest(file_name='collected_public_posts.csv', source_name='Public-post collection workspace',
                    source_type='public_collection', status='real', source_timezone='unknown',
                    collected_on=batches[-1]['manifest']['collected_on'],
                    geographic_relevance='; '.join(relevance),
                    license_notes='; '.join(dict.fromkeys(b['manifest']['license_notes'] for b in batches)),
                    notes='Latest snapshot per platform/post ID; repeated collection replaces the earlier staged snapshot.\n' +
                          '\n'.join(b['manifest']['notes'] for b in batches),
                    sha256=hashlib.sha256(posts.to_csv(index=False).encode()).hexdigest())


def collection_screen(activate):
    st.header('Collect real data')
    st.write('Build a dataset from permitted public observations. Review and download staged records before activating them for analysis.')
    st.caption('Nothing is fetched until you press a collection button. The verified telecom collector saves local raw JSON, CSV, and SQLite. Manual/link staging stays in this session. No raw video or commenter profile fields are collected.')
    telecom_tab, manual_tab, api_tab, instagram_tab = st.tabs(['Verified YouTube pilot', 'Public observations · no API key', 'YouTube links / search', 'Instagram CSV fallback'])
    with telecom_tab:
        telecom_collection_panel(activate)
    with instagram_tab:
        instagram_import_panel(activate)
    with manual_tab:
        st.write('Open a public post yourself and record its exact visible counts. This works across platforms without pretending a link supplies hidden analytics.')
        with st.form('manual_collection'):
            url = st.text_input('Public post URL')
            platform = st.selectbox('Platform', ['Instagram', 'TikTok', 'YouTube', 'Facebook', 'X', 'LinkedIn'])
            brand = st.text_input('Account / brand')
            caption = st.text_area('Exact caption / title / description')
            published = st.text_input('Publication date or ISO timestamp (optional)', placeholder='2026-10-01T18:00:00+05:00')
            st.caption('Date only is allowed; it cannot establish a posting hour. Timestamps without timezone evidence are excluded from local-time comparisons.')
            columns = st.columns(4)
            counts = {field: columns[i].text_input(field.title(), key='manual_' + field) for i, field in enumerate(['likes', 'comments', 'shares', 'views'])}
            st.caption('Leave unavailable counts blank. Enter whole counts without commas. Rounded displays such as 1.2K are not exact observations.')
            relevance = st.text_input('Why is this account/content relevant to the Pakistan market?', key='manual_relevance')
            submitted = st.form_submit_button('Stage public observation')
        if submitted:
            try:
                result = manual_observation(url=url, platform=platform, brand=brand, caption=caption,
                                            relevance_note=relevance, counts=counts, published_at=published.strip())
                stage_collection(result)
                st.success('Observation staged. Add more posts, then activate the collection below.')
            except CollectionError as exc:
                st.error(str(exc))
    with api_tab:
        st.write('Fetch real video titles, descriptions, tags, timestamps, and available counts through YouTube Data API v3.')
        st.markdown('[API key setup](https://developers.google.com/youtube/data/getting-started) · '
                    '[Video fields](https://developers.google.com/youtube/data/reference/rest/v3/videos)')
        with st.form('youtube_collection'):
            key = st.text_input('YouTube Data API key (local use)', type='password', value=youtube_key())
            mode = st.selectbox('Collection mode', ['Selected video links', 'Search recent videos'])
            links = st.text_area('Video URLs / IDs · one per line (up to 200)')
            query = st.text_input('Search query', placeholder='Pakistan skincare tutorial')
            limit = st.number_input('Search collection limit', min_value=1, max_value=200, value=50)
            end_date = datetime.now(timezone.utc).date()
            start = st.date_input('Search publication start (UTC)', value=end_date - timedelta(days=90))
            end = st.date_input('Search publication end (UTC, inclusive)', value=end_date)
            relevance = st.text_input('Pakistan-market relevance and sampling rationale', key='youtube_relevance')
            st.caption('The query/IDs and key are sent only to Google’s YouTube API. The key is excluded from dataset exports. Search uses newest-first results available in Pakistan; it does not verify Pakistani viewers or representative sampling. API quota applies.')
            submitted = st.form_submit_button('Fetch and stage real videos')
        if submitted:
            try:
                if mode == 'Search recent videos' and start > end:
                    raise CollectionError('Search start must be on or before the end date.')
                with st.spinner('Collecting public metadata from YouTube…'):
                    result = collect_youtube(key, links=links if mode == 'Selected video links' else '',
                                             query=query if mode == 'Search recent videos' else '', limit=int(limit),
                                             published_after=datetime.combine(start, time.min, timezone.utc).isoformat() if mode == 'Search recent videos' else '',
                                             published_before=datetime.combine(end + timedelta(days=1), time.min, timezone.utc).isoformat() if mode == 'Search recent videos' else '',
                                             relevance_note=relevance)
                stage_collection(result)
                st.success(f'{len(result.posts)} actual video records staged.')
                if result.missing_ids:
                    st.warning('YouTube omitted these requested IDs (possibly unavailable): ' + ', '.join(result.missing_ids))
            except CollectionError as exc:
                st.error(str(exc))
    posts = st.session_state.get('collection_buffer')
    if posts is not None and not posts.empty:
        batches = st.session_state.collection_batches
        manifest = collected_manifest(posts, batches)
        st.subheader(f'Staged collection · {len(posts)} unique posts')
        st.caption('Repeated collection keeps the latest snapshot for the same platform/post ID. Different observation dates can bias comparisons; inspect collection_datetime.')
        st.dataframe(posts, hide_index=True, width='stretch')
        st.download_button('Download collected CSV', posts.to_csv(index=False).encode('utf-8-sig'), 'collected_public_posts.csv', 'text/csv')
        st.download_button('Download source receipts and manifest', json.dumps({'manifest': manifest.to_dict(), 'batches': batches}, ensure_ascii=False, indent=2), 'collection_receipts.json', 'application/json')
        st.caption('Activation replaces the active analysis dataset with this staged collection. It does not mix in the synthetic demo. Download an existing dataset first if needed.')
        if st.button('Activate collected dataset', type='primary'):
            activate(posts, manifest)
            st.success('Collection activated. Open Label content, then Overview to check evidence coverage.')
        if st.button('Clear staged collection'):
            del st.session_state['collection_buffer']
            del st.session_state['collection_batches']
            st.rerun()


def label_screen(activate):
    st.header('Review content labels')
    st.write('Use one consistent codebook across accounts. Labels describe the post, not its viewers. Unknown labels can stay blank.')
    if 'dataset' not in st.session_state:
        st.info('Collect or import posts first. Labels will be linked to those actual source rows.')
        return
    version = st.session_state.dataset_version
    raw = st.session_state.get('raw_dataset', st.session_state.dataset).copy().reset_index(drop=True)
    for field in ['source_url', 'brand', 'caption', *LABELS]:
        if field not in raw:
            raw[field] = ''
    editable = raw[['source_url', 'brand', 'caption', *LABELS]].copy().fillna('')
    for field in LABELS:
        editable[field] = editable[field].astype(str)
    st.caption('Use content_type for the media format (image, carousel, reel, video); creative_angle for how the message is presented. YouTube video length alone does not establish a Short.')
    with st.form(f'annotations_{version}'):
        edited = st.data_editor(editable, disabled=['source_url', 'brand', 'caption'], hide_index=True,
                                num_rows='fixed', width='stretch', key=f'label_editor_{version}',
                                column_config={
                                    'caption_sentiment': st.column_config.SelectboxColumn('Caption tone', options=['', 'positive', 'neutral', 'negative']),
                                    'caption_language': st.column_config.SelectboxColumn('Caption language', options=['', *LANGUAGES]),
                                    'creative_angle': st.column_config.SelectboxColumn('Creative approach', options=['', *ANGLES]),
                                    'local_context': st.column_config.SelectboxColumn('Local context', options=['', *CONTEXTS]),
                                })
        method = st.text_input('Reviewer / codebook / annotation method', placeholder='Reviewed by Ayesha; codebook v1; mixed means two languages in the caption')
        submitted = st.form_submit_button('Save reviewed labels and recalculate', type='primary')
    if submitted:
        if not method.strip():
            st.error('Document who reviewed the labels and the codebook used before saving.')
            return
        for field in LABELS:
            raw[field] = edited[field].values
        manifest = replace(st.session_state.manifest,
                           notes=st.session_state.manifest.notes + '\nContent label review: ' + method.strip())
        activate(raw, manifest)
        st.rerun()
