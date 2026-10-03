#!/usr/bin/env python3
"""Discover file IDs from named Commons categories for a future curated batch.

Example:
  python discover_commons.py research.json 'Food menus in Korean' \
    'Korean-language signs in South Korea'

This lists direct category members, preserves pagination, and never treats
category membership as proof of Korean text or learning quality.
"""
import argparse
import json
from pathlib import Path
import time
from collect_commons import API, get

parser = argparse.ArgumentParser()
parser.add_argument('output', type=Path)
parser.add_argument('categories', nargs='+')
args = parser.parse_args()
result = []
for category in args.categories:
    continuation = {}
    members = []
    while True:
        data = get(API, params=dict(action='query', format='json', list='categorymembers',
            cmtitle='Category:' + category, cmlimit=100, **continuation)).json()
        members.extend(data.get('query', {}).get('categorymembers', []))
        continuation = data.get('continue', {})
        time.sleep(3)
        if not continuation:
            break
    result.append({'category': category, 'members': members})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(category, len(members), flush=True)
