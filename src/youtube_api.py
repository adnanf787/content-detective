"""Official API transport with bounded retries, privacy-filtered comments, and resume cache."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time

import requests

ENDPOINTS = {'channels', 'playlistItems', 'videos', 'commentThreads'}
COMMENT_FIELDS = ('nextPageToken,pageInfo,items(id,snippet(videoId,topLevelComment(id,'
                  'snippet(textOriginal,textDisplay,publishedAt,updatedAt,likeCount))))')


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


class APIError(ValueError):
    def __init__(self, status, reason):
        self.status, self.reason = status, reason
        super().__init__(f'YouTube API HTTP {status}: {reason}')

    @property
    def credential_or_quota_failure(self):
        return self.reason in {'keyInvalid', 'API_KEY_INVALID', 'accessNotConfigured', 'quotaExceeded',
                               'dailyLimitExceeded', 'ipRefererBlocked', 'API_KEY_SERVICE_BLOCKED'}


class YouTubeAPI:
    def __init__(self, key, raw_dir, *, session=None, sleep=time.sleep):
        if not key.strip():
            raise ValueError('YOUTUBE_API_KEY is missing. Add it to the local ignored .env file.')
        self.key = key.strip()
        self.raw_dir = Path(raw_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.session = session or requests.Session()
        self.sleep = sleep
        self.requests = []
        self.errors = []
        self.halted = False
        self.last_path = ''
        self.last_time = ''

    def _safe(self, value):
        if isinstance(value, str):
            return value.replace(self.key, '[REDACTED]')
        if isinstance(value, list):
            return [self._safe(v) for v in value]
        if isinstance(value, dict):
            return {k: self._safe(v) for k, v in value.items() if k not in {'authorDisplayName', 'authorProfileImageUrl', 'authorChannelUrl', 'authorChannelId'}}
        return value

    def get(self, endpoint, params):
        if endpoint not in ENDPOINTS or any(k in params for k in ('key', 'access_token')):
            raise ValueError('Unsupported YouTube request.')
        params = dict(params)
        if endpoint == 'commentThreads':
            params['fields'] = COMMENT_FIELDS
        fingerprint = hashlib.sha256(json.dumps([endpoint, params], sort_keys=True).encode()).hexdigest()[:24]
        path = self.raw_dir / f'{endpoint}_{fingerprint}.json'
        if path.exists():
            saved = json.loads(path.read_text(encoding='utf-8'))
            self.last_path, self.last_time = str(path), saved['retrieved_at']
            self.requests.append({'endpoint': endpoint, 'cache_hit': True, 'raw_record_path': str(path)})
            return saved['response']
        if self.halted:
            raise APIError(0, 'collectionStoppedAfterCredentialOrQuotaError')
        for attempt in range(3):
            self.sleep(0.1 if attempt == 0 else 0.5 * 2 ** (attempt - 1))
            status, reason = 0, 'networkError'
            try:
                response = self.session.get('https://www.googleapis.com/youtube/v3/' + endpoint,
                                            params={**params, 'key': self.key}, timeout=(10, 30),
                                            allow_redirects=False, stream=True)
                status = response.status_code
                # Bound memory before decoding a remote response.
                chunks, size = [], 0
                for chunk in response.iter_content(65536):
                    size += len(chunk)
                    if size > 8 * 1024 * 1024:
                        raise ValueError('responseTooLarge')
                    chunks.append(chunk)
                response.close()
                payload = json.loads(b''.join(chunks))
                if status == 200 and isinstance(payload, dict) and isinstance(payload.get('items'), list):
                    retrieved = utcnow()
                    envelope = {'endpoint': endpoint, 'parameters': params, 'retrieved_at': retrieved,
                                'response': self._safe(payload)}
                    atomic_json(path, envelope)
                    self.last_path, self.last_time = str(path), retrieved
                    self.requests.append({'endpoint': endpoint, 'status': status, 'attempt': attempt + 1,
                                          'cache_hit': False, 'raw_record_path': str(path)})
                    return envelope['response']
                error = payload.get('error', {}) if isinstance(payload, dict) else {}
                errors = error.get('errors', [])
                reason = errors[0].get('reason', 'unexpectedResponse') if errors else error.get('status', 'unexpectedResponse')
                reason = self._safe(str(reason))
                if not re.fullmatch(r'[A-Za-z0-9_]{1,80}', reason):
                    reason = 'redactedAPIError'
            except requests.RequestException:
                reason = 'networkError'
            except (ValueError, TypeError, AttributeError):
                reason = 'unreadableOrOversizedResponse'
            record = {'endpoint': endpoint, 'status': status, 'reason': reason, 'attempt': attempt + 1,
                      'resource': params.get('videoId') or params.get('id') or params.get('playlistId') or params.get('forUsername') or ''}
            self.requests.append({**record, 'cache_hit': False})
            error = APIError(status, reason)
            transient = status in {0, 429, 500, 502, 503, 504} or reason in {'rateLimitExceeded', 'userRateLimitExceeded', 'backendError'}
            if transient and attempt < 2:
                continue
            self.errors.append(record)
            if error.credential_or_quota_failure:
                self.halted = True
            raise error from None
