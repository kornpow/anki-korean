"""Background video imports and a persistent, reviewable vocabulary library."""

import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

MAX_UPLOAD = 90 * 1024 * 1024
EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}
JOB_ROUTE = re.compile(r"^/api/imports/([a-f0-9]{32})(?:/(vocabulary|study|frames/[^/]+))?$")


def write_json(path, payload):
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".writing-")
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def now():
    return datetime.now(timezone.utc).isoformat()


class VideoImports:
    def __init__(self, directory, parser_path=None):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.parser = parser_path or Path(__file__).resolve().parents[4] / "src/duolingo_parse.py"
        self.lock = threading.RLock()
        self.slot = threading.BoundedSemaphore(2)
        self.pool = ThreadPoolExecutor(max_workers=1)
        for path in self.directory.glob("*/job.json"):
            job = json.loads(path.read_text())
            if job["status"] in ("queued", "processing"):
                job.update(
                    status="failed",
                    error="The server restarted during processing. Upload the video again.",
                )
                write_json(path, job)

    def job_path(self, id):
        return self.directory / id / "job.json"

    def read(self, id):
        path = self.job_path(id)
        if not path.exists():
            raise ValueError("Import not found.")
        with self.lock:
            return json.loads(path.read_text())

    def update(self, id, **changes):
        with self.lock:
            job = self.read(id)
            job.update(changes)
            write_json(self.job_path(id), job)
            return job

    def process(self, id, video):
        try:
            self.update(id, status="processing")
            import cv2

            capture = cv2.VideoCapture(str(video))
            try:
                fps = capture.get(cv2.CAP_PROP_FPS)
                frames = capture.get(cv2.CAP_PROP_FRAME_COUNT)
                width = capture.get(cv2.CAP_PROP_FRAME_WIDTH)
                height = capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
                if not capture.isOpened() or not all(
                    math.isfinite(x) and x > 0 for x in (fps, frames, width, height)
                ):
                    raise ValueError(
                        "This file could not be read as a video. Try an MP4 screen recording."
                    )
                duration = frames / fps
                if duration > 300:
                    raise ValueError(
                        "Please split the recording into clips of five minutes or less."
                    )
                if width * height > 9_000_000 or fps > 120:
                    raise ValueError("Please export this recording at 1080p and 30 or 60 fps.")
            finally:
                capture.release()
            self.update(id, expected_frames=math.ceil(duration), duration_seconds=duration)
            output = video.parent / "result"
            with (video.parent / "parser.log").open("w") as log:
                result = subprocess.run(
                    [
                        sys.executable,
                        str(self.parser),
                        str(video),
                        "--output-dir",
                        str(output),
                        "--engine",
                        "rapidocr",
                        "--min-confidence",
                        "95",
                        "--scale",
                        "1",
                        "--interval",
                        "1",
                    ],
                    stdout=log,
                    stderr=log,
                    timeout=1800,
                )
            report_path = output / "vocabulary.json"
            if result.returncode not in (0, 1) or not report_path.exists():
                raise ValueError(
                    "The parser could not process this video. "
                    "Check the format or ask me to inspect the import."
                )
            report = json.loads(report_path.read_text())
            candidates = self.review_candidates(report)
            write_json(video.parent / "candidates.json", candidates)
            self.update(
                id,
                status="ready",
                summary=report["summary"],
                candidates=candidates,
                message="Review the detected words before saving."
                if candidates
                else "No complete word rows detected. This importer supports Duolingo’s "
                "light-background, bordered word list with Korean above English.",
            )
        except subprocess.TimeoutExpired:
            self.update(id, status="failed", error="Processing took too long. Try a shorter clip.")
        except Exception as error:
            self.update(id, status="failed", error=str(error))
        finally:
            self.slot.release()

    @classmethod
    def review_candidates(cls, report):
        groups = {}
        for entry in report["entries"]:
            for observation in entry["observations"]:
                key = (
                    entry["korean_text"],
                    re.sub(r"\s*,\s*", ",", entry["english_text"]).casefold(),
                )
                groups.setdefault(key, []).append((entry, observation, False))
        for row in report["needs_review"]:
            if row.get("korean_text") and row.get("english_text"):
                key = (row["korean_text"], re.sub(r"\s*,\s*", ",", row["english_text"]).casefold())
                groups.setdefault(key, []).append((row, row, True))
        meanings = {}
        for korean, english in groups:
            meanings.setdefault(korean, set()).add(english)
        candidates = []
        for (korean, _), observations in sorted(groups.items()):
            # Prefer accepted observations, then the strongest original frame.
            entry, observation, uncertain = max(
                observations, key=lambda item: (not item[2], item[1].get("confidence") or 0)
            )
            candidate = cls.candidate(
                len(candidates), entry, observation, uncertain or len(meanings[korean]) > 1
            )
            candidate["observation_count"] = len({item[1]["filename"] for item in observations})
            candidates.append(candidate)
        return candidates

    @staticmethod
    def candidate(index, entry, observation, uncertain):
        lines = observation.get("lines", [])
        bounds = None
        if lines and all(line.get("width", 0) > 0 for line in lines):
            left = max(0, min(line["left"] for line in lines) - 20)
            top = max(0, min(line["top"] for line in lines) - 20)
            right = max(line["left"] + line["width"] for line in lines) + 20
            bottom = max(line["top"] + line["height"] for line in lines) + 20
            bounds = {"x": left, "y": top, "width": right - left, "height": bottom - top}
        return {
            "id": index,
            "bounds": bounds,
            "korean_text": entry["korean_text"],
            "english_text": entry["english_text"],
            "needs_review": uncertain,
            "confidence": observation.get("confidence"),
            "timestamp_seconds": observation.get("timestamp_seconds"),
            "frame": Path(observation["filename"]).name,
        }

    def save_words(self, id, rows):
        job = self.read(id)
        if job["status"] != "ready":
            raise ValueError("This import is not ready.")
        if not isinstance(rows, list) or not rows or len(rows) > 5000:
            raise ValueError("Select at least one word to save.")
        candidates = {x["id"]: x for x in job["candidates"]}
        cleaned, seen = [], set()
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("Invalid word selection.")
            index = row.get("id")
            if not isinstance(index, int) or index not in candidates or index in seen:
                raise ValueError("Invalid or duplicate word selection.")
            seen.add(index)
            korean, english = row.get("korean_text"), row.get("english_text")
            if not all(isinstance(x, str) and 0 < len(x.strip()) <= 500 for x in (korean, english)):
                raise ValueError(
                    "Each selected word needs Korean and English text (maximum 500 characters)."
                )
            cleaned.append(
                dict(candidates[index], korean_text=korean.strip(), english_text=english.strip())
            )
        with self.lock:
            path = self.directory / "vocabulary.json"
            library = (
                json.loads(path.read_text())
                if path.exists()
                else {"schema_version": 1, "entries": []}
            )
            # Replace this import's reviewed contribution, preserving sources from other imports.
            kept = []
            for entry in library["entries"]:
                entry["sources"] = [
                    source for source in entry["sources"] if source["import_id"] != id
                ]
                if entry["sources"]:
                    kept.append(entry)
            merged = {(x["korean_text"], x["english_text"].casefold()): x for x in kept}
            for row in cleaned:
                key = (row["korean_text"], row["english_text"].casefold())
                entry = merged.setdefault(
                    key,
                    {
                        "korean_text": row["korean_text"],
                        "english_text": row["english_text"],
                        "sources": [],
                    },
                )
                entry["sources"].append(
                    {
                        "import_id": id,
                        "candidate_id": row["id"],
                        "frame": row["frame"],
                        "timestamp_seconds": row["timestamp_seconds"],
                        "original_korean": candidates[row["id"]]["korean_text"],
                        "original_english": candidates[row["id"]]["english_text"],
                    }
                )
            library["entries"] = sorted(
                merged.values(), key=lambda x: (x["korean_text"], x["english_text"])
            )
            library["updated_at"] = now()
            write_json(path, library)
            self.update(id, saved_selection=cleaned, saved_at=now())
        return {
            "saved_count": len(cleaned),
            "library_count": len(library["entries"]),
            "saved_at": library["updated_at"],
        }

    def study_state(self, id):
        self.read(id)
        with self.lock:
            path = self.directory / id / "study.json"
            return (
                json.loads(path.read_text())
                if path.exists()
                else {"schema_version": 1, "words": {}, "events": []}
            )

    def rate_word(self, id, body):
        if not isinstance(body, dict):
            raise ValueError("Expected a review object.")
        card = body.get("card_id")
        rating = body.get("rating")
        event = body.get("event_id")
        job = self.read(id)
        if (
            job["status"] != "ready"
            or type(card) is not int
            or card not in {row["id"] for row in job.get("candidates", [])}
        ):
            raise ValueError("Unknown study card.")
        if (
            rating not in ("again", "gotit")
            or not isinstance(event, str)
            or not re.fullmatch(r"[a-f0-9]{32}", event)
        ):
            raise ValueError("Invalid study rating.")
        with self.lock:
            state = self.study_state(id)
            if event in state["events"]:
                return state
            word = state["words"].setdefault(str(card), {"reviews": 0, "again_count": 0})
            word.update(difficult=rating == "again", last_rating=rating, reviewed_at=now())
            word["reviews"] += 1
            word["again_count"] += rating == "again"
            # Retain event IDs so network retries never count a review twice.
            state["events"].append(event)
            state["updated_at"] = now()
            write_json(self.directory / id / "study.json", state)
            return state

    def handle_get(self, handler):
        if urlsplit(handler.path).path == "/api/study/decks":
            decks = []
            for path in self.directory.glob("*/job.json"):
                job = json.loads(path.read_text())
                if job.get("status") == "ready" and job.get("candidates"):
                    decks.append({key: job.get(key) for key in ("id", "filename", "created_at")})
            handler.send_json(200, sorted(decks, key=lambda d: d["created_at"] or "", reverse=True))
            return True
        route = JOB_ROUTE.fullmatch(urlsplit(handler.path).path)
        if not route:
            return False
        id, action = route.groups()
        try:
            job = self.read(id)
            if action and action.startswith("frames/"):
                filename = action.split("/")[1]
                if not re.fullmatch(r"frame_\d{9}\.png", filename):
                    raise ValueError("Unknown frame.")
                frame = self.directory / id / "result/frames" / filename
                if not frame.is_file():
                    raise ValueError("Frame not found.")
                handler.send_response(200)
                handler.send_header("Content-Type", "image/png")
                handler.send_header("Content-Length", str(frame.stat().st_size))
                handler.end_headers()
                with frame.open("rb") as source:
                    shutil.copyfileobj(source, handler.wfile)
            elif action == "study":
                handler.send_json(200, self.study_state(id))
            elif action:
                raise ValueError("Unknown route.")
            else:
                if job["status"] == "processing":
                    job["frames_started"] = len(
                        list((self.directory / id / "result/frames").glob("*.png"))
                    )
                handler.send_json(200, job)
        except ValueError as error:
            handler.send_json(404, {"error": str(error)})
        return True

    def handle_post(self, handler):
        path = urlsplit(handler.path)
        route = JOB_ROUTE.fullmatch(path.path)
        if path.path != "/api/imports" and not route:
            return False
        origin = handler.headers.get("Origin")
        if origin and urlsplit(origin).netloc != handler.headers.get("Host"):
            handler.send_json(403, {"error": "Origin mismatch"})
            return True
        try:
            length = int(handler.headers.get("Content-Length", "0"))
            if route:
                id, action = route.groups()
                if action not in ("vocabulary", "study") or not 0 < length <= 2_000_000:
                    raise ValueError("Invalid save request.")
                if handler.headers.get_content_type() != "application/json":
                    raise ValueError("Expected JSON.")
                body = json.loads(handler.rfile.read(length))
                handler.send_json(
                    200,
                    self.rate_word(id, body)
                    if action == "study"
                    else self.save_words(id, body["entries"]),
                )
            else:
                if not 0 < length <= MAX_UPLOAD:
                    handler.close_connection = True
                    handler.send_json(413, {"error": "Choose a video smaller than 90 MB."})
                    return True
                filename = Path(parse_qs(path.query).get("filename", ["video.mp4"])[0]).name[:200]
                extension = Path(filename).suffix.lower()
                if extension not in EXTENSIONS:
                    raise ValueError("Choose a supported video: MP4, MOV, M4V, AVI, MKV, or WebM.")
                if not self.slot.acquire(blocking=False):
                    handler.close_connection = True
                    handler.send_json(
                        429,
                        {"error": "Two imports are in progress. Please wait for one to finish."},
                    )
                    return True
                id = uuid.uuid4().hex
                directory = self.directory / id
                try:
                    directory.mkdir()
                    video = directory / ("video" + extension)
                    remaining = length
                    handler.connection.settimeout(90)
                    with video.open("wb") as output:
                        while remaining:
                            chunk = handler.rfile.read(min(1024 * 1024, remaining))
                            if not chunk:
                                raise ValueError("Upload was interrupted. Please retry.")
                            output.write(chunk)
                            remaining -= len(chunk)
                    write_json(
                        directory / "job.json",
                        {
                            "id": id,
                            "filename": filename,
                            "status": "queued",
                            "created_at": now(),
                            "bytes": length,
                        },
                    )
                    self.pool.submit(self.process, id, video)
                except Exception:
                    self.slot.release()
                    shutil.rmtree(directory, ignore_errors=True)
                    raise
                handler.send_json(202, {"id": id, "status": "queued"})
        except (ValueError, KeyError, TypeError, OSError) as error:
            handler.close_connection = True
            handler.send_json(400, {"error": str(error)})
        return True
