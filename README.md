# anki-korean

Create Korean flash cards from video content.

## Make Anki cards from Duolingo words

The current deck is `wordlist/duolingo_korean.apkg`: 993 Korean → English
cards. Import it using Anki's File → Import. The accompanying
`wordlist/duolingo_korean.csv` is sorted by Korean spelling.

```bash
uv run python src/create_deck.py 'wordlist/duolingo-korean-words-2026-10-22.csv' \
  --name 'Duolingo Korean' --output wordlist/duolingo_korean.apkg
```

Use `--sort english` to sort by translation or `--sort source` to retain the
export's order. Sorting controls the exported list and initial card order;
Anki's study settings control the order cards are presented.

Add `--reverse` to generate cards in both directions (1,986 cards for 993 words).
This uses a separate note model; choose a direction before importing to avoid
keeping both versions as separate notes.

The builder accepts both `korean,english` and the older
`korean_text,english_text` columns. It removes exact duplicate pairs, preserves
different translations for the same word, and rejects empty fields. Deck and
note IDs are stable: importing the same deck again will not duplicate unchanged
notes. Editing a word or translation creates a new note identity.

Translations are preserved from the source CSV and have not been reviewed for
accuracy. The generated cards contain text only.

## Usage

```bash
# 1. Extract frames from video
uv run python src/video_splitter.py sources/duo-video.mp4

# 2. Crop text boxes from frames
uv run python src/box_cropper.py frames/frame_000001_t0.00s.png
```

## Advanced Usage
```bash
# Run box cropper on all files
find frames/*.png -type f | xargs -I {} uv run src/box_cropper.py {} --crop 0 450 890 1250
```


Install dependencies: `uv sync`

## Import a Duolingo word list

The parser accepts a screen recording, a screenshot, a folder of screenshots, or a
UTF-8 text transcript. It extracts Korean/English pairs and sorts them without
inventing translations or categories.

Install Python dependencies with `uv sync`. For screenshots and recordings,
Tesseract must also be installed with both Korean and English language data.
On Debian/Ubuntu: `sudo apt-get install tesseract-ocr tesseract-ocr-kor`.
Check your installation with `tesseract --list-langs` (must include `kor` and `eng`).
The parser deliberately does not fall back to English-only OCR.

```bash
# Recording: sample once per second, sort by Korean spelling
uv run python src/duolingo_parse.py sources/word-list.mov --output-dir imports/words

# Screenshots already produced by the existing frame/crop scripts
uv run python src/duolingo_parse.py cropped_boxes --output-dir imports/screenshots

# Limit OCR to the word-list area: X Y WIDTH HEIGHT in oriented source pixels
uv run python src/duolingo_parse.py sources/words.png --crop 0 450 890 1250 \
  --output-dir imports/cropped

# Text input needs no OCR engine; stacked pairs explicitly opt in
uv run python src/duolingo_parse.py samples/duolingo_words.txt --layout stacked \
  --sort english --output-dir imports/text

# Feed the resulting CSV directly to the existing Anki generator
uv run python src/create_deck.py --csv imports/words/vocabulary.csv \
  --output korean_vocabulary.apkg
```

Each run uses a new or empty output directory, preventing old frames or results
from being silently mixed into another import. Outputs:

- `vocabulary.csv`: `filename,korean_text,english_text`, compatible with the deck generator.
- `vocabulary.json`: pairs with every source observation, timestamps, OCR confidence,
  settings, uncertain candidates under `needs_review`, and per-image errors.
- `ocr_raw.json`: OCR words and reconstructed lines with positions, or original text lines.
- `frames/`: frames sampled from a video, when the input is a recording.

Sort with `--sort korean`, `english`, or `source`. Korean sorting uses normalized
Unicode spelling, not linguistic/dictionary collation. Duplicate pairs merge while
preserving observations; different meanings for the same Korean spelling remain
separate in both the parser and Anki export. The deck generator still supports its
original default input filename when `--csv` is omitted.

The default layout handles pairs on one line or adjacent, aligned lines within
one OCR block. Use `--layout inline` to disable stacked pairing. Plain text pairs
on separate lines require `--layout stacked`; blank lines separate cards. Use
`--psm` to adjust Tesseract layout segmentation, `--interval` for video sampling,
`--scale` for image resizing, and `--min-confidence` for the acceptance threshold.
Bounding boxes in the OCR audit refer to the resized/cropped OCR image; the saved
settings preserve the transform back to the source.

Low-confidence or unpaired text is kept for review, not silently discarded.
Confidence measures OCR recognition, not the correctness of a translation or pair.
Headers, animations, multi-column screens, and changed app layouts can still need
manual review or a tighter input crop. Themes, part-of-speech tags, and conjugation
grouping are future enrichment steps; this importer preserves the source vocabulary.

Exit codes: `0` means at least one pair and no image failures; `1` means no pairs
or partial image failures (inspect the audit files); `2` means an input/setup error.

```bash
uv run python -m unittest discover -s tests -v
uv run ruff check src/duolingo_parse.py src/create_deck.py tests/test_duolingo_parse.py
```

## Real-world Korean review app

The [Korean learning app](apps/korean_learning/README.md) lives alongside the
Duolingo import and Anki tools. It includes contextual photo review, English
explanations, automatic feedback saving, attributed media catalogs, and the
learning-tool plans.

```bash
uv sync --extra review --extra ocr
uv run --extra review --extra ocr python apps/korean_learning/media/scripts/prepare_media.py
uv run --extra review --extra ocr python apps/korean_learning/media/scripts/serve_review.py
```

See the app README for gallery routes, media restoration, existing feedback
migration, and Obscura browser checks. Downloaded media and personal feedback
are not committed.
## Export your Duolingo words

1. Open https://www.duolingo.com/practice-hub/words in your logged-in browser.
2. Open DevTools (Mac: Option + Command + J) and select Console.
3. Paste the contents of `src/export_duolingo_words.js` and press Enter.
4. Keep the tab open while it expands **Load more**. It downloads a UTF-8 CSV
   with `korean,english` columns once the row count matches the page total.

The script reads the page and uses your existing login. It does not send your
words anywhere. It expects Duolingo's English interface and Korean course.
If Duolingo changes its page layout, it may need updating. Inspect the downloaded
CSV before importing it into Anki. The video/OCR importer above remains available for recordings and screenshots.
