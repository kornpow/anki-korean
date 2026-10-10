# Korean learning app

A Python-backed media reviewer for planning a broader Korean learning tool. Review real-world Korean in photos with English descriptions and selected translations. Choices and notes save automatically to the server—no feedback export step.

## Run from the repository root

```bash
uv sync --extra review --extra ocr
uv run --extra review --extra ocr python apps/korean_learning/media/scripts/prepare_media.py
uv run --extra review --extra ocr python apps/korean_learning/media/scripts/serve_review.py
```

The server binds to `127.0.0.1:8000`. Access it on the host, through your own port forwarding, or through an existing tunnel. The repository does not provision a public URL.

Gallery paths:

- `/sample-20/gallery.html`: second sample, images #11–20.
- `/sample-10/gallery.html`: first sample, images #1–10.
- `/gallery.html`: original 50-image research collection, including less useful candidates.

`prepare_media.py` downloads the exact Commons images referenced by the committed manifests, verifies checksums and dimensions, and builds all galleries. It stops on changed source bytes rather than silently using a different image. To reuse an existing download directory:

```bash
uv run --extra review --extra ocr python apps/korean_learning/media/scripts/prepare_media.py \
  --media-source /path/to/existing/media
```

Downloaded photographs, generated HTML, browser binaries, and personal feedback are ignored by Git. Source manifests, attribution, English explanations, crop coordinates, and stable image numbers are versioned. The attribution JSON records credits and licenses per photo; no single license is assigned to all media.

## Feedback and existing installations

The server stores feedback as JSON in `apps/korean_learning/media/feedback/`, outside the static media directory. Override it with `--feedback-dir /path/to/feedback` to preserve an existing installation. Use `--port` to change the listening port.

Browser-only feedback at the current origin migrates automatically. Keep the same public origin when moving the app if you want to recover that local cache. Already saved server feedback is independent of the origin.

The UI shows Saving, Saved, or a retry message. Offline edits are cached locally and retried. This is a single-reviewer, shared-link prototype: anyone with access to its server can access or modify that collection's feedback. It does not yet implement user accounts.

## Edit and test

Edit `media/scripts/review_template.html` for the UI. After changing it or a collection manifest:

```bash
uv run --extra review --extra ocr python apps/korean_learning/media/scripts/prepare_media.py
```

Browser interaction checks use Obscura controlled directly from Python:

```bash
uv run --extra review --extra ocr python apps/korean_learning/media/scripts/install_obscura.py
uv run --extra review --extra ocr python apps/korean_learning/media/scripts/check_reviewer.py
```

The installer targets Linux x86_64. Set `OBSCURA_BINARY` to an existing executable on another supported platform. Tests use temporary feedback storage, leaving real reviews untouched. No Node, Playwright, or Selenium is required.

## Scope and integration

Implemented: contextual photo review, English explanations, Keep/Maybe/Reject choices, notes, automatic persistence, source attribution, curated media restoration, video vocabulary imports, themed flashcards, and Obscura checks.

Planned: typed Hangul practice, word-level reading help, spaced repetition, and verb/conjugation practice. These are not implemented learning screens yet. See [the product plan](PLAN.md).

The existing root `src/duolingo_parse.py` and `src/create_deck.py` remain independent working tools. Their vocabulary CSV/JSON is the intended import point for a future shared vocabulary library; the reviewer does not yet import those files automatically.

## Import a Duolingo recording

Open `/import` on the running reviewer, or follow **Import Duolingo video** from
any gallery. Choose a screen recording with Korean and English visible together.
Scroll slowly and pause after each scroll. Upload progress is shown separately
from background word extraction; keep the tab open until uploading finishes.
The import URL can then be revisited while processing continues.

The page accepts MP4, MOV, M4V, AVI, MKV and WebM, up to 90 MiB and five minutes.
Codec support depends on OpenCV. The uploader uses local CPU inference with
RapidOCR 3.10.0, ONNX Runtime 1.31.0 and the Korean PP-OCRv5 mobile recognition
model. It supports the light-background, bordered Duolingo word list, with Korean
above English. Cropped, dark-mode, wrapped or changed layouts may need another
adapter; unsupported rows are skipped. The command-line parser retains Tesseract
as its default for other input formats.

The first neural OCR run downloads about 13 MB of model weights to
`~/.cache/anki-korean/ocr`; subsequent runs use that cache and process recordings
locally without sending media to a remote API. Keep the cache for offline use.
Recognition uses two CPU threads and video decoding is limited to two threads.
Complete vocabulary cells are identified before Korean and English recognition.
Repeated pairs are consolidated (including comma-spacing variants), the strongest
accepted observation supplies the preview, and conflicting definitions for the
same Korean spelling are marked for review. Model scores are not calibrated
probabilities or guarantees of correct spelling. Extraction samples one frame
per second. One import processes at a time, with room for one queued upload.

Review detected pairs beside their source frames, edit Korean or English, and
uncheck unwanted pairs. Low-confidence pairs start unchecked. **Save selected
words** writes the reviewed selection directly to the server vocabulary library;
there is no feedback export step. Draft edits stay in this browser. Re-saving
replaces that import's previous contribution and retains words from other imports.
Each saved pair records its import, original OCR text, frame and timestamp.

Private import files live in `media/imports/` by default, configurable with
`--imports-dir`. This ignored directory contains per-import video, job status,
parser audit files and frames, plus the merged `vocabulary.json` library. Original
videos and the library are outside the static gallery directory. Import URLs allow
access to that import's results and frames: this remains a shared-link prototype,
not an authenticated multi-user service. Back up the imports directory to retain
recordings and vocabulary. Files are retained until manually removed. Interrupted
jobs are marked failed on restart and can be uploaded again.

CPU OCR validation (2026-10-10): on 18 manually transcribed, fully visible rows
across three frames of one recording, the earlier row-based Tesseract prototype
matched 16/18 pairs exactly. Korean PP-OCRv5 matched 17/18 exactly; the remaining
pair differed only by whitespace after a comma (18/18 when that spacing is ignored).
Neural OCR took 5.12 seconds for the sampled crops after model initialization;
the Tesseract comparison took 16.95 seconds including Python startup. These are
exploratory measurements, not a held-out benchmark or guaranteed speedup.
The first complete 15.72-second video run took 158.63 seconds including decoding,
frame storage and OCR. Review remains necessary: another row in the full clip
misspelled “grilling.” The uploader uses a conservative score threshold of 95
and keeps lower-scoring pairs unchecked. It does not silently repair spellings.

To use the same model from the command line:

```bash
uv run --extra ocr python src/duolingo_parse.py recording.mp4 \
  --engine rapidocr --scale 1 --min-confidence 95 --output-dir imports/local-ocr
```

## Themed vocabulary review

An import can include a `themes` array in its `job.json`. Each theme has `id`,
`title`, `description`, `count`, and `candidate_ids`. The review page groups cards
by theme and provides a **Study theme** selector. Filtering does not discard edits
or selections; saving includes selected words across all themes. Imports without
theme metadata retain the ordinary review view.

The current two-minute recording has a manually curated first pass: 189 entries
assigned once each across 13 themes. Group sizes follow the available vocabulary
rather than padding every theme to 20 words. Its private import directory also
contains `themes.json` and `themed-vocabulary.csv` for inspection. Grouping uses
Korean meanings; original OCR English and review flags are preserved. Future
uploads are not automatically classified yet.


## Study flashcards

Open `/study` or follow **Study flashcards** from word review. Choose a recording
and a theme, then reveal each answer and mark **Got it** or **Practice again**.
Cards can run Korean → English or English → Korean, with optional shuffling and
a difficult-words-only filter. Flagged OCR entries are excluded by default.

The viewer uses the saved vocabulary selection and its corrections when present,
otherwise the import candidates. Original English meanings may still need
checking in word review. Imports without theme metadata offer an All words deck.

Ratings save automatically to each private import's `study.json`. Pending
ratings are cached in the browser and retried; unique event IDs prevent duplicate
reviews after network retries. A session can repeat its missed cards. Difficulty
reflects the latest rating; this is practice tracking, not yet a spaced-repetition
scheduler. Progress is shared by everyone using this prototype.

Keyboard shortcuts: Space reveals the answer, 1 marks Practice again, and 2
marks Got it. No feedback export is required.
