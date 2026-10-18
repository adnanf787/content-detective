"""Create the reproducible real-pilot notebook; results appear only after execution."""
from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
notebook = nbf.v4.new_notebook()
notebook.cells = [
    nbf.v4.new_markdown_cell('''# Pakistani Social Media Content Detective: real YouTube pilot

Official Jazz, Zong, and Ufone channel snapshots. The collector uses uploads playlists,
public video metadata, and capped newest top-level comments. Read the actual collection
report for counts/errors; no Instagram data or viewer demographics are implied.

The common window was extended to October 2025–September 2026 with user approval after
the April–September window contained only seven eligible Zong videos. Post ages still
differ across brands. NLP outputs are exploratory, unevaluated cue labels, not gold truth.
'''),
    nbf.v4.new_code_cell('''from pathlib import Path
import sys, json
import pandas as pd
import plotly.express as px
ROOT = Path.cwd() if (Path.cwd() / 'src').exists() else Path.cwd().parent
sys.path.insert(0, str(ROOT))
from src.analysis import prepare, feasibility
from src.loader import Manifest, read_csv
from src.metrics import choose_metric, source_coverage, summarize
from src.content_nlp import annotate_comments
from src.reporting import markdown_report
from src.dataset_validation import validate_exports
folder = ROOT / 'data/processed'
receipt = json.loads((folder / 'youtube_collection_report.json').read_text())
raw = read_csv((folder / 'youtube_posts.csv').read_bytes())
comments = annotate_comments(pd.read_csv(folder / 'youtube_comments.csv', dtype=str, keep_default_na=False))
manifest = Manifest(file_name='youtube_posts.csv', source_name='Verified telecom YouTube pilot', source_type='official_api',
                    status='real', source_timezone='UTC', geographic_relevance='Pakistan-relevant brands, not verified Pakistani viewers',
                    notes=receipt['sampling_method'] + '\\n' + receipt['limitations'])
posts, quality = prepare(raw, manifest)
audit = validate_exports(raw, comments)
assert audit['valid'], audit['errors']
metric = choose_metric(posts).name
print('Real posts:', len(posts), '| sampled public comments:', len(comments), '| primary metric:', metric)
display(pd.DataFrame(receipt['brands']))
'''),
    nbf.v4.new_code_cell('''display(source_coverage(posts))
display(feasibility(posts, metric, manifest))
print('API errors:', len(receipt['api_errors']))
print('Latest invocation network calls:', receipt['request_attempts'], '| cached responses:', receipt['cached_responses_used'])
print('Post-age ranges by brand:')
display(posts.groupby('brand').age_days_at_snapshot.agg(['min', 'median', 'max']))
'''),
    nbf.v4.new_code_cell('''display(summarize(posts, 'brand', metric))
px.box(posts, x='brand', y=metric, points='all', hover_data=['post_id', 'age_days_at_snapshot']).show()
'''),
    nbf.v4.new_code_cell('''display(summarize(posts, 'category_suggested', metric))
display(summarize(posts, 'language_inferred', metric))
print('These are suggested content labels; human review and evaluation are pending.')
display(posts[['brand', 'source_url', 'post_datetime', 'category_suggested', 'category_evidence', 'language_inferred']])
'''),
    nbf.v4.new_code_cell('''sentiment_counts = comments.groupby(['brand', 'sentiment_label']).size().reset_index(name='sampled_comments')
display(sentiment_counts)
px.bar(sentiment_counts, x='brand', y='sampled_comments', color='sentiment_label', barmode='group').show()
print('Cue-assessed:', comments.sentiment_label.ne('unassessed').sum(), '/', len(comments))
print('No human labels supplied: no accuracy, macro-F1, or calibrated confidence is claimed.')
'''),
    nbf.v4.new_code_cell('''report = markdown_report(posts, quality, metric, manifest, comments=comments)
(folder / 'youtube_findings.md').write_text(report, encoding='utf-8')
print('Saved evidence report:', folder / 'youtube_findings.md')
'''),
]
notebook.metadata['kernelspec'] = {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}
path = ROOT / 'notebooks/youtube_pilot_analysis.ipynb'
nbf.write(notebook, path)
print('Created', path)
