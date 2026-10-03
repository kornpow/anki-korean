#!/usr/bin/env python3
"""Build a portable, offline media reviewer with images embedded in one HTML file."""
import base64
import csv
import html
import io
import json
import mimetypes
from pathlib import Path
import sys
from PIL import Image, ImageOps


def build(root):
    root = Path(root).resolve()
    records = json.loads((root / 'manifest.json').read_text())
    number_path = root / 'review-numbers.csv'
    existing = {}
    if number_path.exists():
        with number_path.open() as source:
            existing = {int(row['commons_pageid']): int(row['review_number']) for row in csv.DictReader(source)}
    next_number = max(existing.values(), default=0) + 1
    items = []
    for record in records:
        number = existing.get(record['pageid'])
        if number is None:
            number = next_number
            next_number += 1
        path = root / record['local_path']
        mime = mimetypes.guess_type(path.name)[0] or 'image/jpeg'
        items.append({key: record.get(key, '') for key in (
            'pageid', 'theme', 'title', 'label', 'study_target', 'quality_notes',
            'author', 'license', 'license_url', 'source_page', 'original_url',
            'width', 'height', 'sha256', 'credit', 'modification', 'author_evidence',
            'attribution_required', 'retrieved_at', 'description_en', 'korean_text', 'translation_en', 'translation_scope', 'crop_regions', 'crop_masks', 'crop_presentation', 'review_default')})
        with Image.open(path) as image:
            thumbnail = ImageOps.contain(ImageOps.exif_transpose(image).convert('RGB'), (400, 300))
            stream = io.BytesIO()
            thumbnail.save(stream, format='JPEG', quality=82)
        items[-1].update(number=number,
            image='data:' + mime + ';base64,' + base64.b64encode(path.read_bytes()).decode(),
            thumbnail='data:image/jpeg;base64,' + base64.b64encode(stream.getvalue()).decode())
    items.sort(key=lambda item: item['number'])
    data = json.dumps(items, ensure_ascii=False).replace('<', '\\u003c')
    template = Path(__file__).with_name('review_template.html').read_text()
    config_path = root / 'collection.json'
    config = json.loads(config_path.read_text()) if config_path.exists() else {}
    template = template.replace('Browse 50 real-world images.', f'Browse {len(records)} real-world images.').replace(' / 50 reviewed', f' / {len(records)} reviewed').replace('max="50"', f'max="{len(records)}"')
    template = template.replace('korean-starter-50', config.get('id', 'korean-starter-50')).replace('korean-media-review-v1', config.get('storage_key', 'korean-media-review-v1'))
    if config.get('title'):
        template = template.replace('What belongs in your lessons?', html.escape(config['title']))
    if config.get('intro'):
        start = template.index('<h1>')
        paragraph = template.index('<p>', start)
        end = template.index('</p>', paragraph)
        template = template[:paragraph] + '<p>' + html.escape(config['intro']) + template[end:]
    assert template.count('__MEDIA_DATA__') == 1
    (root / 'review-portable.html').write_text(template.replace('__MEDIA_DATA__', data))
    thumbnails = root / '_review_thumbnails'
    thumbnails.mkdir(exist_ok=True)
    source_paths = {record['pageid']: record['local_path'] for record in records}
    local_items = []
    for item in items:
        thumbnail_path = thumbnails / f"{item['pageid']}.jpg"
        thumbnail_path.write_bytes(base64.b64decode(item['thumbnail'].split(',', 1)[1]))
        local_items.append(dict(item, image=source_paths[item['pageid']],
            thumbnail=str(thumbnail_path.relative_to(root))))
    local_data = json.dumps(local_items, ensure_ascii=False).replace('<', '\\u003c')
    (root / 'gallery.html').write_text(template.replace('__MEDIA_DATA__', local_data))
    (root / 'review-numbers.csv').write_text('review_number,commons_pageid\n' +
        ''.join(f"{item['number']:02d},{item['pageid']}\n" for item in items))
    print(f'Built local gallery and portable reviewer for {len(items)} images at {root}')


if __name__ == '__main__':
    build(sys.argv[1])
