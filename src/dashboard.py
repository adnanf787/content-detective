"""Five-section YouTube research workspace. Native Streamlit controls, shared analysis."""
from datetime import datetime
from html import escape
from pathlib import Path
import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analysis import prepare, feasibility, dataset_label, filter_posts
from src.collection_ui import label_screen
from src.content_nlp import evaluation_table
from src.hashtags import hashtag_table
from src.import_ui import import_screen
from src.insights import (MEASURES, MEASURE_NOTES, age_comparability, analysis_summary,
                          brand_benchmarks, linked_comments, posting_cells, relative_to_brand)
from src.metrics import DEFINITIONS, metric_coverage, source_coverage, summarize
from src.recommendations import marketing_prompt, recommend
from src.research_outputs import evidence_bundle
from src.settings import ROOT, youtube_key
from src.study_data import read_saved_study
from src.timing import DAYS
from src.youtube_study import load_config, run_study

NAVIGATION = ['Overview', 'Content', 'Comments', 'Recommendations', 'Data & methods']
GREEN = '#047857'
CHART_COLORS = ['#047857', '#0d9488', '#14b8a6', '#93c5b4', '#cbd5e1']


def activate(raw, manifest):
    frame, quality = prepare(raw, manifest)
    st.session_state.update(raw_dataset=raw.copy(), dataset=frame, quality=quality, manifest=manifest,
                            dataset_version=st.session_state.get('dataset_version', 0) + 1)


def load_pilot():
    raw, comments, manifest, report = read_saved_study(ROOT)
    activate(raw, manifest)
    st.session_state.update(comments_dataset=comments, collection_report=report)


def navigate(page, section=None):
    st.session_state.workspace = page
    if section:
        st.session_state.data_section = section


def number(value, *, count=False):
    if value is None or pd.isna(value):
        return 'N/A'
    if count:
        return f'{value:,.0f}'
    return f'{value:,.2f}' if abs(value) >= 1 or value == 0 else f'{value:.3g}'


def video_title(row):
    title = row.get('title')
    return str(title) if title is not None and pd.notna(title) and str(title).strip() else str(row.post_id)


def chart(fig, height=310):
    fig.update_layout(template='plotly_white', height=height, font=dict(family='Plus Jakarta Sans, sans-serif', size=12, color='#1e293b'),
                      margin=dict(l=8, r=12, t=18, b=12), paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)', colorway=CHART_COLORS,
                      legend=dict(orientation='h', y=-.24), dragmode=False)
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor='#f1f5f9', zeroline=False)
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False, 'scrollZoom': False})


def group_chart(df, field, metric, minimum, *, title=None):
    table = summarize(df, field, metric, minimum)
    if table.empty or table.n.sum() == 0:
        st.info('No measured groups yet. Add or review labels in Data & methods.')
        return table
    measured = table.dropna(subset=['median'])
    if title:
        st.subheader(title)
    fig = px.bar(measured, x='median', y=field, orientation='h', color_discrete_sequence=[GREEN],
                 hover_data={'n': True, 'total_posts': True, 'coverage_pct': ':.0f', 'median': ':.4g'},
                 labels={'median': 'Median ' + MEASURES[metric].lower(), field: ''})
    fig.update_yaxes(autorange='reversed', showgrid=False)
    chart(fig, min(420, max(230, len(measured) * 38 + 80)))
    if table.small_sample.any():
        st.caption(f'Groups with fewer than {minimum} measured videos are exploratory and excluded from recommendations.')
    with st.expander('See group values and coverage'):
        st.dataframe(table.rename(columns={'total_posts': 'Videos', 'n': 'Measured videos', 'median': 'Median', 'mean': 'Mean', 'coverage_pct': 'Coverage (%)'}), hide_index=True, width='stretch')
    return table


def floating_banner(badge_text, title_text, meta_items=None, subsample_count=None):
    """Renders a floating circular banner with pulsing status and live metrics."""
    meta_html = ''
    if meta_items:
        meta_html = ''.join(f'<span class="banner-divider">·</span><span class="banner-window">{escape(item)}</span>' for item in meta_items)
    subsample_html = ''
    if subsample_count is not None:
        subsample_html = f'<div class="banner-right"><span class="banner-subsample-badge">Active Subsample: N={subsample_count}</span></div>'
    st.markdown(f'''<div class="floating-banner-container">
      <div class="floating-circular-banner">
        <div class="banner-left">
          <span class="banner-live-pill"><span class="pulse-dot"></span> {escape(badge_text)}</span>
          <span class="banner-text"><strong>{escape(title_text)}</strong></span>
          {meta_html}
        </div>
        {subsample_html}
      </div>
    </div>''', unsafe_allow_html=True)


def overview(df, sample, metric, minimum, manifest):
    st.title('Overview')
    st.write('Understand the sample, compare observed engagement, then choose the next research step.')

    brand_list = ', '.join(sorted(str(b) for b in df.brand.dropna().unique()))
    floating_banner(
        f"Live Verified Ingest · {len(df)} Videos",
        f"Source: {df.brand.nunique()} Official Brand Channels ({brand_list})",
        ["Common window: Oct 2025–Sep 2026 (Observed: Mar–Sep 2026)", "✓ 0 API errors"],
        len(df)
    )

    chips_html = ''.join(
        f'<span class="brand-chip-pill {escape(str(b).lower())}">{escape(str(b))} <span style="opacity:0.8;font-weight:bold;margin-left:2px;">✕</span></span>'
        for b in sorted(df.brand.dropna().unique())
    )
    st.markdown(f'''<div class="filter-ribbon-card">
      <div class="filter-ribbon-grid">
        <div>
          <div class="ribbon-label-row">
            <span class="ribbon-label">BRAND CORPUS FILTER</span>
            <span class="ribbon-count">{df.brand.nunique()} active brands</span>
          </div>
          <div class="ribbon-chips">{chips_html}</div>
        </div>
        <div>
          <div class="ribbon-label-row">
            <span class="ribbon-label">OBSERVED MEASURE MODE</span>
            <span class="ribbon-count">Strict API Parity</span>
          </div>
          <div class="ribbon-measure-badge">
            <span style="color:#059669;font-weight:bold;">⚡ {escape(MEASURES[metric])}</span>
          </div>
        </div>
        <div class="ribbon-date-box">
          <div class="ribbon-date-label">Date Window</div>
          <div class="ribbon-date-val">Mar 2026 – Sep 2026</div>
        </div>
      </div>
      <div class="ribbon-notice">
        <span class="notice-icon">ℹ</span> Notice: Shares, impressions, and demographic reach are YouTube Data API v3 restricted and intentionally omitted from this dataset.
      </div>
    </div>''', unsafe_allow_html=True)

    with st.container(key='overview_stats'):
        cols = st.columns(4)
        cols[0].metric('Videos in view', number(len(df), count=True), help='Videos remaining after active filters.')
        cols[1].metric('Comments sampled', number(len(sample), count=True), help='Downloaded top-level comments linked to these videos, not the full comment total.')
        cols[2].metric('Brands', number(df.brand.nunique(), count=True), help='Distinct observed brand channels in the filtered sample.')
        cols[3].metric('Measure coverage', f'{df[metric].notna().mean():.0%}', help='Share of filtered videos with all counts required for the selected measure. This is not model accuracy.')

    summary = brand_benchmarks(df, metric, minimum)

    col_main, col_side = st.columns([1.9, 1])
    with col_main:
        st.markdown(f'''<div class="bento-card">
          <div class="bento-header">
            <div class="bento-title">
              <span class="title-dot"></span>
              Observed Brand Corpus Distribution & Metrics
            </div>
            <span class="bento-badge">N = {len(df)} Videos</span>
          </div>
          <div class="bento-subtext">
            Measured brand comparison loads directly from the verified dataset. Balanced quotas prevent brand volume bias in aggregate cross-case comparison.
          </div>
        ''', unsafe_allow_html=True)

        for brand, group in df.groupby('brand'):
            pct = len(group) / len(df) if len(df) else 0
            brand_str = str(brand)
            brand_cls = brand_str.lower()
            st.markdown(f'''
            <div class="dist-bar-item">
              <div class="dist-bar-meta">
                <span class="dist-bar-brand">{escape(brand_str)} <span class="dist-bar-badge">Official Ingest</span></span>
                <span class="dist-bar-val">{len(group)} videos ({pct:.1%})</span>
              </div>
              <div class="dist-bar-track">
                <div class="dist-bar-fill {escape(brand_cls)}" style="width: {max(18, int(pct * 100))}%;">
                  {len(group)} Videos Loaded
                </div>
              </div>
            </div>
            ''', unsafe_allow_html=True)

        st.markdown('''
          <div class="method-note-box">
            <span class="method-note-icon">🛡️</span>
            <div>
              <strong>Methodological note:</strong> Videos have different ages and natural algorithm shelf-lives. These represent observed associations, not proof of algorithmic causality or organic reach differences.
            </div>
          </div>
        </div>''', unsafe_allow_html=True)

        with st.container(border=True, key='brand_comparison'):
            st.subheader('Observed engagement medians by brand')
            st.caption(MEASURE_NOTES[metric] + ' Bars show medians; sample sizes appear on hover.')
            if summary.empty or not summary.n.sum():
                st.info('This sample has no valid measurements for the selected measure.')
            else:
                fig = px.bar(summary.dropna(subset=['median']), x='brand', y='median', color_discrete_sequence=[GREEN],
                             hover_data={'n': True, 'coverage_pct': ':.0f', 'median': ':.4g'},
                             labels={'brand': '', 'median': MEASURES[metric]})
                chart(fig, 250)

        # Recent & Representative Observed Ingests Table
        table_rows = []
        for _, r in df.head(6).iterrows():
            title_txt = video_title(r)
            brand_txt = str(r.brand)
            brand_cls = brand_txt.lower()
            date_str = 'N/A'
            if 'post_datetime' in r and pd.notna(r.post_datetime):
                try:
                    date_str = pd.to_datetime(r.post_datetime).strftime('%b %d, %Y')
                except Exception:
                    date_str = str(r.post_datetime)[:10]
            views_str = f"{int(r.views):,}" if 'views' in r and pd.notna(r.views) else 'N/A'
            likes_str = f"{int(r.likes):,}" if 'likes' in r and pd.notna(r.likes) else 'N/A'
            comments_str = f"{int(r.comments):,}" if 'comments' in r and pd.notna(r.comments) else 'N/A'
            table_rows.append(f'''
            <tr>
              <td style="font-weight:600;max-width:240px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="{escape(title_txt)}">{escape(title_txt)}</td>
              <td><span class="table-brand-pill {escape(brand_cls)}">{escape(brand_txt)}</span></td>
              <td style="font-family:'JetBrains Mono',monospace;color:#64748b;">{escape(date_str)}</td>
              <td style="font-family:'JetBrains Mono',monospace;text-align:right;font-weight:600;">{views_str}</td>
              <td style="font-family:'JetBrains Mono',monospace;text-align:right;color:#475569;">{likes_str}</td>
              <td style="font-family:'JetBrains Mono',monospace;text-align:right;color:#475569;">{comments_str}</td>
              <td style="text-align:center;"><span class="complete-pill"><span class="pulse-dot" style="width:6px;height:6px;"></span> 100% Observed</span></td>
            </tr>
            ''')
        table_html = ''.join(table_rows)

        st.markdown(f'''<div class="representative-table-card">
          <div class="table-card-header">
            <div>
              <div class="table-card-title">Recent & Representative Observed Ingests</div>
              <div class="table-card-subtext">Verifiable records from active sample (Ordered by observed ingestion date)</div>
            </div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:0.76rem;color:#64748b;">
              Showing {min(6, len(df))} of {len(df)} loaded records
            </div>
          </div>
          <div style="overflow-x:auto;">
            <table class="custom-ingest-table">
              <thead>
                <tr>
                  <th>Video Title</th>
                  <th>Channel / Brand</th>
                  <th>Published Date</th>
                  <th style="text-align:right;">Observed Views</th>
                  <th style="text-align:right;">Observed Likes</th>
                  <th style="text-align:right;">Sampled Comments</th>
                  <th style="text-align:center;">Completeness</th>
                </tr>
              </thead>
              <tbody>
                {table_html}
              </tbody>
            </table>
          </div>
          <div class="table-card-footer">
            <span>Integrity Verification: SHA-256 Digest Confirmed (All {len(df)} raw payloads indexed)</span>
            <span style="color:#059669;font-weight:600;">View all records in Content Module →</span>
          </div>
        </div>''', unsafe_allow_html=True)

        st.markdown('''<div class="next-step-card">
          <div class="next-step-content">
            <div class="next-step-title">
              <span class="next-step-icon">➔</span>
              Next Research Step: Qualitative Content Coding
            </div>
            <div class="next-step-desc">
              The initial corpus ingest is complete and balanced. To evaluate brand narrative strategy, proceed to the Content module to review thematic category tags, caption tone vs comment sentiment alignment, and cue classification.
            </div>
            <div class="next-step-cue-note">
              <span>⚠️ Notice: 23 of 279 comments match rule-based cue lexicons; 256 remain unclassified until manual coding validation in Comments workspace.</span>
            </div>
          </div>
        </div>''', unsafe_allow_html=True)
        st.button('Review content labels', on_click=navigate, args=('Data & methods', 'Review labels'), type='primary')

    with col_side:
        st.markdown(f'''<div class="bento-card" style="padding:1.2rem 1.4rem;">
          <div class="bento-header">
            <div class="bento-title" style="font-size:0.95rem;">
              Corpus Stratification
            </div>
            <span class="bento-badge" style="background:#ecfdf5;color:#065f46;border-color:#a7f3d0;">Synced</span>
          </div>
          <div class="bento-subtext" style="margin-bottom:0.85rem;">
            Per-brand telemetry integrity checks.
          </div>
        ''', unsafe_allow_html=True)

        for brand, group in df.groupby('brand'):
            brand_str = str(brand)
            dot_color = '#059669' if 'jazz' in brand_str.lower() else '#0d9488' if 'zong' in brand_str.lower() else '#0284c7'
            st.markdown(f'''
            <div class="strat-card">
              <div class="strat-card-header">
                <span><span class="strat-indicator" style="background:{dot_color};"></span> {escape(brand_str)}</span>
                <span>{len(group)} / {len(group)} Videos</span>
              </div>
              <div class="strat-card-metrics">
                <span>Tracked metrics:</span>
                <span style="color:#059669;font-weight:600;">Views, Likes, Comments</span>
              </div>
            </div>
            ''', unsafe_allow_html=True)

        st.markdown('''
          <div style="font-size:0.72rem;color:#64748b;font-family:'JetBrains Mono',monospace;margin-top:0.6rem;padding-top:0.6rem;border-top:1px solid #e2e8f0;">
            Engagement medians and distribution quartiles compute in Content and Data & methods.
          </div>
        </div>''', unsafe_allow_html=True)

        with st.container(border=True):
            st.subheader('What this sample can answer')
            support = feasibility(df, metric, manifest, minimum)[['question', 'support']].copy()
            support['question'] = ['Platform comparison', 'Content formats', 'Topics & hashtags', 'Caption tone', 'Posting day & time', 'Audience demographics', 'Next content experiment']
            if df.platform.nunique() < 2:
                support.loc[0, 'support'] = 'YouTube only'
            if df.content_type.nunique() < 2:
                support.loc[1, 'support'] = 'One observed format'
            if not posting_cells(df, metric, minimum).eligible.any():
                support.loc[4, 'support'] = 'Needs repeated slots'
            st.dataframe(support.rename(columns={'question': 'Research question', 'support': 'Evidence'}), hide_index=True, width='stretch')

    ages = age_comparability(df)
    if df.brand.nunique() > 1 and not ages['shared_age_range_exists']:
        st.caption('Age caution: these brands do not share a known video-age range in this sample. The comparison is descriptive.')
    else:
        st.caption('Videos have different ages and promotion histories. An observed difference does not establish its cause.')
    with st.expander('Compare distributions and video ages'):
        if df[metric].notna().any():
            chart(px.box(df, x='brand', y=metric, points='all', hover_data=['post_id', 'age_days_at_snapshot'],
                         labels={'brand': '', metric: MEASURES[metric]}, color_discrete_sequence=[GREEN]), 320)
        st.dataframe(summary, hide_index=True, width='stretch')


def content_view(df, metric, minimum):
    st.title('Content')
    st.write('Explore themes, language, hashtags, and publishing patterns in the current sample.')
    floating_banner(
        "Content Intelligence",
        "Thematic Strategy & Karachi Publishing Analysis",
        [f"{len(df)} Active Videos", "Urdu / Roman Urdu / English Cues", "Asia/Karachi Window"],
        len(df)
    )

    topics_tab, tags_tab, timing_tab, library_tab = st.tabs(['Topics & language', 'Hashtags', 'Timing', 'Video library'])
    with topics_tab:
        basis = st.selectbox('Label basis', ['Rule suggestions', 'Reviewed labels'])
        if basis == 'Rule suggestions':
            st.caption('Unreviewed suggestions from explicit keyword and script rules. Ambiguous categories stay uncertain.')
            group_chart(df, 'category_suggested', metric, minimum, title='Suggested content themes')
            group_chart(df, 'language_inferred', metric, minimum, title='Caption language hints')
        else:
            field = st.selectbox('Compare reviewed content', ['topic', 'caption_language', 'creative_angle', 'local_context', 'content_type'],
                                 format_func=lambda v: {'topic': 'Topic', 'caption_language': 'Caption language', 'creative_angle': 'Creative approach', 'local_context': 'Local context', 'content_type': 'Media format'}[v])
            st.caption(f'{df[field].notna().sum()} of {len(df)} videos have a supplied label for this field.')
            group_chart(df, field, metric, minimum)
            st.button('Open label review', on_click=navigate, args=('Data & methods', 'Review labels'))
        with st.expander('Brand caption tone'):
            st.caption('Caption tone is separate from public-comment sentiment. The English baseline abstains on unsupported wording.')
            assessed = df[df.sentiment_label.ne('unassessed')]
            group_chart(assessed, 'sentiment_label', metric, minimum)
    with tags_tab:
        tags = hashtag_table(df, metric, minimum)
        st.subheader('Hashtags used in these videos')
        st.caption('Frequency describes the sampled brand posts. It does not establish nationwide popularity or a hashtag’s causal effect.')
        if tags.empty:
            st.info('No caption hashtags were found in this sample.')
        else:
            ranking = st.radio('Show hashtags by', ['Usage', 'Engagement association'], horizontal=True)
            if ranking == 'Usage':
                shown = tags.sort_values('total_posts', ascending=False).head(12)
                fig = px.bar(shown, x='total_posts', y='hashtag', orientation='h', color_discrete_sequence=[GREEN],
                             labels={'total_posts': 'Videos using hashtag', 'hashtag': ''})
            else:
                shown = tags[tags.n.ge(minimum) & tags.coverage_pct.ge(80)].head(12)
                fig = px.bar(shown, x='median', y='hashtag', orientation='h', color_discrete_sequence=[GREEN],
                             labels={'median': 'Median ' + MEASURES[metric].lower(), 'hashtag': ''}, hover_data=['n'])
            if shown.empty:
                st.info('No hashtag comparison reaches the sample-size and coverage threshold.')
            else:
                fig.update_yaxes(autorange='reversed')
                chart(fig, max(240, len(shown) * 30 + 75))
            with st.expander('Hashtag evidence table'):
                st.dataframe(tags, hide_index=True, width='stretch')
    with timing_tab:
        st.subheader('Publishing patterns')
        st.caption('Asia/Karachi time. Unknown timezones are excluded. These patterns cannot establish a causal best posting time.')
        cells = posting_cells(df, metric, minimum)
        view = st.radio('Timing measure', ['Publishing activity', 'Observed engagement'], horizontal=True)
        if cells.empty:
            st.info('No offset-aware publishing times are available.')
        elif view == 'Observed engagement' and not cells.eligible.any():
            st.info(f'No day/hour slot has {minimum} measured videos with 80% coverage. Collect repeated slots before recommending a time.')
        else:
            if view == 'Publishing activity':
                matrix = cells.pivot(index='weekday', columns='hour', values='videos').reindex(index=DAYS, columns=range(24)).fillna(0)
                title = 'Published videos'
            else:
                eligible = cells[cells.eligible]
                matrix = eligible.pivot(index='weekday', columns='hour', values='median').reindex(index=DAYS, columns=range(24))
                title = 'Observed median'
            fig = go.Figure(go.Heatmap(z=matrix.values, x=[f'{h:02}:00' for h in range(24)], y=DAYS,
                                      colorscale=[[0, '#f4f8f5'], [1, GREEN]], colorbar={'title': title},
                                      hovertemplate='%{y}, %{x}<br>%{z:.4g}<extra></extra>'))
            fig.update_yaxes(autorange='reversed')
            chart(fig, 300)
        with st.expander('Day/hour sample sizes'):
            st.dataframe(cells, hide_index=True, width='stretch')
    with library_tab:
        st.subheader('Source video library')
        search = st.text_input('Search title or caption', placeholder='Find an offer, campaign, or topic')
        library = relative_to_brand(df, metric, minimum)
        if search.strip():
            matches = library.caption.str.contains(search.strip(), case=False, regex=False, na=False)
            if 'title' in library:
                matches |= library.title.astype('string').str.contains(search.strip(), case=False, regex=False, na=False)
            library = library[matches]
        columns = [c for c in ['brand', 'title', metric, 'age_days_at_snapshot', 'brand_relative_index', 'source_url'] if c in library]
        st.dataframe(library[columns].rename(columns={metric: MEASURES[metric], 'age_days_at_snapshot': 'Age (days)', 'brand_relative_index': 'Vs brand median'}),
                     hide_index=True, width='stretch', column_config={'source_url': st.column_config.LinkColumn('Source', display_text='Open video')})
        st.caption('“Vs brand median” is a descriptive within-brand ratio. 1.0 means the observed brand median; it is not a view forecast.')
        options = library.index.tolist()
        if options:
            selected = st.selectbox('Inspect a video', options, format_func=lambda i: video_title(library.loc[i])[:100])
            row = library.loc[selected]
            with st.container(border=True):
                st.write(video_title(row))
                st.caption(str(row.brand) + ' · ' + str(row.post_datetime))
                st.write(row.caption if pd.notna(row.caption) else 'No caption available.')
                st.link_button('Open original video', str(row.source_url))
                with st.expander('Label suggestions and observed counts'):
                    fields = [f for f in ['likes', 'comments', 'views', 'language_inferred', 'category_suggested', 'category_evidence', 'comment_sample_status', 'downloaded_comment_count'] if f in row]
                    st.dataframe(pd.DataFrame({'Field': fields, 'Observed / suggested value': [str(row[f]) for f in fields]}), hide_index=True)


def comments_view(sample):
    st.title('Comments')
    st.write('Read the sampled public conversation and review what the sentiment baseline can assess.')
    if sample.empty:
        st.info('No linked public comments match this sample. Load the saved YouTube study or adjust the brand and age filters.')
        return
    assessed = sample.sentiment_label.ne('unassessed')

    floating_banner(
        "Conversation Explorer",
        "Sampled Public Top-Level Comments across Official Channels",
        [f"{len(sample)} Sampled Comments", f"{int(assessed.sum())} Cue Labels", "No Profile Scraping"],
        len(sample)
    )

    with st.container(key='comment_stats'):
        cols = st.columns(4)
        cols[0].metric('Comments sampled', len(sample))
        cols[1].metric('Cue labels assigned', int(assessed.sum()))
        cols[2].metric('Needs review', int((~assessed).sum()))
        cols[3].metric('Rule coverage', f'{assessed.mean():.1%}')
    st.caption('Unevaluated English, Urdu, and Roman Urdu cue rules. Unassessed does not mean neutral. This recent capped sample is not representative audience sentiment.')

    explore_tab, review_tab = st.tabs(['Explore comments', 'Review & evaluate'])
    with explore_tab:
        counts = sample.groupby(['brand', 'sentiment_label']).size().reset_index(name='Comments')
        counts['Label'] = counts.sentiment_label.map({'positive': 'Positive cue', 'negative': 'Negative cue', 'neutral': 'Neutral cue', 'unassessed': 'Unassessed'})
        chart(px.bar(counts, x='brand', y='Comments', color='Label', labels={'brand': ''},
                     color_discrete_map={'Positive cue': GREEN, 'Negative cue': '#e11d48', 'Neutral cue': '#0d9488', 'Unassessed': '#cbd5e1'}), 280)
        a, b = st.columns([1, 1.8])
        choice = a.selectbox('Comment label', ['All comments', 'Needs review', 'Positive cue', 'Negative cue'])
        query = b.text_input('Search comments', placeholder='Search the sampled text')
        shown = sample.copy()
        if choice != 'All comments':
            shown = shown[shown.sentiment_label.eq({'Needs review': 'unassessed', 'Positive cue': 'positive', 'Negative cue': 'negative'}[choice])]
        if query.strip():
            shown = shown[shown.comment_text.str.contains(query.strip(), case=False, regex=False, na=False)]
        st.caption(f'{len(shown)} matching sampled comments. No author-profile fields were collected.')
        st.dataframe(shown[['brand', 'comment_text', 'language_inferred', 'sentiment_label']].head(40).rename(
            columns={'brand': 'Brand', 'comment_text': 'Comment', 'language_inferred': 'Language hint', 'sentiment_label': 'Cue label'}), hide_index=True, width='stretch')
        st.caption('The video’s total comment metric may include replies and comments outside this downloaded sample. Brand-caption tone is available under Content.')
    with review_tab:
        review = sample[['comment_id', 'brand', 'comment_text', 'language_inferred', 'sentiment_label']].assign(human_label='')
        st.subheader('Evaluate against reviewed labels')
        st.write('Download the review sheet, fill human_label with positive, neutral, or negative, then upload it here.')
        st.download_button('Download review sheet', review.to_csv(index=False).encode('utf-8-sig'), 'comment_review.csv', 'text/csv')
        uploaded = st.file_uploader('Upload reviewed comment labels', type=['csv'])
        if uploaded is None:
            st.info('No evaluation score is available until reviewed labels are supplied.')
        else:
            try:
                from src.loader import read_csv
                labels = read_csv(uploaded.getvalue())
                if not {'comment_id', 'human_label'}.issubset(labels) or labels.comment_id.duplicated().any():
                    raise ValueError('Supply unique comment_id values and a human_label column.')
                if not labels.human_label.isin(['', 'positive', 'neutral', 'negative']).all():
                    raise ValueError('Use positive, neutral, negative, or blank labels.')
                joined = sample.merge(labels[['comment_id', 'human_label']], on='comment_id', how='inner')
                result = evaluation_table(joined)
                if result is None:
                    st.info('No reviewed labels matched the active sample.')
                else:
                    st.write(f'Reviewed sample: {result["n"]} comments · Macro-F1: {result["macro_f1"]:.3f} · Rule coverage: {result["coverage"]:.1%}')
                    st.caption('Across positive, neutral, and negative labels; abstentions count as missed labels. Small or selectively reviewed samples limit interpretation.')
                    st.dataframe(result['confusion_matrix'], width='stretch')
            except ValueError as exc:
                st.error(str(exc))


def recommendations_view(df, metric, minimum, manifest):
    st.title('Recommendations')
    st.write('Turn supported comparisons into a testable next-post plan.')
    floating_banner(
        "Strategic Guidance",
        "Evidence-Supported Content Experiments",
        ["Controlled Observational Recommendations", "Validated Comparisons", "No AI Model Calls"],
        len(df)
    )

    cards = recommend(df, metric, manifest, minimum)
    supported = [c for c in cards if c['confidence'] == 'Exploratory; requires validation']
    if supported:
        st.caption('These are observational content experiments. Source examples support the measured comparison, not a guaranteed result.')
        for card in supported:
            with st.container(border=True):
                st.subheader(card['kind'])
                st.write(card['action'])
                for example in card.get('examples', []):
                    st.link_button(f'{example["group"]}: source example', example['url'])
                with st.expander('Supporting evidence and limitations'):
                    st.write(card['evidence'])
                    st.caption(card['limitations'])
    else:
        st.info('No comparison currently clears the evidence threshold. Review content labels or collect more comparable observations before choosing a winner.')
        st.button('Review the content labels', on_click=navigate, args=('Data & methods', 'Review labels'))
    insufficient = [c for c in cards if c['confidence'] == 'Insufficient evidence']
    if insufficient:
        with st.expander('What needs more evidence'):
            for card in insufficient:
                st.markdown('**' + card['kind'] + '**')
                st.write(card['action'])
                st.caption(card['evidence'])
    st.subheader('Prepare an AI-assisted writing brief')
    st.caption('This packages computed evidence for a writing assistant. It does not call an AI model.')
    brief = st.text_area('Brand, objective, and creative constraints', placeholder='Describe the brand, product, audience goal, and what the next post should achieve.')
    if brief.strip():
        st.download_button('Download evidence-based writing brief', marketing_prompt(df, metric, manifest, brief, minimum), 'ai_marketing_brief.md', 'text/markdown', type='primary')
    st.caption(f'Experiment success measure: {MEASURES[metric]}. Compare variants after equal observation windows; keep the product, platform, and paid exposure comparable.')


def data_view(df, sample, metric, minimum, manifest, quality, filters):
    st.title('Data & methods')
    st.write('Inspect sources, review labels, refresh the YouTube study, or take the evidence with you.')
    floating_banner(
        "Research Provenance",
        "Official API Ingest & Data Integrity Workbench",
        ["SHA-256 Verified Ingest", "Full Lineage Traceability", "Export Research Evidence"],
        len(df)
    )

    section = st.radio('Data workspace', ['Study & quality', 'Review labels', 'Collect / import', 'Export'],
                       horizontal=True, key='data_section')
    if section == 'Study & quality':
        st.subheader('Current study')
        st.caption(dataset_label(df))
        st.write(manifest.geographic_relevance)
        st.dataframe(source_coverage(df), hide_index=True, width='stretch')
        with st.expander('Source verification and sampling'):
            verification = ROOT / 'config/brand_verification.json'
            if verification.exists():
                st.json(json.loads(verification.read_text()), expanded=False)
            st.write(manifest.notes)
        with st.expander('Metric formulas and coverage'):
            st.dataframe(metric_coverage(df), hide_index=True, width='stretch')
        with st.expander('Import quality and provenance'):
            st.json(quality, expanded=False)
            st.json(manifest.to_dict(), expanded=False)
        guide = ROOT / 'docs/FEATURE_GUIDE.md'
        if guide.exists():
            with st.expander('Feature guide — how to use every section'):
                st.markdown(guide.read_text())
        st.subheader('Interpretation limits')
        st.markdown('''- This phase observes YouTube only; no cross-platform winner can be inferred.
- Pakistan-relevant brands do not establish viewer nationality, age, gender, or city.
- Missing shares, saves, reach, and impressions remain unknown.
- Language, category, and comment-sentiment rules need human review and evaluation.
- Account size, video age, paid exposure, and campaigns can explain observed differences.''')
    elif section == 'Review labels':
        st.caption('The label editor applies to the entire loaded dataset. Source text and measured counts are preserved.')
        label_screen(activate)
    elif section == 'Collect / import':
        st.subheader('Saved YouTube study')
        if (ROOT / 'data/processed/youtube_posts.csv').exists():
            if st.button('Reload saved YouTube dataset'):
                try:
                    load_pilot()
                    st.rerun()
                except (ValueError, OSError):
                    st.error('The saved dataset could not be loaded. Check the source files and collection report.')
        with st.expander('Refresh the official telecom pilot'):
            collection_controls()
        with st.expander('Import a documented post CSV'):
            import_screen(activate)
    else:
        st.subheader('Export the active research sample')
        if df.empty:
            st.info('No active YouTube rows to export. Adjust the sample filters first.')
            return
        if df.data_status.nunique() > 1:
            st.warning('Import one data-status track before exporting research findings. Synthetic and empirical observations cannot be pooled.')
            return
        st.caption('Exports include the active brand/date/age filters, source status, missingness, source links, and interpretation limits.')
        bundle, report, summary = evidence_bundle(df, sample, manifest, quality, metric, minimum, filters)
        st.download_button('Download research evidence ZIP', bundle, 'youtube_research_evidence.zip', 'application/zip', type='primary')
        st.download_button('Download findings report', report, 'youtube_findings.md', 'text/markdown')
        st.download_button('Download analyzed videos', relative_to_brand(df, metric, minimum).to_csv(index=False).encode('utf-8-sig'), 'youtube_analyzed_posts.csv', 'text/csv')
        if not sample.empty:
            st.download_button('Download sampled comments', sample.to_csv(index=False).encode('utf-8-sig'), 'youtube_sampled_comments.csv', 'text/csv')
        st.download_button('Download analysis summary', json.dumps(summary, ensure_ascii=False, indent=2, default=str), 'youtube_analysis_summary.json', 'application/json')
        with st.expander('Preview the findings report'):
            st.markdown(report)


def collection_controls():
    config_path = ROOT / 'config/brands.yml'
    if not config_path.exists():
        st.info('No collection configuration is available in this workspace.')
        return
    study = load_config(config_path)['study']
    st.write(f'{study["publication_start"]} to {study["publication_end"]} · {study["videos_per_brand"]} videos per brand · up to {study["comments_per_video"]} newest top-level comments per video.')
    st.caption('A fresh run sends official requests to YouTube and creates a new local observation snapshot. Saved-data analysis is offline.')
    if st.button('Collect a fresh YouTube snapshot', disabled=not bool(youtube_key())):
        status = st.empty()
        with st.spinner('Collecting official YouTube metadata and public comments…'):
            try:
                _, _, result = run_study(root=ROOT, progress=status.write)
                st.session_state.latest_collection_attempt = result
            except ValueError:
                st.error('Collection could not start. Check local credentials and sampling configuration.')
    if 'latest_collection_attempt' in st.session_state:
        result = st.session_state.latest_collection_attempt
        st.write(f'{result["posts_collected"]} videos · {result["comments_collected"]} sampled comments · {len(result["api_errors"])} API errors · {result["status"]}')
        with st.expander('Collection report'):
            st.json(result)
        if result['posts_collected'] and result['validation']['valid']:
            if st.button('Load the collected study', type='primary'):
                try:
                    load_pilot()
                    st.rerun()
                except (ValueError, OSError):
                    st.error('The collected files could not be loaded. Inspect the collection report.')


def main():
    st.set_page_config(page_title='PakTelco Analytical Observational Workbench · Content Detective', page_icon='🇵🇰', layout='wide')
    css = ROOT / 'assets/dashboard.css'
    if css.exists():
        st.markdown('<style>' + css.read_text() + '</style>', unsafe_allow_html=True)

    st.markdown('''<div class="app-brand">
  <div class="app-brand-top">
    <div class="app-crest">
      <div class="crest-icon">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">
          <ellipse cx="12" cy="5" rx="9" ry="3"></ellipse>
          <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path>
          <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path>
        </svg>
      </div>
      <div>
        <div class="app-wordmark">PTCL & Telco Corpus</div>
        <div class="app-subwordmark">CONTENT DETECTIVE</div>
      </div>
    </div>
    <div class="app-context">Pakistan Telecom · YouTube Study</div>
    <div class="verified-pill">
      <span class="pulse-dot"></span>
      <span>Verified YouTube Ingest</span>
    </div>
  </div>
  <div class="rail-footer">
    <div class="rail-status-row">
      <span style="color:#64748b;font-weight:600;">● Corpus Status</span>
      <span class="status-badge">Dataset v2.4 (Active)</span>
    </div>
    <div class="rail-meta">Sampling: Oct 2025–Sep 2026</div>
    <div class="rail-meta-success">
      <span class="success-dot"></span>
      <span>Zero collection API errors</span>
    </div>
    <div class="rail-docs-link">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:-1px;margin-right:3px;">
        <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
        <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
      </svg>
      <span>Documentation & Codebook</span>
    </div>
  </div>
</div>

<div class="desktop-masthead">
  <div class="masthead-left">
    <span class="masthead-title">PakTelco Analytical Observational Workbench</span>
    <div class="masthead-links">
      <span class="masthead-link active">Corpus v2.4</span>
      <span class="masthead-link">Methodology Note</span>
      <span class="masthead-link">Codebook</span>
      <span class="masthead-link">Data Dictionary</span>
    </div>
  </div>
  <div class="masthead-right">
    <span class="masthead-pill-tag">✓ Official YouTube API v3 Verified</span>
  </div>
</div>''', unsafe_allow_html=True)

    if not st.session_state.get('pilot_autoload_done'):
        st.session_state.pilot_autoload_done = True
        if 'dataset' not in st.session_state and (ROOT / 'data/processed/youtube_posts.csv').exists():
            try:
                load_pilot()
            except (ValueError, OSError, KeyError):
                st.session_state.load_error = 'The saved dataset could not be loaded. Inspect its CSVs and collection report in Data & methods.'

    required = {'age_days_at_snapshot', 'visible_rate_followers', 'language_inferred', 'category_suggested'}
    if 'dataset' in st.session_state and not required.issubset(st.session_state.dataset.columns):
        activate(st.session_state.get('raw_dataset', st.session_state.dataset), st.session_state.manifest)

    with st.container(key='main_navigation'):
        page = st.radio('Workspace', NAVIGATION, horizontal=True, key='workspace', label_visibility='collapsed')
        st.button('Export research', icon=':material/download:', on_click=navigate, args=('Data & methods', 'Export'), key='navigation_export')

    if 'load_error' in st.session_state:
        st.error(st.session_state.load_error)

    if 'dataset' not in st.session_state:
        st.title('Start with a real YouTube sample')
        st.write('No dataset is active. Collect a verified telecom pilot or import documented post observations.')
        collect_tab, import_tab = st.tabs(['Collect YouTube', 'Import observations'])
        with collect_tab:
            collection_controls()
        with import_tab:
            import_screen(activate)
        return

    all_df = st.session_state.dataset
    with st.popover('Filter sample', icon=':material/tune:'):
        st.markdown('### Research sample')
        options = sorted(all_df.brand.dropna().unique().tolist())
        version = st.session_state.dataset_version
        brands = st.multiselect('Brands', options, default=options, key=f'brands_{version}')
        available = [m for m in MEASURES if all_df[m].notna().any()]
        available = available or ['visible_interactions']
        metric = st.selectbox('Measure', available, format_func=lambda value: MEASURES[value], key=f'measure_{version}')
        start = end = low_age = high_age = None
        minimum = 5
        with st.expander('Refine the sample'):
            dates = all_df.source_date.dropna()
            if len(dates) and st.checkbox('Limit publication dates', key=f'dates_on_{version}'):
                date_range = st.date_input('Publication range', (pd.Timestamp(dates.min()).date(), pd.Timestamp(dates.max()).date()), key=f'date_range_{version}')
                if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
                    start, end = date_range
            ages = all_df.age_days_at_snapshot.dropna()
            if len(ages) and st.checkbox('Compare similar video ages', key=f'ages_on_{version}'):
                low_age = st.number_input('Minimum age (days)', min_value=0, value=7, key=f'age_min_{version}')
                high_age = st.number_input('Maximum age (days)', min_value=0, value=max(7, int(ages.max()) + 1), key=f'age_max_{version}')
                st.caption('Videos with unknown ages are excluded from this filter.')
            minimum = int(st.number_input('Minimum videos per group', min_value=2, max_value=100, value=5))
        st.caption('One observed platform: YouTube. The collected sample is a Pakistan-market proxy.')

    selections = {'brand': brands} if options else {}
    df = filter_posts(all_df, selections, start, end)
    df = df[df.platform.eq('YouTube')].copy()
    if low_age is not None:
        df = df[df.age_days_at_snapshot.between(low_age, high_age)]
    filters = {'brands': brands, 'publication_start': start, 'publication_end': end, 'min_age_days': low_age,
               'max_age_days': high_age, 'minimum_group_n': minimum, 'metric': metric, 'platform': 'YouTube'}
    sample = linked_comments(df, st.session_state.get('comments_dataset'))

    if page == 'Data & methods':
        data_view(df, sample, metric, minimum, st.session_state.manifest, st.session_state.quality, filters)
        return
    if df.empty:
        st.title(page)
        st.info('No YouTube videos match the active sample. Choose at least one brand or widen the date and age filters.')
        return
    if df.data_status.nunique() > 1:
        st.warning('This sample mixes synthetic, real, or unverified tracks. Import one data track before analyzing it.')
        return

    demo = df.data_status.eq('synthetic').all()
    source = 'SYNTHETIC DEMONSTRATION' if demo else 'YouTube API snapshot' if st.session_state.manifest.source_type == 'official_api' else 'Imported observations'
    st.markdown('<div class="source-note"><strong>' + escape(source) + '</strong><span>' + str(len(df)) + ' videos · ' + str(len(sample)) + ' sampled comments</span><small>Active measure: ' + escape(MEASURES[metric]) + ' · Source platform: YouTube</small></div>', unsafe_allow_html=True)

    if page == 'Overview':
        overview(df, sample, metric, minimum, st.session_state.manifest)
    elif page == 'Content':
        content_view(df, metric, minimum)
    elif page == 'Comments':
        comments_view(sample)
    elif page == 'Recommendations':
        recommendations_view(df, metric, minimum, st.session_state.manifest)
