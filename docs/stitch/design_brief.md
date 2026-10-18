# Content Detective: a clear student research dashboard

Create a polished desktop analytics workspace for the existing Python/Streamlit project
“Pakistani Social Media Content Detective”. This is a working research product, not a
marketing landing page. A student needs to understand real YouTube research without
15 competing pages, giant headings, yellow warning walls, or technical setup forms.

Design one OVERVIEW screen with a narrow left rail and an airy, compact main canvas.
Use a consistent white/light-neutral theme, dark charcoal text, one deep emerald accent,
12px panel corners, legible modern sans typography, restrained dividers, no gradients,
no decorative photography or invented logos, and no fake scores or forecasts.

The application has only five main destinations: Overview, Content, Comments,
Recommendations, Data & methods. In the final Streamlit implementation navigation
must also be visible at narrow/mobile widths; design for straightforward native controls.
Use a small “Content Detective” wordmark and Pakistan telecom / YouTube study context.
Preserve the full project title in a small secondary line, rather than a huge hero.

The default screen opens the REAL saved dataset. Aggregate facts are real:
30 YouTube videos, 3 official brand channels (Jazz, Zong, Ufone), 279 sampled top-level
public comments. 10 videos per brand. Zero collection API errors. The common sampling
window is October 2025–September 2026, but actual observed posting dates are March–September 2026.
Metrics: views, likes, and total comment counts are observed on all 30 videos. Shares,
saves, reach, and impressions are unavailable, so do not display invented values.

Place a compact source-status line, five navigation destinations, and a small filter row
(Brands, Measure, optional refinement). Main content: four compact summary metrics
(30 videos; 279 comments sampled; 3 brands; 100% selected-metric coverage), a clear
brand comparison area, source-supported recent/representative video observations, and
a “Next research step” panel that directs the student to review content labels.

Important: Do NOT invent engagement medians or plot made-up numeric bar heights.
For an illustrative layout show a neutral chart placeholder labeled “Measured brand
comparison loads from the dataset” or use only actual video counts Jazz 10 / Zong 10 /
Ufone 10. The final implementation will populate true engagement measures.

Keep one concise limitation near the chart: “Videos have different ages. These are
observed associations, not proof of cause.” Put formula details, raw JSON, collection
controls, developer settings, and full research limitations in Data & methods.

Comments screen is not this overview, but remember the analysis distinguishes brand
caption tone from sampled-comment sentiment. Only 23 of 279 comments match the
unevaluated cue rules; 256 remain unassessed. Never depict all comments as classified.
No viewer demographics, nationality verification, viral score, or guaranteed view lift.

Use concrete short labels, clear alignment, healthy whitespace, visible focus states,
and a comfortable reading hierarchy. The visual direction should be practical to
translate into native Streamlit widgets and real Plotly charts. Return a usable design
reference with layout and typography we can adapt to the existing application.
