# Project 1: 🇵🇰 Pakistani Social Media Content Detective

## The story

You are junior digital-marketing data scientists helping a Pakistani brand decide what to post next. Your question is: **What type of social-media content gets Pakistani audiences to engage?**

Collect real observations, clean them, compare engagement patterns, explain the limitations, and turn the strongest findings into a testable marketing recommendation. Sentiment is one explanatory feature alongside format, topics, hashtags, publication time, platform, and any documented audience context.

The supplied brief does not mandate a platform, minimum dataset size, or trained ML model. A clear descriptive investigation is the foundation. No separate attachment was visible in the correcting message; the pasted seven-question brief is the working specification.

## What makes this version distinctive

**Pakistan Content Lab** studies the relationship between engagement and reviewed caption language (Urdu, Roman Urdu, English, mixed), creative approach (tutorials, humour, stories, product demos, offers, questions), and local context (Ramadan, Eid, PSL/cricket, weddings, national occasions, everyday content).

For example: “Within the same account and platform, did Roman Urdu tutorial captions have higher median visible interactions per 1,000 views than English tutorials?” This is an investigation question, not a finding. Only the collected data can answer it. Language describes the caption and cannot identify viewers’ age, city, gender, or nationality.

## Main assignment workflow

1. Choose a sector, such as clothing, food, beauty, or education, and a documented set of relevant accounts. Start with three accounts and 10 recent posts each as a quality pilot. Include consecutive/ordinary posts, not just apparent winners.
2. Gather a common publication window and record observation times. Where possible, observe posts at similar ages. Grow to 150–240 posts only if practical; these numbers are project advice, not course rules. Compare platforms only when two genuinely observed platforms have sufficiently comparable samples.
3. Use exact public observations, authorized exports, or an official API. The app supports manual public observations across platforms, CSV import, and an optional YouTube collector. An API is a collection tool; it is not the project’s distinctive contribution.
4. Review labels using the codebook below. Keep missing counts blank. Save raw observations and source receipts before ending the session.
5. Inspect coverage and address the seven questions. Report “unavailable” when the data cannot answer a question. Public counts alone cannot supply audience geography, age/city segment response rates, reach, retention, or private shares.
6. Form a recommendation with its supporting metric, group sample sizes, observed medians, caveats, and an A/B test. Export the evidence and an optional AI writing prompt. A human reviews any AI wording.

## Small annotation codebook

| Field | Decision rule |
|---|---|
| content_type | The media format: image, carousel, reel, video, text. Verify a platform-specific Short/Reel classification; do not infer it from duration alone. |
| topic | A consistent sector-specific theme, e.g. product explanation, styling, service update. Write the theme definitions before labeling. |
| caption_sentiment | Positive, neutral, negative, or blank if uncertain. Label the caption’s tone, not audience emotion. Have a second reviewer inspect a sample where possible. |
| caption_language | Urdu script; Roman Urdu written in Latin letters; English; Mixed when more than one language carries meaningful content; Other. A hashtag alone need not change the caption language. Leave uncertain cases blank. |
| creative_angle | Choose the dominant approach: tutorial, humour, story, product demo, offer, question, or Other. A reel may use any approach. |
| local_context | Choose a context only if the caption/creative supports it. Everyday means no specific occasion; Other can cover an occasion outside the options. Record ambiguity in reviewer notes rather than guessing. |

## Add-ons after the investigation

| Priority | Add-on | What must exist first |
|---|---|---|
| 1 | **Video-link adviser**: retrieve available caption/tags/counts, review labels, compare with relevant posts, propose hooks/caption/tag experiments. | Real benchmark data and a supported integration for the chosen platform. YouTube link metadata collection is available now; automatic Instagram/TikTok retrieval and per-video benchmark advice are not implemented. |
| 2 | **Pakistan caption studio**: draft Urdu/Roman Urdu/English alternatives grounded in the strongest comparisons. | Evidence export, a chosen AI writing method, and human language review. Current AI brief download prepares the evidence but does not invoke an AI model. |
| 3 | **Experiment tracker**: record two planned variants and compare results after equal observation windows. | Actual follow-up measurements, consistent metrics, and a clear experiment design. |
| 4 | **Comment-theme analysis**: discover recurring questions and purchase objections without storing identities. | Genuine linked comments, permitted access, and evaluated multilingual labeling. |

Automatic “viral scores,” guaranteed views, fabricated audience segments, and universal best posting times are outside the evidentiary scope.

## Current status (updated after the real pilot)

The existing Python project now includes a real official-API telecom pilot: **30 videos (10 each for Jazz, Zong, Ufone) and 279 top-level public comments**, acquired and validated on October 18, 2026 with zero API errors. The user approved extending the common publication window to October 2025–September 2026 after a six-month pilot returned only seven Zong videos. Brand links/IDs are recorded in config/brands.yml. Source JSON, CSV exports, SQLite snapshots, post ages, cue-label review/evaluation, and a real-pilot notebook are available. Caption/comment sentiment are separate and unevaluated. Instagram API work is deferred; its offline CSV validator is fixture-tested without claiming real Instagram access. The earlier web experiment and synthetic educational demo are preserved separately. See YOUTUBE_COLLECTION_LOG.md for actual counts, missing fields, and limitations.
