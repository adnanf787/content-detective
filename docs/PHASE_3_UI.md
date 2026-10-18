# Phase 3: a usable YouTube research workspace

The dashboard answers the assignment's seven research questions with the available evidence. Its five destinations are Overview, Content, Comments, Recommendations, and Data & methods. Instagram is deferred. The saved 30-video / 279-comment study loads automatically; no API request is triggered by opening the dashboard.

## Latest Stitch redesign retrieved on October 18, 2026

The user requested retrieval of the redesigned screen. The existing project now has a second screen: **Content Detective - Interactive Analytical Dashboard**, ID `15bec2f4c90949b5ac3133907cea9405`. Its [screenshot](stitch/redesign-reference.png), [HTML reference](stitch/redesign-reference.html), and [metadata](stitch/redesign-reference.json) were downloaded from Google. The generated HTML was inspected as reference and not executed.

The application now adapts its cool neutral canvas, emerald status panel, metric cards, desktop side rail, and brand composition panel. Desktop navigation uses the same native Streamlit radio control positioned as a side rail above 1100px; narrower screens retain visible top navigation. Invented PTCL/JazzDigital wording and generated dataset/version labels were replaced with real project names and values. No fake query execution or decorative filter controls were copied. [Every feature is explained here](FEATURE_GUIDE.md), also accessible under Data & methods.

## Original UI audit and design reference

The previous interface exposed 15 destinations, repeated methodology notices, and setup controls alongside analysis. The redesign groups related work and puts collection and technical details behind Data & methods. A visible Filter sample button replaces the collapsed-sidebar discovery problem on narrow screens.

Google Stitch generated the reference after the user explicitly approved sharing the UI brief, project title, brand names, and aggregate counts. The brief contains no raw comments, transcripts, or other API credentials. Reference metadata:

- Project: `16620202411574461487`
- Screen: `cd977f44d0cc4604941a914ebc039da1`
- [Approved brief](stitch/design_brief.md)
- [Generated reference](stitch/overview-reference.png)
- [Actual application preview](phase3-overview.jpg)

The generated screen supplied visual direction, not research facts. Its illustrative brand wording and academic labels were replaced with the actual brands and student-friendly language. The downloaded HTML is an inert reference and is not part of the running app. Raw service response files are ignored by Git.

The available design-taste-frontend skill explicitly excludes dashboards from its target interfaces. Its audit-first approach informed inspection, but the implementation uses native Streamlit controls adapted from the Stitch reference. No marketing-page layout or unrelated web framework was introduced.

Visual choices: white/light-neutral canvas, deep emerald `#087755`, charcoal text, restrained dividers, 12px metric corners, small wordmark, and compact headings. Navigation remains visible on narrow screens. Native radio semantics, labels, keyboard navigation, focus indicators, and reduced-motion preferences are preserved. Four desktop summary columns become a 2×2 grid at narrow widths. The 603px in-app viewport was visually checked; wider layouts use Streamlit's native responsive columns but were not separately screenshot-tested.

## Where the work lives

| Earlier area | Current destination |
|---|---|
| Sample overview, distributions, source coverage | Overview; detail in Data & methods |
| Content intelligence, Pakistan content lab, caption tone | Content → Topics & language |
| Hashtags | Content → Hashtags |
| Day/hour analysis | Content → Timing |
| Raw source posts and inspectable links | Content → Video library |
| Public-comment sentiment and evaluation | Comments |
| Recommendation studio and AI writing prompt | Recommendations |
| Content annotation | Data & methods → Review labels |
| Acquisition, import, formulas, quality, exports | Data & methods |

`app.py` delegates to `src/dashboard.py`. Shared loading lives in `src/study_data.py`; Phase 3 summaries in `src/insights.py`; portable evidence exports in `src/research_outputs.py`. Styling is limited to `assets/dashboard.css`. Existing cleaning, normalization, comment annotation, hashtag extraction, and recommendation modules are reused.

## Analysis and interpretation

Run `.venv/bin/python scripts/analyze_youtube.py` to regenerate the derived CSV tables, JSON summary, findings report, and evidence ZIP from the saved real snapshot. This performs validation and local analysis without network calls or source CSV edits. Dashboard exports include active filters and only comments linked to selected source posts.

The primary measure is likes plus total comments per 1,000 observed views, excluding shares. The dashboard also exposes public interactions, follower-snapshot normalization, likes, and total comments when available. The within-brand index divides by that brand's observed median only when at least five measured posts and 80% coverage are available and the median is positive. It is descriptive, not a forecast.

The actual sample contains 10 videos each for Jazz, Zong, and Ufone. It has no overlapping observed video-age range across the three brands. No joint day/hour cell reaches the default five-video threshold. Publishing activity is still visible, while the engagement timing view explains why it cannot recommend a slot. Unknown timezones are excluded.

Content and language rules are review suggestions. Users can supply reviewed topic, language, creative approach, context, and format labels with a reviewer/codebook note. These labels do not establish viewer demographics. Sampled-comment cue rules assign 14 positive and 9 negative labels; 256 comments remain unassessed. Human-label evaluation stays unavailable until a real review sheet is uploaded. No sentiment accuracy, causal lift, demographic response, or guaranteed view increase is claimed.

Recommendations cite sufficiently covered observed groups and source examples. The AI writing-brief download packages measured evidence and creative constraints; it does not send research data to an AI model. A pasted-video adviser remains a later add-on.
