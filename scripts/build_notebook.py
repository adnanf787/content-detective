"""Create the educational notebook; analytics stay in shared src modules."""
from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
nb = nbf.v4.new_notebook()
nb.metadata.kernelspec = dict(display_name='Python 3', language='python', name='python3')
nb.cells = [
    nbf.v4.new_markdown_cell('''# Pakistani Social Media Content Detective 🇵🇰

**SYNTHETIC DEMONSTRATION ONLY.** No empirical claims about Pakistani audiences are established here.

Business question: What type of social-media content gets Pakistani audiences to engage?

This notebook runs the same import, cleaning, EDA, caption sentiment, and recommendation code used by the dashboard. Run all cells from this directory or the repository root. Replace the input path **and manifest** only after inspecting a genuine dataset and its provenance.'''),
    nbf.v4.new_code_cell('''from pathlib import Path
import sys
import json
import pandas as pd
import plotly.express as px
from IPython.display import display, Markdown

ROOT = Path.cwd() if (Path.cwd() / "src").exists() else Path.cwd().parent
sys.path.insert(0, str(ROOT))
from src.loader import Manifest, read_csv
from src.schema import suggest_mapping, apply_mapping
from src.analysis import prepare, filter_posts, feasibility, dataset_label
from src.metrics import choose_metric, metric_coverage, summarize
from src.hashtags import hashtag_table
from src.reporting import summary_tables, executive_summary, markdown_report
from src.recommendations import recommend

manifest = Manifest(**json.loads((ROOT / "data/demo_manifest.json").read_text()))
raw = read_csv((ROOT / "data/sample_synthetic_posts.csv").read_bytes())
mapping = suggest_mapping(raw.columns)
cleaned, quality = prepare(apply_mapping(raw, mapping), manifest)
posts = filter_posts(cleaned)
metric = choose_metric(posts).name
print(dataset_label(posts), "|", len(posts), "posts | primary metric:", metric)
display(pd.DataFrame([manifest.to_dict()]))'''),
    nbf.v4.new_markdown_cell('''## Validate before interpreting

Identical original duplicates are reported and removed. Conflicting source/account/post IDs stay in cleaned exports and are excluded from analysis. Missing and invalid counts remain missing. Rates require complete likes/comments/shares and a positive, separately defined denominator.'''),
    nbf.v4.new_code_cell('''display(pd.DataFrame({"field": list(quality["missingness"]), "missing": list(quality["missingness"].values())}))
print({k:v for k,v in quality.items() if k != "missingness"})
display(metric_coverage(posts))
display(feasibility(posts, metric, manifest))'''),
    nbf.v4.new_markdown_cell('''## 1–2. Platforms and content formats

Compare means, medians, valid n, coverage, and group date ranges. Raw platform counts and differently defined denominators require qualification. Filter to comparable accounts/date ranges before forming a practical experiment.'''),
    nbf.v4.new_code_cell('''tables = summary_tables(posts, metric, manifest)
for group in ["platform", "content_type"]:
    display(tables[group])
    px.box(posts, x=group, y=metric, points="outliers", title=f"SYNTHETIC DEMO: {group} vs {metric}").show()'''),
    nbf.v4.new_markdown_cell('''## 3. Hashtag usage and supplied topics

Unicode-safe extraction counts each tag once per post. Frequency describes usage in this sample, not audience popularity. No topics are invented.'''),
    nbf.v4.new_code_cell('''display(hashtag_table(posts, metric))
display(tables["topic"])'''),
    nbf.v4.new_markdown_cell('''## 4. Caption sentiment

Supplied labels are disclosed as unverified. Otherwise a tiny offline English lexicon abstains on Urdu script, uncertain vocabulary, and negation. Roman Urdu accuracy is not claimed. These labels describe captions, not audience comments.'''),
    nbf.v4.new_code_cell('''display(posts.sentiment_label.value_counts().rename_axis("caption sentiment").to_frame("posts"))
display(tables["sentiment_label"])
display(posts[["caption_original", "sentiment_label", "sentiment_method"]].head(12))'''),
    nbf.v4.new_markdown_cell('''## 5–6. Timing and audience evidence

Karachi-local timing requires a known source timezone/offset. Date-only observations do not imply an hour. The synthetic fixture has no audience demographics. Pakistani brands alone would still only be a market proxy.'''),
    nbf.v4.new_code_cell('''display(posts.time_status.value_counts().to_frame("posts"))
display(tables["weekday"])
display(tables["hour"])
display(tables["audience_segment"])
print("Insufficient audience-demographic data" if tables["audience_segment"].empty else "See audience evidence and grain limitations")'''),
    nbf.v4.new_markdown_cell('''## 7. What should a brand test next?

The deterministic engine quotes computed medians, means, comparison n, metric, dates, dataset status, and limitations. Groups need n≥5 and ≥80% metric coverage; otherwise it asks for observations. Association is not causation.'''),
    nbf.v4.new_code_cell('''for card in recommend(posts, metric, manifest):
    display(Markdown(f"### {card['kind']}\\n{card['action']}\\n\\nEvidence: {card['evidence']}\\n\\nConfidence: {card['confidence']}. {card['limitations']}"))'''),
    nbf.v4.new_markdown_cell('''## Reproduce the export

The executive summary covers all seven questions, including unsupported ones. The report below stays in memory; use the dashboard for explicit downloads. Demo findings must not be rewritten as empirical Pakistani conclusions.'''),
    nbf.v4.new_code_cell('''report = markdown_report(posts, quality, metric, manifest)
assert "SYNTHETIC DEMO" in report
assert "Which Pakistani audience segment" in report
display(Markdown(executive_summary(posts, metric, manifest)))
print("Markdown report ready:", len(report), "characters")'''),
]
nbf.write(nb, ROOT / 'notebooks/assignment_analysis.ipynb')
