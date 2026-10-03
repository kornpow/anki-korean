#!/usr/bin/env python3
"""Restore curated source media and build galleries; never import personal feedback."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time

import requests
from PIL import Image

from build_review import build
from serve_review import COLLECTIONS


def matches(path, record):
    return path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--media-source', type=Path,
                        help='Optional existing media directory (containing starter-50) to copy from')
    args = parser.parse_args()
    media = Path(__file__).resolve().parents[1]
    cache = {}
    with requests.Session() as session:
        session.headers['User-Agent'] = 'KoreanLearningResearch/0.1 (educational media catalog)'
        for folder in COLLECTIONS.values():
            root = media / 'starter-50' / folder
            records = json.loads((root / 'manifest.json').read_text())
            for record in records:
                relative = Path(record['local_path'])
                if relative.is_absolute() or '..' in relative.parts:
                    raise ValueError('Invalid media path in manifest')
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                if not matches(destination, record):
                    candidates = [cache.get(record['sha256'])]
                    if args.media_source:
                        candidates.append(args.media_source / 'starter-50' / folder / relative)
                    existing = next((x for x in candidates if x and matches(x, record)), None)
                    if existing:
                        shutil.copy2(existing, destination)
                    else:
                        response = session.get(record['download_url'], timeout=60)
                        response.raise_for_status()
                        if hashlib.sha256(response.content).hexdigest() != record['sha256']:
                            raise ValueError(f'Source bytes changed for {record["pageid"]}; review metadata before updating the checksum.')
                        temporary = destination.with_suffix(destination.suffix + '.part')
                        temporary.write_bytes(response.content)
                        temporary.replace(destination)
                        time.sleep(1)
                with Image.open(destination) as image:
                    if image.size != (record['width'], record['height']):
                        raise ValueError(f'Image dimensions differ for {record["pageid"]}')
                cache[record['sha256']] = destination
            build(root)
    print('Media restored and all galleries built. Feedback was not imported.')


if __name__ == '__main__':
    main()
