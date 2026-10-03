#!/usr/bin/env python3
"""Download a curated Commons selection; retain source metadata and attribution.

Usage: python3 collect_commons.py selection.json output_directory --width 1600
Selection: [{"pageid": 123, "theme": "menus", ...optional editorial fields...}]
Requires requests and Pillow. Existing valid files are reused on reruns.
"""
import argparse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import html
import io
import json
from pathlib import Path
import re
import time

import requests
from PIL import Image

API = 'https://commons.wikimedia.org/w/api.php'
SESSION = requests.Session()
SESSION.headers['User-Agent'] = 'KoreanLearningResearch/0.1 (personal educational media catalog)'
STATUS_PATH = None
MAX_RETRY_WAIT = 60


def get(url, **kwargs):
    for attempt in range(5):
        response = SESSION.get(url, timeout=60, **kwargs)
        if response.status_code == 429 or response.status_code >= 500:
            raw = response.headers.get('Retry-After')
            try:
                delay = float(raw) if raw else 5 * (attempt + 1)
            except ValueError:
                delay = max(0, (parsedate_to_datetime(raw) - datetime.now(timezone.utc)).total_seconds())
            print(f'HTTP {response.status_code}; retry after {delay:.0f}s', flush=True)
            if delay > MAX_RETRY_WAIT:
                raise RuntimeError(f'Resource deferred until {datetime.fromtimestamp(time.time() + delay, timezone.utc).isoformat()}; server Retry-After={delay:.0f}s; no retry attempted')
            if STATUS_PATH:
                STATUS_PATH.write_text(json.dumps({'state': 'backing_off', 'url': url,
                    'resume_after_epoch': time.time() + delay}, indent=2))
            deadline = time.monotonic() + delay
            while time.monotonic() < deadline:
                time.sleep(min(30, max(0, deadline - time.monotonic())))
            continue
        response.raise_for_status()
        return response
    raise RuntimeError(f'Could not fetch {url} after retries')


def plain(value):
    return html.unescape(re.sub('<[^>]*>', '', value or '')).strip()


def main():
    global STATUS_PATH
    parser = argparse.ArgumentParser()
    parser.add_argument('selection', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--width', type=int, default=1600)
    parser.add_argument('--delay', type=float, default=3.0)
    parser.add_argument('--not-before', type=float, default=0)
    args = parser.parse_args()
    selected = json.loads(args.selection.read_text())
    assert len({x['pageid'] for x in selected}) == len(selected), 'Duplicate source page'
    args.output.mkdir(parents=True, exist_ok=True)
    STATUS_PATH = args.output / 'job_status.json'
    while time.time() < args.not_before:
        STATUS_PATH.write_text(json.dumps({'state': 'backing_off', 'resume_after_epoch': args.not_before}, indent=2))
        time.sleep(min(30, max(0, args.not_before - time.time())))
    cache = args.output / '_metadata'
    cache.mkdir(exist_ok=True)
    pages = {}
    missing = []
    for item in selected:
        path = cache / f"{item['pageid']}.json"
        if path.exists():
            pages[item['pageid']] = json.loads(path.read_text())
        else:
            missing.append(item['pageid'])
    for start in range(0, len(missing), 20):
        response = get(API, params={
            'action': 'query', 'format': 'json',
            'pageids': '|'.join(map(str, missing[start:start + 20])),
            'prop': 'imageinfo', 'iiprop': 'url|extmetadata|size|sha1|mime',
            'iiurlwidth': args.width,
        }).json()
        for page in response.get('query', {}).get('pages', {}).values():
            pages[page['pageid']] = page
            (cache / f"{page['pageid']}.json").write_text(json.dumps(page, ensure_ascii=False, indent=2))
        time.sleep(2)
    records, failures = [], []
    for n, item in enumerate(selected, 1):
        try:
            page = pages[item['pageid']]
            info = page['imageinfo'][0]
            meta = info.get('extmetadata', {})
            field = lambda key: plain(meta.get(key, {}).get('value', ''))
            if not field('LicenseShortName'):
                raise ValueError('Missing license metadata')
            if info.get('mime') not in ('image/jpeg', 'image/png', 'image/webp'):
                raise ValueError('Not a supported still-image format')
            url = info.get('thumburl', info['url']).split('?')[0]
            extension = '.png' if '.png' in url.lower().rsplit('/', 1)[-1] else '.jpg'
            relative = Path(item['theme']) / f"commons-{item['pageid']}{extension}"
            destination = args.output / relative
            destination.parent.mkdir(exist_ok=True)
            if not destination.exists():
                data = get(url).content
                with Image.open(io.BytesIO(data)) as image:
                    image.verify()
                destination.write_bytes(data)
                time.sleep(args.delay)
            with Image.open(destination) as image:
                image.load()
                width, height = image.size
            record = dict(item, title=page['title'].removeprefix('File:'),
                          local_path=str(relative), source_page=info['descriptionurl'],
                          original_url=info['url'].split('?')[0], download_url=url,
                          author=item.get('author_override') or field('Artist'), credit=field('Credit'),
                          license=field('LicenseShortName'), license_url=field('LicenseUrl'),
                          attribution_required=field('AttributionRequired'),
                          source_description=field('ImageDescription'),
                          source_date=field('DateTimeOriginal'),
                          width=width, height=height,
                          sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
                          source_sha1=info.get('sha1'),
                          retrieved_at=datetime.now(timezone.utc).isoformat(),
                          modification='Unedited downloaded Commons image or Commons thumbnail',
                          transcript_status='not_transcribed')
            records.append(record)
            print(f"{n}/{len(selected)} {item['theme']} {item['pageid']} {width}x{height}", flush=True)
        except Exception as exc:
            failures.append(dict(item, error=str(exc)))
            print(f"FAILED {item['pageid']}: {exc}", flush=True)
        (args.output / 'manifest.json').write_text(json.dumps(records, ensure_ascii=False, indent=2))
        (args.output / 'failures.json').write_text(json.dumps(failures, ensure_ascii=False, indent=2))
        STATUS_PATH.write_text(json.dumps({'state': 'running', 'processed': n,
            'target': len(selected), 'downloaded': len(records), 'failed': len(failures)}, indent=2))
    print(f'Finished: {len(records)} downloaded, {len(failures)} failed', flush=True)
    STATUS_PATH.write_text(json.dumps({'state': 'finished' if not failures else 'finished_with_errors',
        'target': len(selected), 'downloaded': len(records), 'failed': len(failures)}, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
