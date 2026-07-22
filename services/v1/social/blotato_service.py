import os
import requests
import logging

logger = logging.getLogger(__name__)

BLOTATO_API_BASE = os.environ.get('BLOTATO_API_URL', 'https://api.blotato.com')

PLATFORM_CHAR_LIMITS = {
    'twitter': 280,
    'bluesky': 300,
    'threads': 500,
    'instagram': 2200,
    'facebook': 63206,
    'linkedin': 3000,
    'tiktok': 2200,
    'pinterest': 500,
    'youtube': 5000,
}


def _headers():
    api_key = os.environ.get('BLOTATO_API_KEY', '')
    return {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }


def list_accounts(platform=None):
    params = {}
    if platform:
        params['platform'] = platform
    r = requests.get(f'{BLOTATO_API_BASE}/accounts', headers=_headers(), params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def create_post(payload):
    r = requests.post(f'{BLOTATO_API_BASE}/posts', headers=_headers(), json=payload, timeout=60)
    r.raise_for_status()
    return r.json()


def get_post_status(post_id):
    r = requests.get(f'{BLOTATO_API_BASE}/posts/{post_id}', headers=_headers(), timeout=30)
    r.raise_for_status()
    return r.json()


def list_posts(since=None, until=None, status=None, platform=None, limit=50, cursor=None):
    params = {'limit': limit}
    if since:
        params['since'] = since
    if until:
        params['until'] = until
    if status:
        params['status'] = status if isinstance(status, str) else ','.join(status)
    if platform:
        params['platform'] = platform if isinstance(platform, str) else ','.join(platform)
    if cursor:
        params['cursor'] = cursor
    r = requests.get(f'{BLOTATO_API_BASE}/posts', headers=_headers(), params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def get_post_analytics(post_id):
    r = requests.get(f'{BLOTATO_API_BASE}/posts/{post_id}/analytics', headers=_headers(), timeout=30)
    r.raise_for_status()
    return r.json()


def list_schedules(limit=20, cursor=None):
    params = {'limit': limit}
    if cursor:
        params['cursor'] = cursor
    r = requests.get(f'{BLOTATO_API_BASE}/schedules', headers=_headers(), params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def delete_schedule(schedule_id):
    r = requests.delete(f'{BLOTATO_API_BASE}/schedules/{schedule_id}', headers=_headers(), timeout=30)
    r.raise_for_status()
    return r.json() if r.text else {}


def update_schedule(schedule_id, payload):
    r = requests.patch(
        f'{BLOTATO_API_BASE}/schedules/{schedule_id}',
        headers=_headers(),
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def list_top_posts(limit=10):
    r = requests.get(
        f'{BLOTATO_API_BASE}/posts/top',
        headers=_headers(),
        params={'limit': limit},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()
