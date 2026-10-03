#!/usr/bin/env python3
"""Build an offline gallery, CSV, source notes, and collection summary."""
import csv
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
records = json.loads((root / 'manifest.json').read_text())
themes = {
    'menus_and_food': 'Menus and food',
    'getting_around': 'Getting around',
    'notices_and_rules': 'Notices and rules',
    'shopping_and_services': 'Shopping and services',
    'products_and_labels': 'Products and labels',
    'places_and_culture': 'Places and culture',
}
counts = Counter(r['theme'] for r in records)
fields = ['pageid', 'theme', 'label', 'study_target', 'local_path', 'source_page',
          'author', 'license', 'license_url', 'width', 'height', 'quality_notes',
          'visual_review', 'transcript_status', 'sha256', 'retrieved_at']
with (root / 'catalog.csv').open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(records)
attributions = ['# Media Sources and Attribution', '',
    'Metadata records the license reported by the source at collection time. Images are unchanged Commons downloads or thumbnails. Source dates may be historical; visible prices and notices are reading material, not current travel information.', '']
for r in records:
    label = r.get('label', r['title'])
    attributions += [f"## {r['pageid']} {label}", '',
        f"- Local image: [{r['local_path']}]({r['local_path']})",
        f"- Source: [{r['title']}]({r['source_page']})",
        f"- Author: {r['author']}",
        f"- License: {r['license']}" + (f" — {r['license_url']}" if r['license_url'] else ''),
        f"- Credit supplied by source: {r['credit']}",
        f"- Source date: {r['source_date']}",
        f"- Modification: {r['modification']}", '']
(root / 'ATTRIBUTION.md').write_text('\n'.join(attributions))
attribution_fields = ['pageid', 'title', 'label', 'local_path', 'source_page',
    'author', 'author_evidence', 'credit', 'license', 'license_url',
    'attribution_required', 'modification', 'retrieved_at']
(root / 'attribution.json').write_text(json.dumps({
    'schema_version': 1,
    'collection': 'korean-starter-50',
    'note': 'License and credit as reported by the source. Author evidence is included where manually resolved. Gallery previews are resized; downloaded source images are unchanged.',
    'items': [{key: record[key] for key in attribution_fields if key in record} for record in records]
}, ensure_ascii=False, indent=2))
summary = ['# Korean Media Starter Collection', '',
    f'{len(records)} downloaded still images organized by learning theme.', '',
    '[Open the media reviewer](gallery.html) · [CSV catalog](catalog.csv) · [JSON manifest](manifest.json) · [Attribution JSON](attribution.json) · [Readable attribution](ATTRIBUTION.md)', '',
    '## Theme counts', '', '| Theme | Items |', '| --- | ---: |']
summary += [f'| {themes.get(theme,theme)} | {count} |' for theme,count in counts.items()]
summary += ['', '## Review status', '',
    'The selection has been visually checked for Korean text and theme relevance. The catalog includes learning targets and image limitations. Full transcription, word boundaries, translations, audio, and difficulty grading have not been completed. These are source assets for lesson preparation, not finished lessons.', '',
    'Source photos can contain English translations, historical prices, or outdated notices. Images are retained as downloaded; no translation masking or text edits have been applied. Each record preserves its source page, author, reported license, original image URL, downloaded dimensions, and SHA-256 checksum.', '',
    '## Collection files', '',
    '- Theme folders contain the selected media files.',
    '- `_metadata` contains the original Commons image metadata for each source.',
    '- `selection.json` records the curated IDs and editorial notes used to create this batch.',
    '- `manifest.json` is the machine-readable inventory; `catalog.csv` is the spreadsheet version.',
    '- `ATTRIBUTION.md` preserves source credits and license links.', '',
    '- `attribution.json` contains just the source credit and license fields for easy auditing.', '',
    'The collection covers still images of everyday Korean. It does not include video reels or synchronized speech.', '']
(root / 'README.md').write_text('\n'.join(summary))
print(f'Built gallery and catalogs for {len(records)} items at {root}')

from build_review import build
build(root)
