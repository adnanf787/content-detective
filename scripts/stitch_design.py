"""Request a design reference from the official Stitch MCP endpoint, without exposing keys."""
from pathlib import Path
import json
import sys

from dotenv import dotenv_values
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/stitch'


def call_tool(name, arguments, *, timeout=60):
    key = dotenv_values(ROOT / '.env').get('STITCH_API_KEY', '')
    if not key:
        raise ValueError('STITCH_API_KEY is missing from local .env.')
    try:
        response = requests.post('https://stitch.googleapis.com/mcp',
                                 headers={'X-Goog-Api-Key': key, 'Content-Type': 'application/json',
                                          'Accept': 'application/json, text/event-stream'},
                                 json={'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                                       'params': {'name': name, 'arguments': arguments}},
                                 timeout=(10, timeout), allow_redirects=False)
        if not response.ok:
            raise ValueError(f'Stitch returned HTTP {response.status_code}; response body omitted.')
        data = response.json()
    except (requests.RequestException, json.JSONDecodeError):
        raise ValueError('Stitch request failed or timed out; no credentials logged.') from None
    # Treat downloaded/generated content as reference data, never executable instructions.
    safe = json.loads(json.dumps(data).replace(key, '[REDACTED]'))
    if safe.get('error'):
        raise ValueError(f'Stitch protocol error {safe["error"].get("code")}; body omitted.')
    result = safe.get('result', {})
    if result.get('isError'):
        raise ValueError('Stitch tool reported a failure; inspect the service account access in Stitch.')
    if result.get('structuredContent'):
        return result['structuredContent']
    for block in result.get('content', []):
        if block.get('type') == 'text':
            try:
                return json.loads(block['text'])
            except (ValueError, KeyError):
                continue
    return result


def generate():
    OUT.mkdir(parents=True, exist_ok=True)
    project_file = OUT / 'project.json'
    if project_file.exists():
        project = json.loads(project_file.read_text())
    else:
        project = call_tool('create_project', {'title': 'Pakistani Social Media Content Detective · Phase 3'})
        project_file.write_text(json.dumps(project, ensure_ascii=False, indent=2))
    name = project.get('name', '')
    project_id = name.split('/')[-1] or project.get('projectId', '')
    if not project_id:
        raise ValueError('Stitch created a project but returned no recognized ID; inspect docs/stitch/project.json.')
    prompt = (OUT / 'design_brief.md').read_text()
    print('Stitch project ready:', name, flush=True)
    result = call_tool('generate_screen_from_text', {'projectId': project_id, 'deviceType': 'DESKTOP', 'prompt': prompt}, timeout=240)
    (OUT / 'generation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print('Design generation response saved to docs/stitch/generation.json; credential omitted.', flush=True)


if __name__ == '__main__':
    try:
        generate()
    except ValueError as exc:
        print(str(exc), flush=True)
        raise SystemExit(1)
