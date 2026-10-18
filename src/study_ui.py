"""Saved, genuinely acquired datasets and separate public-comment analysis."""
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.content_nlp import annotate_comments, evaluation_table
from src.instagram_csv import import_instagram_csv, instagram_template
from src.loader import Manifest, read_csv
from src.settings import ROOT, youtube_key
from src.youtube_study import load_config, run_study
from src.study_data import read_saved_study


def load_saved_pilot(activate):
    posts, comments, manifest, report = read_saved_study(ROOT)
    activate(posts, manifest)
    st.session_state['comments_dataset'] = comments
    st.session_state['collection_report'] = report


def telecom_collection_panel(activate):
    config = load_config()
    st.subheader('Official Pakistan telecom channels')
    st.dataframe(pd.DataFrame([{'brand': b['brand_name'], 'channel_id': b['youtube'].get('channel_id'),
                               'handle': b['youtube'].get('handle'), 'verified_official': b['youtube'].get('verified_official'),
                               'verification_url': b['youtube'].get('verification_url')} for b in config['brands']]),
                 hide_index=True, width='stretch', column_config={'verification_url': st.column_config.LinkColumn('Corporate verification source')})
    study = config['study']
    st.write(f'Publication window: {study["publication_start"]} to {study["publication_end"]}, Asia/Karachi. '
             f'Target: {study["videos_per_brand"]} newest eligible videos/brand; up to {study["comments_per_video"]} newest public top-level comments/video. '
             'No replies or commenter profile fields are requested.')
    st.caption(study.get('window_decision', 'No window change recorded.'))
    st.caption('Key: ' + ('available from local environment/.env' if youtube_key() else 'missing; add YOUTUBE_API_KEY to .env'))
    if st.button('Collect / refresh verified YouTube pilot', disabled=not bool(youtube_key())):
        status = st.empty()
        with st.spinner('Collecting through official YouTube endpoints…'):
            try:
                _, _, summary = run_study(progress=status.write)
                st.session_state['latest_collection_attempt'] = summary
            except ValueError:
                st.error('Collection could not start. Check local configuration and credentials. No credential values are displayed.')
    if 'latest_collection_attempt' in st.session_state:
        st.json(st.session_state.latest_collection_attempt, expanded=False)
    report_path = ROOT / 'data/processed/youtube_collection_report.json'
    if report_path.exists():
        summary = json.loads(report_path.read_text())
        st.subheader('Latest saved, validated dataset')
        st.write(f'{summary["posts_collected"]} real videos · {summary["comments_collected"]} sampled comments · status: {summary["status"]}')
        st.dataframe(pd.DataFrame(summary['brands']), hide_index=True, width='stretch')
        st.caption(f'API errors: {len(summary["api_errors"])}. Validation passed: {summary["validation"]["valid"]}. '
                   'Missing fields and sample-access states are preserved in the report and CSV.')
        if st.button('Load saved YouTube pilot into analysis', type='primary'):
            load_saved_pilot(activate)
            st.success('Real dataset activated. Open Overview, Content intelligence, or Comment sentiment.')
        for file_name in ['youtube_posts.csv', 'youtube_comments.csv', 'youtube_collection_report.json', 'sentiment_review_template.csv']:
            path = ROOT / 'data/processed' / file_name
            if path.exists():
                st.download_button('Download ' + file_name, path.read_bytes(), file_name, key='pilot_' + file_name)
        with st.expander('Coverage, collection errors, and missing fields'):
            st.json(summary)


def instagram_import_panel(activate):
    st.subheader('Instagram · manual CSV only')
    st.info('Instagram API development is deferred while the YouTube milestone is completed. No Meta credentials are required for this offline fallback.')
    st.download_button('Download instagram_posts.csv template', instagram_template(), 'instagram_posts.csv', 'text/csv')
    st.caption('Record verified handle and verification source, post URL, offset-aware publication/collection timestamps, media format, and any exact visible counts. Unknown measurements stay blank. source_method must be manual_public. No comment sentiment or private analytics is inferred.')
    upload = st.file_uploader('Upload instagram_posts.csv', type=['csv'], key='instagram_csv')
    if upload is not None:
        try:
            posts, manifest, quality = import_instagram_csv(upload.getvalue())
        except ValueError as exc:
            st.error(str(exc))
            return
        st.dataframe(posts, hide_index=True, width='stretch')
        st.json(quality, expanded=False)
        if st.button('Activate validated Instagram observations'):
            activate(posts, manifest)
            st.success('Manual Instagram dataset activated. This replaces the active dataset; no API connection is claimed.')


def comment_sentiment_screen(df):
    st.header('Public comment sentiment · separate from caption tone')
    st.warning('Exploratory cue rules, not a validated multilingual model. Downloaded comments are a recent capped sample, not a representative audience survey. Confidence and model accuracy are unavailable until reviewed against human labels.')
    comments = st.session_state.get('comments_dataset')
    if comments is None or comments.empty:
        st.info('No linked public comments are loaded. Load the saved YouTube pilot. Instagram comment sentiment is unavailable through the CSV fallback.')
        return
    sample = linked_comment_sample(df)
    if sample.empty:
        st.info('No downloaded comments match the active post filters.')
        return
    assessed = sample.sentiment_label.ne('unassessed')
    cols = st.columns(3)
    cols[0].metric('Sampled comments', len(sample))
    cols[1].metric('Cue-assessed comments', int(assessed.sum()))
    cols[2].metric('Linked videos', sample.platform_post_id.nunique())
    counts = sample.groupby(['brand', 'sentiment_label']).size().reset_index(name='sampled_comments')
    st.plotly_chart(px.bar(counts, x='brand', y='sampled_comments', color='sentiment_label', barmode='group'), width='stretch')
    st.caption('These counts describe downloaded comments only. Per-post comments metrics include comments not downloaded and may include replies. Caption sentiment must not be compared as the same variable.')
    st.dataframe(sample[['brand', 'platform_post_id', 'comment_text', 'language_inferred', 'sentiment_label', 'sentiment_method']].head(100),
                 hide_index=True, width='stretch')
    review = sample[['comment_id', 'brand', 'comment_text', 'language_inferred', 'sentiment_label']].assign(human_label='')
    st.download_button('Download human-label review sheet', review.to_csv(index=False).encode('utf-8-sig'), 'comment_review.csv', 'text/csv')
    st.subheader('Evaluation against reviewed labels')
    st.caption('Return comment_id and human_label (positive, neutral, negative). Predictions are joined from the active dataset, rather than accepted from the uploaded file. Blank labels are not ground truth.')
    uploaded = st.file_uploader('Upload reviewed comment labels', type=['csv'], key='comment_evaluation')
    if uploaded is not None:
        try:
            labels = read_csv(uploaded.getvalue())
            if not {'comment_id', 'human_label'}.issubset(labels.columns):
                raise ValueError('The review sheet needs comment_id and human_label columns.')
            if labels.comment_id.duplicated().any():
                raise ValueError('Review sheet contains duplicate comment IDs.')
            if not labels.human_label.isin(['', 'positive', 'neutral', 'negative']).all():
                raise ValueError('Use positive, neutral, negative, or blank for human_label.')
            merged = sample.merge(labels[['comment_id', 'human_label']], on='comment_id', how='inner')
            result = evaluation_table(merged)
            if result is None:
                st.info('No human-reviewed labels matched the active sample. No evaluation score was computed.')
            else:
                st.write(f'Reviewed n={result["n"]}; cue coverage={result["coverage"]:.1%}; macro-F1={result["macro_f1"]:.3f} across positive/neutral/negative. Abstentions count as missed true labels. This sample may be small or selectively labeled.')
                st.dataframe(result['confusion_matrix'])
        except ValueError as exc:
            st.error(str(exc))


def linked_comment_sample(df):
    comments = st.session_state.get('comments_dataset')
    if comments is None:
        return pd.DataFrame()
    real = df[df.data_status.eq('real (declared)')]
    keys = set(zip(real.platform.astype(str), real.post_id.astype(str)))
    return comments[[(str(p), str(i)) in keys for p, i in zip(comments.platform, comments.platform_post_id)]].copy()
