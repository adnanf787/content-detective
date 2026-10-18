# How to use Content Detective

The research question is: **What type of social-media content gets Pakistani audiences to engage?** The current project investigates official Pakistan telecom brands on YouTube. It uses 30 real videos, 10 each from Jazz, Zong, and Ufone, plus 279 sampled public top-level comments collected on October 18, 2026. Brand location does not prove the viewers' nationality.

## Web appearance and shortcuts

The web dashboard starts in a soft slate **Dusk** theme, with subtle emerald/teal gradients and floating study banners. The sun/moon button in the top bar switches between Dusk and Light and remembers the choice in this browser. Reduced-motion preferences disable the decorative animation.

Select a brand name in the Overview engagement chart to focus the sample on that brand. **All brands** restores the brand selection while retaining the other filters. Tabs support Left/Right arrow keys and Home/End; Escape closes a dialog or the mobile navigation.

## What is real data, a calculation, or a rule?

- **Real observations:** video IDs, titles/descriptions, publishing dates, source links, available likes, total comment counts, views, channel subscriber snapshots, and sampled comment text come from official YouTube API responses.
- **Calculations:** engagement measures, medians, group sizes, missingness, hashtag frequencies, ages, and comparison tables are computed from the loaded rows and recalculate when you change filters.
- **Configured study choices:** three brands, the publication window, 10 videos per brand, and up to 30 newest top-level comments per video are collection settings, not invented results.
- **Coded rules:** suggested themes, language hints, and sentiment cues use explicit keyword/script rules. They are not a trained model. A rule can miss slang, negation, sarcasm, and mixed language; unassessed text needs review.
- **Recommendation templates:** the wording is structured, while supporting group sizes, medians, and example URLs come from the current data. The app does not currently call a generative AI model.

## Filter sample

Filters apply across the analysis sections and evidence exports:

- **Brands:** study one brand or compare selected brands. Clearing all returns an empty sample.
- **Measure:** choose what the charts compare. Public interactions = likes + total comments. Interactions / 1,000 views = 1,000 × (likes + comments) / views. The follower measure = 100 × (likes + comments) / observed subscriber snapshot. Likes and total comments can also be inspected separately.
- **Limit publication dates:** select which publishing dates enter the analysis.
- **Compare similar video ages:** filter the days between publication and the metric snapshot. Older videos have had more time to accumulate engagement. Unknown ages are excluded when this filter is on.
- **Minimum videos per group:** defaults to five. Recommendations also require at least 80% metric coverage per comparison group. This is a small-sample safeguard, not statistical confidence.

For an illustrative calculation, 20 likes plus 5 total comments on 1,000 views gives 25 interactions per 1,000 views. This does not mean 25 unique people engaged. Shares, saves, reach, and impressions are unavailable and are not filled with zero.

## Overview

- **Study-status panel:** identifies the data source, active video/comment counts, and selected measure. A synthetic import is labeled as such.
- **Videos in view:** number remaining after your filters.
- **Comments sampled:** downloaded comments linked to the selected videos. This differs from the videos' total comment metrics.
- **Brands:** number of distinct brand channels in view.
- **Measure coverage:** percentage of videos with the fields needed for the selected measure. A value of 100% means complete measurement inputs; it does not mean perfect predictions or sentiment accuracy.
- **Observed engagement by brand:** compares each brand's median. Hover for measured group size and coverage. The median is the middle observation after sorting, so an unusually large video has less influence than on the average.
- **Brand coverage:** shows the number of videos from each brand and its share of the filtered sample. These bars represent sample composition, not engagement.
- **Compare distributions and video ages:** expands a plot of individual observations and a table of means, medians, counts, coverage, and age ranges.
- **What this sample can answer:** checks support for the seven assignment questions. YouTube alone cannot establish a cross-platform winner, and post data cannot establish demographic response rates.
- **Next research step:** opens content-label review. Labels are currently missing for the actual pilot and must be reviewed before those comparisons can support recommendations.

The actual pilot has no overlapping observed video-age range across all three brands. Read brand differences as descriptive observations.

## Content

**Topics & language** compares content groups. Choose Rule suggestions to inspect tentative themes and language hints, or Reviewed labels to compare supplied topic, language, creative approach, local context, or media-format labels. Expand group values to see n, mean, median, and coverage. Brand caption tone is available separately; the tone of a brand's text is different from the reaction in comments. The app reads metadata text, not the video's speech, images, or audio.

**Hashtags** extracts tags from the observed text. Usage ranks tags by the number of sampled videos containing them. Engagement association compares eligible tag groups using the selected measure. A tag being common or associated with a high median does not establish that it caused views or is popular throughout Pakistan.

**Timing** converts offset-aware publishing times to Asia/Karachi. Publishing activity shows the number of videos in each weekday/hour cell. Observed engagement shows medians only for adequately measured, repeated cells. Expand the cell table to inspect counts. The actual pilot has no cell with five measured videos, so it cannot currently recommend a best posting slot.

**Video library** lets you search titles/captions, view metrics and ages, open original YouTube sources, and inspect one video's metadata and rule evidence. “Vs brand median” divides a video's selected measure by its own brand's observed median: 1.0 is the median, 2.0 is twice that observed value. It is shown only for adequately measured groups with positive medians and is not a future-view forecast.

## Comments

**Explore comments** shows the sampled-comment counts by brand and cue label. Filter positive cues, negative cues, or Needs review, and search text. Up to 40 matching comments are displayed in the preview; exports retain the full linked sample. No commenter profile fields were requested.

**Current baseline:** 14 positive cues, 9 negative cues, and 256 unassessed comments. Therefore only 23/279, or 8.2%, receive a cue label. Unassessed does not mean neutral.

**Review & evaluate** downloads a review sheet. Fill `human_label` with positive, neutral, or negative after reading each comment, then upload the sheet. IDs must be unique and match the active comments. The app shows evaluation only for genuinely supplied labels: Macro-F1 summarizes performance across the three classes, the confusion matrix shows agreements/errors/abstentions, and rule coverage shows how much text received a cue label. Blank labels are not ground truth. Evaluation uploads calculate scores; they do not train a new model or automatically replace all baseline labels.

The recent capped top-level-comment sample excludes replies and does not represent all viewers' opinions. Comment sentiment does not prove sentiment causes engagement.

## Recommendations

The app proposes content experiments only when comparisons have enough measured observations. Cards link actual source examples and expand to show n, medians, metric definitions, and limitations. “What needs more evidence” explains missing comparisons. A candidate is a next experiment to test, not a guaranteed view increase.

**AI-assisted writing brief:** enter a brand, objective, and creative constraints, then download the brief. It contains your inputs, computed evidence, source examples, and limitations for use with a writing assistant. No AI model is called by this button. Keep variants comparable in platform, product, observation period, and paid promotion.

## Data & methods

**Study & quality** shows source coverage, official-account verification evidence, sampling notes, formulas, missingness, import-quality checks, and provenance. The feature guide is available in an expander here. Missing counts remain unknown; conflicts remain visible but are excluded from analysis.

**Review labels** is a table editor for topic, content type, caption language, caption tone, creative approach, and local context. Source text and metrics are locked. Enter a reviewer/codebook note before saving. Saving recalculates analysis for the entire loaded dataset, not only the active filtered subset. Edits are session-scoped: export your analyzed rows before closing/reloading if you need to retain the reviewed labels. Reloading the saved pilot reads the original source files.

**Collect / import** has two paths. Reload saved YouTube dataset reopens the existing validated snapshot without network requests. Collect a fresh YouTube snapshot uses the local key and official API to create a new observation snapshot; collection only happens when its button is clicked. The report shows actual counts, validation, and errors. For CSV import, download the template, upload documented rows, map column names, declare source/timezone/status/limitations, and validate before activation. The active analysis filters to YouTube.

**Export** downloads the active evidence ZIP, findings report, analyzed videos, linked sampled comments, and JSON analysis summary. The ZIP includes derived tables, quality checks, filters, and the source manifest. The desktop Export research shortcut opens this workspace. Exports preserve unknown values and interpretation limits.

## Suggested assignment workflow

1. Inspect Overview and choose the measure.
2. Review and label the actual videos in Data & methods.
3. Compare reviewed content groups, hashtag usage, and publishing patterns in Content.
4. Read comments and build a real sentiment evaluation sample.
5. Inspect supported experiments in Recommendations and prepare the writing brief.
6. Export the evidence and use its source URLs, sample sizes, and limitations in your presentation.

Instagram, an automatic pasted-video adviser, audiovisual/transcript analysis, demographic inference, and view prediction are not part of the current dashboard. The later adviser can use the collected benchmarks to assess a newly supplied YouTube link once that separate workflow is implemented.
