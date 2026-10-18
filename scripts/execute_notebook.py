"""Execute the notebook using this environment without installing a global kernel."""
from pathlib import Path
import os
import sys
import tempfile
import json
import nbformat
from nbclient import NotebookClient
import argparse

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--notebook', default='notebooks/assignment_analysis.ipynb')
args = parser.parse_args()
path = ROOT / args.notebook
notebook = nbformat.read(path, as_version=4)
with tempfile.TemporaryDirectory(prefix='detective-jupyter-') as temporary:
    kernel_dir = Path(temporary) / 'kernels' / 'detective-local'
    kernel_dir.mkdir(parents=True)
    (kernel_dir / 'kernel.json').write_text(json.dumps({
        'argv': [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}'],
        'display_name': 'Content Detective local Python', 'language': 'python',
    }))
    previous = os.environ.get('JUPYTER_PATH')
    os.environ['JUPYTER_PATH'] = temporary + (os.pathsep + previous if previous else '')
    try:
        client = NotebookClient(notebook, timeout=60, kernel_name='detective-local',
                                resources={'metadata': {'path': str(ROOT)}},
                                ipython_hist_file=':memory:')
        client.execute()
    finally:
        if previous is None:
            os.environ.pop('JUPYTER_PATH', None)
        else:
            os.environ['JUPYTER_PATH'] = previous
nbformat.write(notebook, path)
print(f'Executed {sum(c.cell_type == "code" for c in notebook.cells)} code cells: {path}')
