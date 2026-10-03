# Korean learning app

A Python-backed media reviewer for planning a broader Korean learning tool. Review real-world Korean in photos with English descriptions and selected translations. Choices and notes save automatically to the server—no feedback export step.

## Run from the repository root

```bash
uv sync --extra review
uv run --extra review python apps/korean_learning/media/scripts/prepare_media.py
uv run --extra review python apps/korean_learning/media/scripts/serve_review.py
```

The server binds to `127.0.0.1:8000`. Access it on the host, through your own port forwarding, or through an existing tunnel. The repository does not provision a public URL.

Gallery paths:

- `/sample-20/gallery.html`: second sample, images #11–20.
- `/sample-10/gallery.html`: first sample, images #1–10.
- `/gallery.html`: original 50-image research collection, including less useful candidates.

`prepare_media.py` downloads the exact Commons images referenced by the committed manifests, verifies checksums and dimensions, and builds all galleries. It stops on changed source bytes rather than silently using a different image. To reuse an existing download directory:

```bash
uv run --extra review python apps/korean_learning/media/scripts/prepare_media.py \
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
uv run --extra review python apps/korean_learning/media/scripts/prepare_media.py
```

Browser interaction checks use Obscura controlled directly from Python:

```bash
uv run --extra review python apps/korean_learning/media/scripts/install_obscura.py
uv run --extra review python apps/korean_learning/media/scripts/check_reviewer.py
```

The installer targets Linux x86_64. Set `OBSCURA_BINARY` to an existing executable on another supported platform. Tests use temporary feedback storage, leaving real reviews untouched. No Node, Playwright, or Selenium is required.

## Scope and integration

Implemented: contextual photo review, English explanations, Keep/Maybe/Reject choices, notes, automatic persistence, source attribution, curated media restoration, and Obscura checks.

Planned: themed vocabulary, typed Hangul practice, word-level reading help, spaced repetition, and verb/conjugation practice. These are not implemented learning screens yet. See [the product plan](PLAN.md).

The existing root `src/duolingo_parse.py` and `src/create_deck.py` remain independent working tools. Their vocabulary CSV/JSON is the intended import point for a future shared vocabulary library; the reviewer does not yet import those files automatically.
