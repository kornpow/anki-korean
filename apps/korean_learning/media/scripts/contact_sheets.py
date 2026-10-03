#!/usr/bin/env python3
"""Create contact sheets from a collector output for human visual review."""
import json
from pathlib import Path
import sys
from PIL import Image, ImageDraw, ImageOps

root = Path(sys.argv[1])
records = json.loads((root / 'manifest.json').read_text())
out = root / '_contact_sheets'
out.mkdir(exist_ok=True)
for theme in sorted({r['theme'] for r in records}):
    items = [r for r in records if r['theme'] == theme]
    for start in range(0, len(items), 12):
        batch = items[start:start + 12]
        sheet = Image.new('RGB', (1500, ((len(batch) + 2) // 3) * 390), 'white')
        draw = ImageDraw.Draw(sheet)
        for i, item in enumerate(batch):
            x, y = (i % 3) * 500, (i // 3) * 390
            with Image.open(root / item['local_path']) as original:
                thumb = ImageOps.contain(ImageOps.exif_transpose(original).convert('RGB'), (490, 350))
                sheet.paste(thumb, (x + (500 - thumb.width) // 2, y))
            draw.text((x + 8, y + 357), str(item['pageid']), fill='black')
        path = out / f'{theme}-{start // 12 + 1}.jpg'
        sheet.save(path, quality=90)
        print(path)
